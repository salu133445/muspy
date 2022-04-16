"""Base classes.

This module defines the bases classes for MusPy objects.

Classes
-------

- Base
- ComplexBase

"""
import copy
from collections import OrderedDict
from inspect import isclass
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Type,
    TypeVar,
    Union,
)

from .utils import yaml_dump

__all__ = ["Base", "ComplexBase"]

BaseT = TypeVar("BaseT", bound="Base")
ComplexBaseT = TypeVar("ComplexBaseT", bound="ComplexBase")


def _get_type_string(attr_type):
    """Return a string represeting acceptable type(s)."""
    if isinstance(attr_type, (list, tuple)):
        if len(attr_type) > 1:
            return (
                ", ".join([x.__name__ for x in attr_type[:-1]])
                + " or "
                + attr_type[-1].__name__
            )
        return attr_type[0].__name__
    return attr_type.__name__


class Base:
    """Base class for MusPy classes.

    This is the base class for MusPy classes. It provides two handy I/O
    methods---`from_dict` and `to_ordered_dict`. It also provides
    intuitive `repr` as well as methods `pretty_str` and `print` for
    beautifully printing the content.

    In addition, `hash` is implemented by `hash(repr(self))`.
    Comparisons between two Base objects are also supported, where
    equality check will compare all attributes, while 'less than' and
    'greater than' will only compare the `time` attribute.

    Hint
    ----
    To implement a new class in MusPy, please inherit from this class
    and set the following class variables properly.

    - `_attributes`: An OrderedDict with attribute names as keys and
      their types as values.
    - `_optional_attributes`: A list of optional attribute names.
    - `_list_attributes`: A list of attributes that are lists.

    Take :class:`muspy.Note` for example.::

        _attributes = OrderedDict(
            [
                ("time", int),
                ("duration", int),
                ("pitch", int),
                ("velocity", int),
                ("pitch_str", str),
            ]
        )
        _optional_attributes = ["pitch_str"]

    See Also
    --------
    :class:`muspy.ComplexBase` :
        Base class that supports advanced operations on list attributes.

    """

    _attributes: Mapping[str, Any] = {}
    _optional_attributes: List[str] = []
    _list_attributes: List[str] = []

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        to_join = []
        for attr in self._attributes:
            value = getattr(self, attr)
            if attr in self._list_attributes:
                if not value:
                    continue
                if len(value) > 3:
                    to_join.append(
                        attr + "=" + repr(value[:3])[:-1] + ", ...]"
                    )
                else:
                    to_join.append(attr + "=" + repr(value))
            elif value is not None:
                to_join.append(attr + "=" + repr(value))
        return type(self).__name__ + "(" + ", ".join(to_join) + ")"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other) -> bool:
        for attr in self._attributes:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __lt__(self, other) -> bool:
        if not hasattr(self, "time") or not hasattr(other, "time"):
            return NotImplemented
        if getattr(self, "time") < getattr(other, "time"):
            return True
        return False

    def __gt__(self, other) -> bool:
        if not hasattr(self, "time") or not hasattr(other, "time"):
            return NotImplemented
        if getattr(self, "time") > getattr(other, "time"):
            return True
        return False

    def __deepcopy__(self: BaseT, memo: dict) -> BaseT:
        return self.from_dict(self.to_ordered_dict())

    @classmethod
    def from_dict(
        cls: Type[BaseT],
        dict_: Mapping,
        strict: bool = False,
        cast: bool = False,
    ) -> BaseT:
        """Return an instance constructed from a dictionary.

        Instantiate an object whose attributes and the corresponding
        values are given as a dictionary.

        Parameters
        ----------
        dict_ : dict or mapping
            A dictionary that stores the attributes and their values as
            key-value pairs, e.g., `{"attr1": value1, "attr2": value2}`.
        strict : bool, default: False
            Whether to raise errors for invalid input types.
        cast : bool, default: False
            Whether to cast types.

        Returns
        -------
        Constructed object.

        """
        assert not (
            strict and cast
        ), "`strict` and `cast` cannot be both True."
        kwargs: Dict[str, Any] = {}
        for attr, attr_type in cls._attributes.items():
            if isinstance(attr_type, tuple):
                attr_type = attr_type[0]
            value = dict_.get(attr)
            if value is None:
                if attr in cls._optional_attributes:
                    continue
                raise TypeError(f"`{attr}` must not be None.")
            if isclass(attr_type) and issubclass(attr_type, Base):
                if attr in cls._list_attributes:
                    kwargs[attr] = [attr_type.from_dict(v) for v in value]
                else:
                    kwargs[attr] = attr_type.from_dict(value)
            else:
                if strict:
                    if attr in cls._list_attributes:
                        if not isinstance(value, list):
                            raise TypeError(
                                f"`{attr}` must be a list, but got : "
                                f"{type(value)} ."
                            )
                        for v in value:  # pylint: disable=invalid-name
                            if not isinstance(v, attr_type):
                                raise TypeError(
                                    f"`{attr}` must be a list of type "
                                    f"{attr_type}, but got : {type(v)} ."
                                )
                    elif not isinstance(value, attr_type):
                        raise TypeError(
                            f"`{attr}` must be of type {attr_type}, "
                            f"but got : {type(value)} ."
                        )
                if cast:
                    is_bad_input = False
                    if attr in cls._list_attributes:
                        if not isinstance(value, list):
                            is_bad_input = True
                        for v in value:  # pylint: disable=invalid-name
                            if not isinstance(v, attr_type):
                                is_bad_input = True
                        if is_bad_input:
                            kwargs[attr] = [attr_type(v) for v in value]
                        else:
                            kwargs[attr] = value
                    elif not isinstance(value, attr_type):
                        kwargs[attr] = attr_type(value)
                else:
                    kwargs[attr] = value
        return cls(**kwargs)

    def to_ordered_dict(
        self, skip_missing: bool = True, deepcopy: bool = True
    ) -> OrderedDict:
        """Return the object as an OrderedDict.

        Return an ordered dictionary that stores the attributes and
        their values as key-value pairs.

        Parameters
        ----------
        skip_missing : bool, default: True
            Whether to skip attributes with value None or those that are
            empty lists.
        deepcopy : bool, default: True
            Whether to make deep copies of the attributes.

        Returns
        -------
        OrderedDict
            A dictionary that stores the attributes and their values as
            key-value pairs, e.g., `{"attr1": value1, "attr2": value2}`.

        """
        ordered_dict: OrderedDict = OrderedDict()
        for attr, attr_type in self._attributes.items():
            value = getattr(self, attr)
            if attr in self._list_attributes:
                if not value and skip_missing:
                    continue
                if isclass(attr_type) and issubclass(attr_type, Base):
                    ordered_dict[attr] = [
                        v.to_ordered_dict(
                            skip_missing=skip_missing, deepcopy=deepcopy
                        )
                        for v in value
                    ]
                elif deepcopy:
                    ordered_dict[attr] = copy.deepcopy(value)
                else:
                    ordered_dict[attr] = value
            elif value is None:
                if not skip_missing:
                    ordered_dict[attr] = None
            elif isclass(attr_type) and issubclass(attr_type, Base):
                ordered_dict[attr] = value.to_ordered_dict(
                    skip_missing=skip_missing, deepcopy=deepcopy
                )
            elif deepcopy:
                ordered_dict[attr] = copy.deepcopy(value)
            else:
                ordered_dict[attr] = value
        return ordered_dict

    def copy(self: BaseT) -> BaseT:
        """Return a shallow copy of the object.

        This is equivalent to :py:func:`copy.copy(self)`.

        Returns
        -------
        Shallow copy of the object.

        """
        return copy.copy(self)

    def deepcopy(self: BaseT) -> BaseT:
        """Return a deep copy of the object.

        This is equivalent to :py:func:`copy.deepcopy(self)`

        Returns
        -------
        Deep copy of the object.

        """
        return copy.deepcopy(self)

    def pretty_str(self, skip_missing: bool = True) -> str:
        """Return the attributes as a string in a YAML-like format.

        Parameters
        ----------
        skip_missing : bool, default: True
            Whether to skip attributes with value None or those that are
            empty lists.

        Returns
        -------
        str
            Stored data as a string in a YAML-like format.

        See Also
        --------
        :meth:`muspy.Base.print` :
            Print the attributes in a YAML-like format.

        """
        return yaml_dump(
            self.to_ordered_dict(skip_missing=skip_missing, deepcopy=False)
        )

    def print(self, skip_missing: bool = True):
        """Print the attributes in a YAML-like format.

        Parameters
        ----------
        skip_missing : bool, default: True
            Whether to skip attributes with value None or those that are
            empty lists.

        See Also
        --------
        :meth:`muspy.Base.pretty_str` :
            Return the the attributes as a string in a YAML-like format.

        """
        print(self.pretty_str(skip_missing=skip_missing))

    def _validate_attr_type(self, attr: str, recursive: bool):
        attr_type = self._attributes[attr]
        value = getattr(self, attr)
        if value is None:
            if attr in self._optional_attributes:
                return
            raise TypeError(f"`{attr}` must not be None")
        if attr in self._list_attributes:
            if not isinstance(value, list):
                raise TypeError(f"`{attr}` must be a list.")
            for item in value:
                if not isinstance(item, attr_type):
                    raise TypeError(
                        f"`{attr}` must be a list of type "
                        f"{_get_type_string(attr_type)}."
                    )
        elif not isinstance(value, attr_type):
            raise TypeError(
                f"`{attr}` must be of type {_get_type_string(attr_type)}."
            )

        # Apply recursively
        if recursive and isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                for item in getattr(self, attr):
                    item.validate_type(recursive=recursive)
            elif getattr(self, attr) is not None:
                getattr(self, attr).validate_type(recursive=recursive)

    def validate_type(
        self: BaseT, attr: str = None, recursive: bool = True
    ) -> BaseT:
        """Raise an error if an attribute is of an invalid type.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str, optional
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        See Also
        --------
        :meth:`muspy.Base.is_valid_type` :
            Return True if an attribute is of a valid type.
        :meth:`muspy.Base.validate` :
            Raise an error if an attribute has an invalid type or value.

        """
        if attr is None:
            for attribute in self._attributes:
                self._validate_attr_type(attribute, recursive)
        else:
            self._validate_attr_type(attr, recursive)
        return self

    def _validate(self, attr: str, recursive: bool):
        attr_type = self._attributes[attr]
        if isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                if getattr(self, attr):
                    for item in getattr(self, attr):
                        item.validate()
            else:
                getattr(self, attr).validate()
        else:
            # Set recursive=False to avoid repeated checks invoked when
            # calling `validate` recursively
            self._validate_attr_type(attr, False)
            if attr == "time" and getattr(self, "time") < 0:
                raise ValueError("`time` must be nonnegative.")

        # Apply recursively
        if recursive and isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                for item in getattr(self, attr):
                    item.validate(recursive=recursive)
            elif getattr(self, attr) is not None:
                getattr(self, attr).validate(recursive=recursive)

    def validate(
        self: BaseT, attr: str = None, recursive: bool = True
    ) -> BaseT:
        """Raise an error if an attribute has an invalid type or value.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str, optional
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        See Also
        --------
        :meth:`muspy.Base.is_valid` :
            Return True if an attribute has a valid type and value.
        :meth:`muspy.Base.validate_type` :
            Raise an error if an attribute is of an invalid type.

        """
        if attr is None:
            for attribute in self._attributes:
                self._validate(attribute, recursive)
        else:
            self._validate(attr, recursive)
        return self

    def is_valid_type(self, attr: str = None, recursive: bool = True) -> bool:
        """Return True if an attribute is of a valid type.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str, optional
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        bool
            Whether the attribute is of a valid type.

        See Also
        --------
        :meth:`muspy.Base.validate_type` :
            Raise an error if a certain attribute is of an invalid type.
        :meth:`muspy.Base.is_valid` :
            Return True if an attribute has a valid type and value.

        """
        try:
            self.validate_type(attr, recursive)
        except TypeError:
            return False
        return True

    def is_valid(self, attr: str = None, recursive: bool = True) -> bool:
        """Return True if an attribute has a valid type and value.

        This will recursively apply to an attribute's attributes.

        Parameters
        ----------
        attr : str, optional
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        bool
            Whether the attribute has a valid type and value.

        See Also
        --------
        :meth:`muspy.Base.validate` :
            Raise an error if an attribute has an invalid type or value.
        :meth:`muspy.Base.is_valid_type` :
            Return True if an attribute is of a valid type.

        """
        try:
            self.validate(attr, recursive)
        except (TypeError, ValueError):
            return False
        return True

    def _adjust_time(
        self, func: Callable[[int], int], attr: str, recursive: bool
    ):
        attr_type = self._attributes[attr]
        if attr == "time":
            if "time" in self._list_attributes:
                new_list = [func(item) for item in getattr(self, "time")]
                setattr(self, "time", new_list)
            else:
                setattr(self, "time", func(getattr(self, attr)))
        elif recursive and isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                for item in getattr(self, attr):
                    item.adjust_time(func, recursive=recursive)
            elif getattr(self, attr) is not None:
                getattr(self, attr).adjust_time(func, recursive=recursive)

    def adjust_time(
        self: BaseT,
        func: Callable[[int], int],
        attr: str = None,
        recursive: bool = True,
    ) -> BaseT:
        """Adjust the timing of time-stamped objects.

        Parameters
        ----------
        func : callable
            The function used to compute the new timing from the old
            timing, i.e., `new_time = func(old_time)`.
        attr : str, optional
            Attribute to adjust. Defaults to adjust all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is None:
            for attribute in self._attributes:
                self._adjust_time(func, attribute, recursive)
        else:
            self._adjust_time(func, attr, recursive)
        return self

    def _fix_type(self: BaseT, attr: str, recursive: bool):
        attr_type = self._attributes[attr]
        if isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                if getattr(self, attr):
                    for item in getattr(self, attr):
                        item.fix_type()
            else:
                getattr(self, attr).fix_type()
        else:
            value = getattr(self, attr)
            if not isinstance(value, attr_type):
                if isinstance(attr_type, tuple):
                    setattr(self, attr, attr_type[0](value))
                else:
                    setattr(self, attr, attr_type(value))

        # Apply recursively
        if recursive and isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                for item in getattr(self, attr):
                    item.fix_type(recursive=recursive)
            elif getattr(self, attr) is not None:
                getattr(self, attr).fix_type(recursive=recursive)

    def fix_type(
        self: BaseT, attr: str = None, recursive: bool = True
    ) -> BaseT:
        """Fix the types of attributes.

        Parameters
        ----------
        attr : str, optional
            Attribute to adjust. Defaults to adjust all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is None:
            for attribute in self._attributes:
                self._fix_type(attribute, recursive)
        else:
            self._fix_type(attr, recursive)
        return self


class ComplexBase(Base):
    """Base class that supports advanced operations on list attributes.

    This class extend the Base class with advanced operations on list
    attributes, including `append`, `remove_invalid`, `remove_duplicate`
    and `sort`.

    See Also
    --------
    :class:`muspy.Base` : Base class for MusPy classes.

    """

    def __iadd__(
        self: ComplexBaseT, other: Union[ComplexBaseT, Iterable]
    ) -> ComplexBaseT:
        return self.extend(other)

    def __add__(self: ComplexBaseT, other: ComplexBaseT) -> ComplexBaseT:
        if not isinstance(other, type(self)):
            raise TypeError(
                "Expect the second operand to be of type "
                f"{type(self).__name__}, but got {type(other).__name__}."
            )
        return self.deepcopy().extend(other, deepcopy=True)

    def _append(self, obj):
        for attr in self._list_attributes:
            attr_type = self._attributes[attr]
            if isinstance(obj, attr_type):
                if isclass(attr_type) and issubclass(attr_type, Base):
                    if getattr(self, attr) is None:
                        setattr(self, attr, [obj])
                    else:
                        getattr(self, attr).append(obj)
                    return
        raise TypeError(
            f"Cannot find a list attribute for type {type(obj).__name__}."
        )

    def append(self: ComplexBaseT, obj) -> ComplexBaseT:
        """Append an object to the corresponding list.

        This will automatically determine the list attributes to append
        based on the type of the object.

        Parameters
        ----------
        obj
            Object to append.

        """
        self._append(obj)
        return self

    def extend(
        self: ComplexBaseT,
        other: Union[ComplexBaseT, Iterable],
        deepcopy: bool = False,
    ) -> ComplexBaseT:
        """Extend the list(s) with another object or iterable.

        Parameters
        ----------
        other : :class:`muspy.ComplexBase` or iterable
            If an object of the same type is given, extend the
            list attributes with the corresponding list attributes of
            the other object. If an iterable is given, call
            :meth:`muspy.ComplexBase.append` for each item.
        deepcopy : bool, default: False
            Whether to make deep copies of the appended objects.

        Returns
        -------
        Object itself.

        """
        if isinstance(other, ComplexBase):
            if not isinstance(other, type(self)):
                raise TypeError(
                    f"Expect `other` to be of type {type(self).__name__}, "
                    f"but got {type(other).__name__}."
                )
            for attr in self._list_attributes:
                other_value = getattr(other, attr)
                getattr(self, attr).extend(
                    copy.deepcopy(other_value) if deepcopy else other_value
                )
            return self

        for item in other:  # type: ignore
            self._append(copy.deepcopy(item) if deepcopy else item)
        return self

    def _remove_invalid(self, attr: str, recursive: bool):
        # Skip it if empty
        if not getattr(self, attr):
            return

        attr_type = self._attributes[attr]
        is_class = isclass(attr_type)
        is_base = is_class and issubclass(attr_type, Base)
        is_complexbase = is_class and issubclass(attr_type, ComplexBase)
        value = getattr(self, attr)

        # NOTE: The ordering mathers here. We first apply recursively
        # and later check the currect object so that something that can
        # be fixed in a lower level would not make the high-level object
        # removed.

        # Apply recursively
        if recursive and is_complexbase:
            for item in value:
                item.remove_invalid(recursive=recursive)

        # Replace the old list with a new list of only valid items
        if is_base:
            value[:] = [item for item in value if item.is_valid()]
        else:
            value[:] = [item for item in value if isinstance(item, attr_type)]

    def remove_invalid(
        self: ComplexBaseT, attr: str = None, recursive: bool = True
    ) -> ComplexBaseT:
        """Remove invalid items from a list attribute.

        Parameters
        ----------
        attr : str, optional
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is None:
            for attribute in self._list_attributes:
                self._remove_invalid(attribute, recursive)
        elif attr in self._list_attributes:
            self._remove_invalid(attr, recursive)
        else:
            raise TypeError("`{}` must be a list attribute.")
        return self

    def _remove_duplicate(self, attr: str, recursive: bool):
        # Skip it if empty
        if not getattr(self, attr):
            return

        attr_type = self._attributes[attr]
        is_complexbase = isclass(attr_type) and issubclass(
            attr_type, ComplexBase
        )
        value = getattr(self, attr)

        # NOTE: The ordering mathers here. We first apply recursively
        # and later check the currect object so that something that can
        # be fixed in a lower level would not make the high-level object
        # removed.

        # Apply recursively
        if recursive and is_complexbase:
            for item in value:
                item.remove_duplicate(recursive=recursive)

        # Replace the old list with a new list without duplicates
        # TODO: Speed this up by grouping by time.
        new_value = []
        for item in value:
            if item not in new_value:
                new_value.append(item)
        value[:] = new_value

    def remove_duplicate(
        self: ComplexBaseT, attr: str = None, recursive: bool = True
    ) -> ComplexBaseT:
        """Remove duplicate items from a list attribute.

        Parameters
        ----------
        attr : str, optional
            Attribute to check. Defaults to check all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is None:
            for attribute in self._list_attributes:
                self._remove_duplicate(attribute, recursive)
        elif attr in self._list_attributes:
            self._remove_duplicate(attr, recursive)
        else:
            raise TypeError("`{}` must be a list attribute.")
        return self

    def _sort(self, attr: str, recursive: bool):
        # Skip it if empty
        if not getattr(self, attr):
            return

        # Sort the list
        attr_type = self._attributes[attr]
        if isclass(attr_type) and issubclass(attr_type, Base):
            getattr(self, attr).sort()
            # Apply recursively
            if recursive and issubclass(attr_type, ComplexBase):
                for value in getattr(self, attr):
                    value.sort(recursive=recursive)

    def sort(
        self: ComplexBaseT, attr: str = None, recursive: bool = True
    ) -> ComplexBaseT:
        """Sort a list attribute.

        Parameters
        ----------
        attr : str, optional
            Attribute to sort. Defaults to sort all attributes.
        recursive : bool, default: True
            Whether to apply recursively.

        Returns
        -------
        Object itself.

        """
        if attr is None:
            for attribute in self._list_attributes:
                self._sort(attribute, recursive)
        elif attr in self._list_attributes:
            self._sort(attr, recursive)
        else:
            raise TypeError("`{}` must be a list attribute.")
        return self
