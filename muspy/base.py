"""Base classes.

This module defines the bases classes for MusPy objects.

Classes
-------

- Base
- ComplexBase

"""
from collections import OrderedDict
from inspect import isclass
from operator import attrgetter
from typing import Any, Callable, List, Mapping, Optional, Type, TypeVar

import yaml

__all__ = ["Base", "ComplexBase"]

BaseType = TypeVar("BaseType", bound="Base")
ComplexBaseType = TypeVar("ComplexBaseType", bound="ComplexBase")


class _OrderedDumper(yaml.SafeDumper):
    """A dumper that supports OrderedDict."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


_OrderedDumper.add_representer(OrderedDict, _dict_representer)


def _yaml_dump(data):
    """Dump data to YAML, which supports OrderedDict.

    Code adapted from https://stackoverflow.com/a/21912744.
    """
    return yaml.dump(data, Dumper=_OrderedDumper, allow_unicode=True)


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
    """The base class for MusPy classes.

    This is the base class for MusPy classes. It provides two handy I/O
    methods---`from_dict` and `to_ordered_dict`. It also provides intuitive
    `__repr__` as well as methods `pretty_str` and `print` for beautifully
    printing the content.

    Hint
    ----
    To implement a new class in MusPy, please inherit from this class and
    set the following class variables properly.

    - `_attributes`: An OrderedDict with attribute names as keys and their
      types as values.
    - `_optional_attributes`: A list of optional attribute names.
    - `_list_attributes`: A list of attributes that are lists.
    - `_sort_attributes`: A list of attributes used when being sorted,
      which will be passed to operator.attrgetter.

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
        _sort_attributes = ["time", "duration", "pitch"]

    See Also
    --------
    :class:`muspy.ComplexBase` : A base class that supports advanced
      operations on list attributes.

    """

    _attributes: Mapping[str, Any] = {}
    _optional_attributes: List[str] = []
    _list_attributes: List[str] = []
    _sort_attributes: List[str] = []

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
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

    @classmethod
    def from_dict(cls: Type[BaseType], dict_: Mapping) -> BaseType:
        """Return an instance constructed from a dictionary.

        Instantiate an object whose attributes and the corresponding values
        are given as a dictionary.

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

    def to_ordered_dict(self, skip_none: bool = True) -> OrderedDict:
        """Return the object as an OrderedDict.

        Return an ordered dictionary that stores the attributes and their
        values as key-value pairs.

        Parameters
        ----------
        skip_none : bool
            Whether to skip attributes with value None or those that are
            empty lists.

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
                if not value and skip_none:
                    continue
                if isclass(attr_type) and issubclass(attr_type, Base):
                    ordered_dict[attr] = [v.to_ordered_dict() for v in value]
                else:
                    ordered_dict[attr] = value
            elif value is None:
                if not skip_none:
                    ordered_dict[attr] = None
            elif isclass(attr_type) and issubclass(attr_type, Base):
                ordered_dict[attr] = value.to_ordered_dict()
            else:
                ordered_dict[attr] = value
        return ordered_dict

    def pretty_str(self) -> str:
        """Return the stored data as a string in a beautiful YAML-like format.

        Returns
        -------
        str
            Stored data as a string in pretty YAML-like format.

        See Also
        --------
        :meth:`muspy.Base.print` : Print the stored data in a beautiful
          YAML-like format.

        """
        return _yaml_dump(self.to_ordered_dict())

    def print(self):
        """Print the stored data in a beautiful YAML-like format.

        See Also
        --------
        :meth:`muspy.Base.pretty_str` : Return the stored data as a string in a
          beautiful YAML-like format.

        """
        print(self.pretty_str())

    def _validate_attr_type(self, attr: str):
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

    def validate_type(self: BaseType, attr: Optional[str] = None) -> BaseType:
        """Raise an error if a certain attribute has an invalid type.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.

        Returns
        -------
        Object itself.

        See Also
        --------
        :meth:`muspy.Base.is_valid_type` : Return True if an attribute has a
          valid type, otherwise False.
        :meth:`muspy.Base.validate` : Raise an error if a certain attribute has
          an invalid type or value.

        """
        if attr is None:
            for attribute in self._attributes:
                self._validate_attr_type(attribute)
        else:
            self._validate_attr_type(attr)
        return self

    def _validate(self, attr: str):
        attr_type = self._attributes[attr]
        if isclass(attr_type) and issubclass(attr_type, Base):
            if attr in self._list_attributes:
                if getattr(self, attr):
                    for item in getattr(self, attr):
                        item.validate()
            else:
                getattr(self, attr).validate()
        else:
            self._validate_attr_type(attr)
            if attr == "time" and getattr(self, "time") < 0:
                raise ValueError("`time` must be nonnegative.")

    def validate(self: BaseType, attr: Optional[str] = None) -> BaseType:
        """Raise an error if a certain attribute has an invalid type or value.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.

        Returns
        -------
        Object itself.

        See Also
        --------
        :meth:`muspy.Base.is_valid` : Return True if an attribute is valid,
          otherwise False.
        :meth:`muspy.Base.validate_type` : Raise an error if a certain
          attribute has an invalid type.

        """
        if attr is None:
            for attribute in self._attributes:
                self._validate(attribute)
        else:
            self._validate(attr)
        return self

    def is_valid_type(self, attr: Optional[str] = None) -> bool:
        """Return True if an attribute has a valid type, otherwise False.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.

        Returns
        -------
        bool
            Whether the attribute has a valid type.

        See Also
        --------
        :meth:`muspy.Base.validate_type` : Raise an error if a certain
          attribute has an invalid type.
        :meth:`muspy.Base.is_valid` : Return True if an attribute is valid,
          otherwise False.

        """
        try:
            self.validate_type(attr)
        except TypeError:
            return False
        return True

    def is_valid(self, attr: Optional[str] = None) -> bool:
        """Return True if an attribute is valid, otherwise False.

        This will recursively apply to an attribute's attributes.

        Parameters
        ----------
        attr : str
            Attribute to validate. Defaults to validate all attributes.

        Returns
        -------
        bool
            Whether the attribute has a valid type and value.

        See Also
        --------
        :meth:`muspy.Base.validate` : Raise an error if a certain attribute
          has an invalid type or value.
        :meth:`muspy.Base.is_valid_type` : Return True if an attribute has a
          valid type, otherwise False.

        """
        try:
            self.validate(attr)
        except (TypeError, ValueError):
            return False
        return True

    def _adjust_time(self, func: Callable[[int], int], attr: str):
        attr_type = self._attributes[attr]
        if attr == "time":
            if "time" in self._list_attributes:
                new_list = [func(item) for item in getattr(self, "time")]
                setattr(self, "time", new_list)
            else:
                setattr(self, "time", func(getattr(self, attr)))
        else:
            if isclass(attr_type) and issubclass(attr_type, Base):
                if attr in self._list_attributes:
                    for item in getattr(self, attr):
                        item.adjust_time(func)
                elif getattr(self, attr) is not None:
                    getattr(self, attr).adjust_time(func)

    def adjust_time(
        self: BaseType, func: Callable[[int], int], attr: Optional[str] = None
    ) -> BaseType:
        """Adjust the timing of time-stamped objects.

        This will apply recursively to an attribute's attributes.

        Parameters
        ----------
        func : callable
            The function used to compute the new timing from the old timing,
            i.e., `new_time = func(old_time)`.
        attr : str
            Attribute to adjust. If None, adjust all attributes. Defaults to
            None.

        Returns
        -------
        Object itself.

        """
        if attr is None:
            for attribute in self._attributes:
                self._adjust_time(func, attribute)
        else:
            self._adjust_time(func, attr)
        return self


class ComplexBase(Base):
    """A base class that supports advanced operations on list attributes.

    This class extend the Base class with advanced operations on list
    attributes, including `append`, `remove_invalid`, `remove_duplicate` and
    `sort`.

    See Also
    --------
    :class:`muspy.Base` : The base class for MusPy classes.

    """

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
            "Cannot find a list attribute for type {}.".format(
                type(obj).__name__
            )
        )

    def append(self: ComplexBaseType, obj) -> ComplexBaseType:
        """Append an object to the correseponding list.

        This will automatically determine the list attributes to append
        based on the type of the object.

        Parameters
        ----------
        obj
            Object to append.

        """
        self._append(obj)
        return self

    def _remove_invalid(self, attr: str, recursive: bool):
        # Skip it if empty
        if not getattr(self, attr):
            return

        # Replace the old lis with a new list of only valid items
        attr_type = self._attributes[attr]
        value = getattr(self, attr)
        is_class = isclass(attr_type)
        if is_class and issubclass(attr_type, Base):
            new_value = [item for item in value if item.is_valid()]
        else:
            new_value = [item for item in value if isinstance(item, attr_type)]
        setattr(self, attr, new_value)

        # Apply recursively
        if recursive and is_class and issubclass(attr_type, ComplexBase):
            for value in getattr(self, attr):
                value.remove_invalid(recursive=recursive)

    def remove_invalid(
        self: ComplexBaseType,
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> ComplexBaseType:
        """Remove invalid items from list attributes, others left unchanged.

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

        # Replace the old lis with a new list without duplicates
        attr_type = self._attributes[attr]
        value = getattr(self, attr)
        new_value = [value[0]]
        for item, next_item in zip(value[:-1], value[1:]):
            if item != next_item:
                new_value.append(next_item)
        setattr(self, attr, new_value)

        # Apply recursively
        if (
            recursive
            and isclass(attr_type)
            and issubclass(attr_type, ComplexBase)
        ):
            for value in getattr(self, attr):
                value.sort(recursive=recursive)

    def remove_duplicate(
        self: ComplexBaseType,
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> ComplexBaseType:
        """Remove duplicate items.

        Parameters
        ----------
        attr : str
            Attribute to check. If None, check all attributes. Defaults to
            None.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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
            # pylint: disable=protected-access
            if attr_type._sort_attributes:
                getattr(self, attr).sort(
                    key=attrgetter(*attr_type._sort_attributes)
                )
            # Apply recursively
            if recursive and issubclass(attr_type, ComplexBase):
                for value in getattr(self, attr):
                    value.sort(recursive=recursive)

    def sort(
        self: ComplexBaseType,
        attr: Optional[str] = None,
        recursive: bool = True,
    ) -> ComplexBaseType:
        """Sort a list attribute.

        Parameters
        ----------
        attr : str
            Attribute to sort. If None, sort all attributes. Defaults to None.
        recursive : bool
            Whether to apply recursively. Defaults to True.

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
