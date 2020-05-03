"""
Base classes
============

These are the two base classes of MusPy. All MusPy objects inherit from
the base class :class:`muspy.Base`. Some MusPy objects inherit from
:class:`muspy.ComplexBase`, which also inherit from :class:`muspy.Base`.

"""
from collections import OrderedDict
from inspect import isclass
from typing import Any, Callable, List, Mapping, Optional
from operator import attrgetter


def _get_type_string(attr_cls):
    """Return a string represeting acceptable type(s)."""
    if isinstance(attr_cls, (list, tuple)):
        if len(attr_cls) > 1:
            return (
                ", ".join([x.__name__ for x in attr_cls[:-1]])
                + " or "
                + attr_cls[-1].__name__
            )
        return attr_cls[0].__name__
    return attr_cls.__name__


class Base:
    """The base class of MusPy objects.

    It provides the following features.

    - Intuitive and meaningful `__repr__` in the form of
      `class_name(attr_1=value_1, attr_2=value_2,...)`.
    - Method `from_dict`: Instantiate an object whose attributes and the
      the corresponding values are given as a dictionary.
    - Method `to_ordered_dict`: Returns the object as an OrderedDict.
    - Method `validate_type`: Raise TypeError if any attribute of the object
      is of the wrong type according to `_attributes` (see Notes).
    - Method `validate`: Raise TypeError or ValueError if any attribute of
      the object is of the wrong type according to `_attributes` (see
      Notes) or having an invalid value.
    - Method `is_valid_type`: Return True if each attribute of the object is
      of the correct type according to `_attributes` (see Notes).
    - Method `is_valid`: Return True if each attribute of the object is
      of the correct type according to `_attributes` (see Notes) and having
      a valid value.
    - Method `adjust_time`: Adjust the timing of time-stamped objects. For
      example, if `tempo` is an instance of the :class:`muspy.Tempo` class
      and `func` is a callable, then calling `tempo.adjust_time(func)` leads
      to `tempo.time = func(tempo.time)`.

    Notes
    -----
    This is the base class for MusPy objects. To add a new class, please
    inherit from this class and set the following class variables properly.

    - `_attributes`: An OrderedDict with all the attributes (both required
      and optional ones) of the object as keys and their types as values.
    - `_optional_attributes`: A list containing optional attributes. An
      attribute in this list is allowed to be None.
    - _temporal_attributes: A list containing attributes that are considered
      temporal. An attribute in this list is supposed to always have a
      nonnegative value. The first item of this list is used to determine
      the order of objects when being sorted.
    - _list_attributes: A list containing attributes that are lists.

    """

    _attributes: Mapping[str, Any] = {}
    _optional_attributes: List[str] = []
    _temporal_attributes: List[str] = []
    _list_attributes: List[str] = []

    def _init(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __init__(self, **kwargs):
        self._init(**kwargs)

    def __repr__(self):
        to_join = []
        for attr in self._attributes:
            value = getattr(self, attr)
            if attr in self._list_attributes:
                if not value:
                    to_join.append(attr + "=[]")
                elif len(value) > 1:
                    to_join.append(attr + "=[" + repr(value[0]) + ", ...]")
                else:
                    to_join.append(attr + "=" + repr(value))
            else:
                to_join.append(attr + "=" + repr(value))
        return type(self).__name__ + "(" + ", ".join(to_join) + ")"

    @classmethod
    def from_dict(cls, dict_: Mapping):
        """Return an instance constructed from a dictionary.

        Parameters
        ----------
        dict_ : dict
            A dictionary that stores the attributes and their values as
            key-value pairs.

        """
        kwargs = {}
        for attr, attr_cls in cls._attributes.items():
            if attr not in dict_:
                if attr in cls._optional_attributes:
                    continue
                raise TypeError("`{}` is a required attribute.".format(attr))
            if isclass(attr_cls) and issubclass(attr_cls, Base):
                if attr in cls._list_attributes:
                    kwargs[attr] = [
                        attr_cls.from_dict(value) for value in dict_[attr]
                    ]
                else:
                    kwargs[attr] = attr_cls.from_dict(dict_[attr])
            else:
                kwargs[attr] = dict_[attr]
        return cls(**kwargs)

    def to_ordered_dict(self) -> OrderedDict:
        """Return the object as an OrderedDict."""
        ordered_dict: OrderedDict = OrderedDict()
        for attr, attr_cls in self._attributes.items():
            value = getattr(self, attr)
            if value is None:
                ordered_dict[attr] = None
            elif isclass(attr_cls) and issubclass(attr_cls, Base):
                if attr in self._list_attributes:
                    ordered_dict[attr] = [v.to_ordered_dict() for v in value]
                else:
                    ordered_dict[attr] = value.to_ordered_dict()
            else:
                ordered_dict[attr] = value
        return ordered_dict

    def _validate_attr_type(self, attr):
        attr_cls = self._attributes[attr]
        value = getattr(self, attr)
        if value is None:
            if attr in self._optional_attributes:
                return
            raise TypeError("`{}` must not be None".format(attr))
        if attr in self._list_attributes:
            if not isinstance(value, list):
                raise TypeError("`{}` must be a list.".format(attr))
            for v in value:
                if not isinstance(v, attr_cls):
                    raise TypeError(
                        "`{}` must be a list of type {}.".format(
                            attr, _get_type_string(attr_cls)
                        )
                    )
        elif not isinstance(value, attr_cls):
            raise TypeError(
                "`{}` must be of type {}.".format(
                    attr, _get_type_string(attr_cls)
                )
            )

    def _validate_type(self, attr: Optional[str] = None):
        if attr is None:
            for attribute in self._attributes:
                self._validate_attr_type(attribute)
        else:
            self._validate_attr_type(attr)

    def validate_type(self, attr: Optional[str] = None):
        """Raise proper errors if a certain attribute is of wrong type.

        This will recursively apply to each attribute's attributes. When
        `attr` is not given, check all attributes.

        """
        self._validate_type(attr)

    def _validate_attr(self, attr: str):
        attr_cls = self._attributes[attr]
        if isclass(attr_cls) and issubclass(attr_cls, Base):
            if attr in self._list_attributes and getattr(self, attr):
                for item in getattr(self, attr):
                    item.validate()
            else:
                getattr(self, attr).validate()
        else:
            self._validate_attr_type(attr)
            if attr in self._temporal_attributes and getattr(self, attr) < 0:
                raise ValueError("`{}` must be nonnegative.".format(attr))

    def _validate(self, attr: Optional[str] = None):
        if attr is None:
            for attribute in self._attributes:
                self._validate_attr(attribute)
        else:
            self._validate_attr(attr)

    def validate(self, attr: Optional[str] = None):
        """Raise proper errors if a certain attribute is invalid.

        This will recursively apply to each attribute's attributes. When
        `attr` is not given, check all attributes.

        """
        self._validate(attr)

    def is_type_valid(self, attr: Optional[str] = None):
        """Return True if a certain attribute is valid, otherwise False.

        This will recursively apply to each attribute's attributes. When `attr`
        is not given, return True only if all attributes are valid, otherwise
        False.

        """
        try:
            self.validate_type(attr)
        except TypeError:
            return False
        return True

    def is_valid(self, attr: Optional[str] = None):
        """Return True if a certain attribute is valid, otherwise False.

        This will recursively apply to each attribute's attributes. When `attr`
        is not given, return True only if all attributes are valid, otherwise
        False.

        """
        try:
            self.validate(attr)
        except (TypeError, ValueError):
            return False
        return True

    def _adjust_time(self, func, attr):
        attr_cls = self._attributes[attr]
        if attr in self._temporal_attributes:
            if attr_cls in self._list_attributes:
                new_list = [func(item) for item in getattr(self, attr)]
                setattr(self, attr, new_list)
            else:
                setattr(self, attr, func(getattr(self, attr)))
        else:
            if isclass(attr_cls) and issubclass(attr_cls, Base):
                if attr_cls in self._list_attributes:
                    for item in getattr(self, attr):
                        item.adjust_time(func)
                else:
                    getattr(self, attr).adjust_time(func)

    def adjust_time(self, func: Callable, attr: Optional[str] = None):
        """Adjust the timing of time-stamped objects.

        Parameters
        ----------
        func : callable
            The function used to compute the new timing from the old timing,
            i.e., `new_time = func(old_time)`.

        """
        if attr is None:
            for attribute in self._attributes:
                self._adjust_time(func, attribute)
        else:
            self._adjust_time(func, attr)
        return self


class ComplexBase(Base):
    """A base class that supports operations on list attributes.

    The supported operations are
    - Method `remove_invalid`: Remove invalid items from list attributes.
    - Method `append`: Automatically append the object to the corresponding
      list. For example, if `track` is an instance of the
      :class:`muspy.Track` class and `note` is an instance of the
      :class:`muspy.Note` class, then calling `track.append(note)` leads to
      `track.notes.append(note)`.
    - Method `sort`: Sort the time-stamped objects with respect to the
      first item in `_time_attributes`. For example, if `track` is an
      instance of the :class:`muspy.Track` class, then calling
      `track.sort()` leads to `track.notes.sort(lambda x: x.time)`. Note
      that the `time` attribute is used to sort :class:`muspy.Note` objects
      since is `muspy.Note._time_attribute = ['time']`.

    """

    def _append(self, obj):
        for attr in self._list_attributes:
            attr_cls = self._attributes[attr]
            if isinstance(obj, attr_cls):
                if isclass(attr_cls) and issubclass(attr_cls, Base):
                    if getattr(self, attr) is None:
                        setattr(self, attr, [obj])
                    else:
                        getattr(self, attr).append(obj)
                    return
        raise TypeError(
            "Cannot find a list of type {}.".format(type(obj).__name__)
        )

    def append(self, obj):
        """Append an object to the correseponding list."""
        self._append(obj)
        return self

    def _remove_invalid(self, attr):
        if not getattr(self, attr):
            return
        attr_cls = self._attributes[attr]
        if isclass(attr_cls) and issubclass(attr_cls, Base):
            new_list = [
                item for item in getattr(self, attr) if item.is_valid()
            ]
        else:
            new_list = [
                item
                for item in getattr(self, attr)
                if isinstance(item, self._attributes[attr])
            ]
        setattr(self, attr, new_list)

    def remove_invalid(self, attr: Optional[str] = None):
        """Remove invalid items from list attributes, others left unchanged.

        When `attr` is not given, remove invalid items for each list attribute.

        """
        if attr is None:
            for attribute in self._list_attributes:
                self._remove_invalid(attribute)
        else:
            if attr not in self._list_attributes:
                raise TypeError("`{}` is not a list attribute.")
            self._remove_invalid(attr)
        return self

    def _sort(self, attr):
        if not getattr(self, attr):
            return
        attr_cls = self._attributes[attr]
        if isclass(attr_cls) and issubclass(attr_cls, Base):
            # pylint: disable=protected-access
            if attr_cls._temporal_attributes:
                ref_attr = attr_cls._temporal_attributes[0]
                getattr(self, attr).sort(attrgetter(ref_attr))

    def sort(self, attr: Optional[str] = None):
        """Sort the time-stamped objects recursively."""
        if attr is None:
            for attribute in self._list_attributes:
                self._sort(attribute)
        else:
            if attr not in self._list_attributes:
                raise TypeError("`{}` is not a list attribute.")
            self._sort(attr)
        return self
