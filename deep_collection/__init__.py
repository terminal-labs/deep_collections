import operator
from functools import reduce


def _stringlike(obj):
    return any(isinstance(obj, base) for base in (str, bytes, bytearray))


def _can_be_deep(obj):
    """Determine if an object could be a nested collection.

    The general heuristic is that an object must be iterable, but not stringlike
    so that an element can be arbitrary, like another collection.
    """
    try:
        iter(obj)
    except TypeError:
        return False

    if _stringlike(obj):
        return False

    return True


def del_by_path(obj, path):
    """Delete a key-value in a nested object in root by item sequence.
    from https://stackoverflow.com/a/14692747/913080

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> del_by_path(obj, ("a", 0))
    >>> obj
    {'a': [{'c': 'd'}]}
    """
    del get_by_path(obj, path[:-1])[path[-1]]


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

    If the path doesn't fully exist, this will create it to set the value,
    making dicts along the way.

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> set_by_path(obj, ["a", 0], "foo")
    >>> obj
    {'a': ['foo', {'c': 'd'}]}
    >>> set_by_path(obj, ["a", 1, "e"], "foo")
    >>> obj
    {'a': ['foo', {'c': 'd', 'e': 'foo'}]}
    >>> obj = {}
    >>> set_by_path(obj, range(10), 10)
    >>> obj
    {0: {1: {2: {3: {4: {5: {6: {7: {8: {9: 10}}}}}}}}}}
    """
    path = list(path)  # needed for later equality checks

    traversed = []
    for part in path:
        branch = get_by_path(obj, traversed)
        traversed.append(part)

        try:
            branch[part]
        except (IndexError, KeyError):
            branch[part] = {}

        if traversed == path:
            branch[part] = value


def paths_to_field(obj, field, current=None):
    """Return the path to a specified field and the associated value. This is useful to
    determin what is using e.g. "password".

    Because this can handle a generalized config, which can have lists in it, this can
    also handle a list of all configs.

    >>> list(paths_to_field({"x": "value"}, "x"))
    [['x']]
    >>> list(paths_to_field({"x": {"y": "value"}}, "y"))
    [['x', 'y']]
    >>> list(paths_to_field(["value"], "x"))
    []
    >>> list(paths_to_field([{"x": "value"}], "x"))
    [[0, 'x']]
    >>> list(paths_to_field({"x": ["a", "b", {"y": "value"}]}, "y"))
    [['x', 2, 'y']]
    >>> list(paths_to_field([{"x": {"y": "value", "z": {"y": "asdf"}}}], "y"))
    [[0, 'x', 'y'], [0, 'x', 'z', 'y']]
    """
    if current is None:
        current = []

    # field is compound
    if _can_be_deep(field):
        try:
            get_by_path(obj, field)
        except (KeyError, IndexError, TypeError):
            try:
                for k, v in obj.items():
                    yield from paths_to_field(v, field, current + [k])
            except AttributeError:
                for idx, i in enumerate(obj):
                    yield from paths_to_field(i, field, current + [idx])
        else:
            yield current + list(field)
    else:  # field is simple; str, int, float, etc.
        try:
            for k, v in obj.items():
                if k == field:
                    yield current + [k]
                if _can_be_deep(v):
                    yield from paths_to_field(v, field, current + [k])
        except AttributeError:
            for idx, i in enumerate(obj):
                if i == field:
                    yield current + [idx]
                if _can_be_deep(i):
                    yield from paths_to_field(i, field, current + [idx])


def values_for_field(obj, field):
    """Generate all values for a given field.

    >>> list(values_for_field([{"x": {"y": "value", "z": {"y": "value"}}, "y": {1: 2}}], "y"))
    ['value', 'value', {1: 2}]
    """
    for path in paths_to_field(obj, field):
        yield get_by_path(obj, path)


class DynamicSubclasser(type):
    """Return an instance of the class that uses this as its metaclass.
    This metaclass allows for a class to be instantiated with an argument,
    and assume that argument's class as its parent class.

    >>> class Foo(metaclass=DynamicSubclasser): pass
    >>> foo = Foo(5)
    >>> isinstance(foo, int)
    True
    """

    def __call__(cls, *args, **kwargs):
        if args:
            obj = args[0]
            args = args[1:]
        else:
            obj = {}

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
        except AttributeError as e:
            # NOTE: compat - dotty_dict
            # This amounts to a token compatibility with dotty_dict. Many methods and
            # features overlap. Try to prefer ours, and fall back to theirs.
            #
            # dotty_dict enforces an instance check on its first arg that dotty_dict
            # itself fails.
            #
            # Can't test for dotty without dotty available. If that's the case, fall
            # back to the original AttributeError because we can't tell why we get it.
            try:
                from dotty_dict import Dotty
            except ModuleNotFoundError:
                raise e

            if isinstance(obj, Dotty):
                super().__init__(obj.to_dict(), *args, **kwargs)
            else:  # We have Dotty available, but that's not obj.
                raise e

        # In addition to inheritence, we also use composition so that we can do faster
        # calculations internally against the original type, without having the overhead
        # of our metaclass at every step of the way. Composition isn't strictly
        # necessary, but helps performance a lot.
        self.obj = obj

    def __getattr__(self, item):
        try:
            return self[item]
        except (KeyError, IndexError):
            raise AttributeError(f"DeepCollection has no attr {item}")

    def __getitem__(self, path):
        def get_raw():
            # Use self.obj instead of self to avoid unnecessary intermediate
            # DeepCollections. Just make a final conversion at the end.

            # Assume strs aren't supposed to be iterated through.
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

    def __delitem__(self, path):
        if _can_be_deep(path):
            del_by_path(self, path)
        else:
            super().__delitem__(path)
            del self.obj[path]

    def __setitem__(self, path, value):
        if _can_be_deep(path):
            set_by_path(self, path, value)
        else:
            super().__setitem__(path, value)
            self.obj[path] = value

    def get(self, path, default=None):
        try:
            return self.__getitem__(path)
        except (KeyError, IndexError, TypeError):
            return default

    def paths_to_field(self, field):
        yield from paths_to_field(self, field)

    def values_for_field(self, field):
        yield from values_for_field(self, field)
