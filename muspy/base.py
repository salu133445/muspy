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
from operator import attrgetter
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from .utils import yaml_dump

__all__ = ["Base", "ComplexBase"]

T = TypeVar("T")
BaseType = TypeVar("BaseType", bound="Base")
ComplexBaseType = TypeVar("ComplexBaseType", bound="ComplexBase")


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
    intuitive `__repr__` as well as methods `pretty_str` and `print` for
    beautifully printing the content.

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

    def __eq__(self, other) -> bool:
        for attr in self._attributes:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __deepcopy__(self: BaseType, memo: Optional[dict]) -> BaseType:
        return self.from_dict(self.to_ordered_dict())

    @classmethod
    def from_dict(cls: Type[BaseType], dict_: Mapping) -> BaseType:
        """Return an instance constructed from a dictionary.

        Instantiate an object whose attributes and the corresponding
        values are given as a dictionary.

        Parameters
        ----------
        dict_ : dict or mapping
            A dictionary that stores the attributes and their values as
            key-value pairs, e.g., `{"attr1": value1, "attr2": value2}`.

        Returns
        -------
        Constructed object.

        """
        kwargs = {}
        for attr, attr_type in cls._attributes.items():
            value = dict_.get(attr)
            if value is None:
                if attr in cls._optional_attributes:
                    continue
                raise TypeError("`{}` must not be None.".format(attr))
            if isclass(attr_type) and issubclass(attr_type, Base):
                if attr in cls._list_attributes:
                    kwargs[attr] = [attr_type.from_dict(v) for v in value]
                else:
                    kwargs[attr] = attr_type.from_dict(value)
            else:
                kwargs[attr] = value
        return cls(**kwargs)

    def to_ordered_dict(
        self, skip_missing: bool = True, deepcopy: bool = True,
    ) -> OrderedDict:
        """Return the object as an OrderedDict.

        Return an ordered dictionary that stores the attributes and
        their values as key-value pairs.

        Parameters
        ----------
        skip_missing : bool
            Whether to skip attributes with value None or those that are
            empty lists. Defaults to True.
        deepcopy : bool
            Whether to make deep copies of the attributes. Defaults to
            True.

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

    def copy(self: BaseType) -> BaseType:
        """Return a shallow copy of the object.

        This is equivalent to :py:func:`copy.copy(self)`.

        Returns
        -------
        Shallow copy of the object.

        """
        return copy.copy(self)

    def deepcopy(self: BaseType) -> BaseType:
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
        skip_missing : bool
            Whether to skip attributes with value None or those that are
            empty lists. Defaults to True.

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
        skip_missing : bool
            Whether to skip attributes with value None or those that are
            empty lists. Defaults to True.

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
            raise TypeError("`{}` must not be None".format(attr))
        if attr in self._list_attributes:
            if not isinstance(value, list):
                raise TypeError("`{}` must be a list.".format(attr))
            for item in value:
                if not isinstance(item, attr_type):
                    raise TypeError(
                        "`{}` must be a list of type {}.".format(
                            attr, _get_type_string(attr_type)
                        )
                    )
        elif not isinstance(value, attr_type):
            raise TypeError(
                "`{}` must be of type {}.".format(
                    attr, _get_type_string(attr_type)
                )
            )

        # Apply recursively
        if recursive and isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                for item in getattr(self, attr):
                    item.validate_type(recursive=recursive)
            elif getattr(self, attr) is not None:
                getattr(self, attr).validate_type(recursive=recursive)

    def validate_type(
        self: BaseType, attr: Optional[str] = None, recursive: bool = True,
    ) -> BaseType:
        """Raise an error if an attribute is of an invalid type.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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
        self: BaseType, attr: Optional[str] = None, recursive: bool = True,
    ) -> BaseType:
        """Raise an error if an attribute has an invalid type or value.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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

    def is_valid_type(
        self, attr: Optional[str] = None, recursive: bool = True,
    ) -> bool:
        """Return True if an attribute is of a valid type.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

        Returns
        -------
        bool
            Whether the attribute is of a valid type.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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

    def is_valid(
        self, attr: Optional[str] = None, recursive: bool = True,
    ) -> bool:
        """Return True if an attribute has a valid type and value.

        This will recursively apply to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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
        self: BaseType,
        func: Callable[[int], int],
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> BaseType:
        """Adjust the timing of time-stamped objects.

        Parameters
        ----------
        func : callable
            The function used to compute the new timing from the old
            timing, i.e., `new_time = func(old_time)`.
        attr : str
            Attribute to adjust. Defaults to adjust all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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


class ComplexBase(Base):
    """Base class that supports advanced operations on list attributes.

    This class extend the Base class with advanced operations on list
    attributes, including `append`, `remove_invalid`,
    `remove_duplicate` and `sort`.

    See Also
    --------
    :class:`muspy.Base` : Base class for MusPy classes.

    """

    def __iadd__(
        self: ComplexBaseType, other: Union[ComplexBaseType, Iterable]
    ) -> ComplexBaseType:
        return self.extend(other)

    def __add__(
        self: ComplexBaseType, other: ComplexBaseType
    ) -> ComplexBaseType:
        if not isinstance(other, type(self)):
            raise TypeError(
                "Expect the second operand to be of type "
                f"{type(self).__name__}, but got {type(other).__name__}."
            )
        return self.deepcopy().extend(other, deepcopy=True)

    def _traverse_lists(
        self,
        attr: Optional[str],
        recursive: bool
    ) -> Iterator[Tuple[str, Type[T], List[T]]]:
        """A generator yielding a tuple `(attr, attr_type, value)`
        for all list attributes."""
        if attr is None:
            for attribute in self._list_attributes:
                yield from self._traverse_lists(  # type: ignore
                    attribute, recursive)
            return
        if attr not in self._list_attributes:
            raise TypeError("`attr` must be a list attribute.")
        attr_type = self._attributes[attr]

        # Apply recursively using post-order traversal
        # (first children, then self)
        if (
            recursive
            and isclass(attr_type)
            and issubclass(attr_type, ComplexBase)
        ):
            for item in getattr(self, attr):
                yield from item._traverse_lists(  # type: ignore
                    attr=None, recursive=recursive)

        yield (attr, attr_type, getattr(self, attr))

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

    def append(self: ComplexBaseType, obj) -> ComplexBaseType:
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
        self: ComplexBaseType,
        other: Union[ComplexBaseType, Iterable],
        deepcopy: bool = False,
    ) -> ComplexBaseType:
        """Extend the list(s) with another object or iterable.

        Parameters
        ----------
        other : :class:`muspy.ComplexBase` or iterable
            If an object of the same type is given, extend the
            list attributes with the corresponding list attributes of
            the other object. If an iterable is given, call
            :meth:`muspy.ComplexBase.append` for each item.
        deepcopy : bool
            Whether to make deep copies of the appended objects.
            Defaults to False.

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

    def remove_invalid(
        self: ComplexBaseType,
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> ComplexBaseType:
        """Remove invalid items from a list attribute.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

        Returns
        -------
        Object itself.

        """
        # NOTE: We depend on the fact that _traverse_lists uses
        # post-order traversal. This way, we first apply recursively
        # and later check the currect object so that something that
        # can be fixed in a lower level would not make the high-level
        # object to be removed.

        attr_type: Type
        value: list
        for _, attr_type, value in self._traverse_lists(attr, recursive):
            # Skip it if empty
            if not value:
                continue

            if isclass(attr_type) and issubclass(attr_type, Base):
                value[:] = [item for item in value  # type: ignore
                            if (isinstance(item, attr_type)
                                and cast(Base, item).is_valid())]
            else:
                value[:] = [item for item in value  # type: ignore
                            if isinstance(item, attr_type)]

        return self

    def remove_duplicate(
        self: ComplexBaseType,
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> ComplexBaseType:
        """Remove duplicate items from a list attribute.

        Parameters
        ----------
        attr : str
            Attribute to check. Defaults to check all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

        Returns
        -------
        Object itself.

        """
        value: list
        for _, _, value in self._traverse_lists(attr, recursive):
            # Replace the old list with a new list without duplicates
            # TODO: Speed this up by grouping by time.
            new_value = []
            for item in value:  # type: ignore
                if item not in new_value:
                    new_value.append(item)
            value[:] = new_value

        return self

    def sort(
        self: ComplexBaseType,
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> ComplexBaseType:
        """Sort a list attribute.

        Parameters
        ----------
        attr : str
            Attribute to sort. Defaults to sort all attributes.
        recursive : bool
            Whether to apply recursively. Defaults to True.

        Returns
        -------
        Object itself.

        """
        attr_type: Type
        value: list
        for _, attr_type, value in self._traverse_lists(attr, recursive):
            if value and "time" in getattr(attr_type, "_attributes"):
                value.sort(key=attrgetter("time"))

        return self

    def lists(self, recursive: bool = False) -> Iterator[Tuple[str, list]]:
        """Return an iterator over the names and values of all list
        attributes.

        Parameters
        ----------
        recursive: bool
            Whether to apply recursively to all list attributes.
            Defaults to False.

        Returns
        -------
        An iterator over `(attr_name, attr_value)` tuples.
        """
        def generator():
            attr: str
            value: list
            for attr, _, value in self._traverse_lists(attr=None,
                                                       recursive=recursive):
                yield attr, value

        return generator()

    def list_items(self, recursive: bool = False) -> Iterator:
        """Return a flat iterator over the items of all list attributes.

        Parameters
        ----------
        recursive: bool
            Whether to apply recursively to all list attributes.
            Defaults to False.

        Returns
        -------
        A flat iterator over list items.
        """
        def generator():
            value: list
            for _, _, value in self._traverse_lists(attr=None,
                                                    recursive=recursive):
                yield from value

        return generator()
