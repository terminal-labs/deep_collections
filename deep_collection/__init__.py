import operator
from functools import reduce


def get_by_path(obj, path):
    """Access a nested object in obj by iterable path.
    from https://stackoverflow.com/a/14692747/913080

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> get_by_path(obj, ["a", 1, "c"])
    'd'
    """
    return reduce(operator.getitem, path, obj)


def set_by_path(obj, path, value):
    """Set a value in a nested object in obj by iterable path.
    from https://stackoverflow.com/a/14692747/913080

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> set_by_path(obj, ["a", 0], "foo")
    >>> obj
    {'a': ['foo', {'c': 'd'}]}
    >>> set_by_path(obj, ["a", 1, "e"], "foo")
    >>> obj
    {'a': ['foo', {'c': 'd', 'e': 'foo'}]}
    """
    get_by_path(obj, path[:-1])[path[-1]] = value


def _stringlike(obj):
    return any(isinstance(obj, base) for base in (str, bytes, bytearray))


def _can_be_deep(obj):
    """Determine if an object could be a nested collection.

    The general heuristic is that an object must be iterable, but not stringlike
    so that an element can be arbitrary like another collection.
    """
    try:
        iter(obj)
    except TypeError:
        return False

    if _stringlike(obj):
        return False

    return True


class DynamicSubclasser(type):
    """Return an instance of the class that uses this as its metaclass.
    This metaclass allows for a class to be instantiated with an argument,
    and assume that argument's class as its parent class.

    >>> class Foo(metaclass=DynamicSubclasser): pass
    >>> foo = Foo(5)
    >>> isinstance(foo, int)
    True
    """

    def __call__(cls, obj, *args, **kwargs):
        dynamic_parent_cls = type(obj)

        # Make this metaclass inherit from the dynamic_parent's metaclass.
        # This avoids metaclass conflicts.
        mcls = type(cls)
        cls.__class__ = type(mcls.__name__, (mcls, type(dynamic_parent_cls)), {})

        # Make a new class that inherits from the old and the object type.
        new_cls = type(cls.__name__, (cls, dynamic_parent_cls), {})

        # Create the instance and initialize it with the given object.
        # Sets obj in instance for immutables like `tuple`
        instance = new_cls.__new__(new_cls, obj, *args, **kwargs)
        # Sets obj in instance for mutables like `list`
        instance.__init__(obj, *args, **kwargs)

        return instance


class DeepCollection(metaclass=DynamicSubclasser):
    """A class intended to allow easy access to items of deep collections.

    >>> dc = DeepCollection({"a": ["i", "j", "k"]})
    >>> dc["a", 1]
    'j'
    """

    def __init__(self, obj, *args, original_path=None, **kwargs):
        # This often sets the original value for `self` for mutable types.
        # I.e. it gives a new list its content.
        # Immutables like tuples often already have the base class set via __new__.
        try:
            super().__init__(obj, *args, **kwargs)
        except TypeError:  # self is immutable - like a tuple
            pass

        self.original_path = original_path
        self.obj = obj

    def __getattr__(self, item):
        try:
            return self[item]
        except (KeyError, IndexError):
            raise AttributeError(f"DeepCollection has no attr {item}")

    def __getitem__(self, path):
        def get_raw():
            # self.obj instead of self to avoid unnecessary intermediate
            # DeepCollections. Just make a final conversion at the end.

            # Assume these aren't supposed to be iterated through.
            if _stringlike(path):
                return self.obj[path]

            try:
                iter(path)
            except TypeError:
                return self.obj[path]

            return get_by_path(self.obj, path)

        rv = get_raw()

        if _can_be_deep(rv):
            return DeepCollection(rv)
        return rv

    def get(self, path, default=None):
        try:
            return self.__getitem__(path)
        except (KeyError, IndexError, TypeError):
            return default
