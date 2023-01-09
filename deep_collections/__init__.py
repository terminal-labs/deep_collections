import operator
from fnmatch import fnmatchcase
from functools import reduce
from functools import wraps
from itertools import chain


def _stringlike(obj):
    """Return True if obj is an instance of str, bytes, or bytearray
    >>> _stringlike("a")
    True
    >>> _stringlike(b"a")
    True
    >>> _stringlike(1)
    False
    """
    return any(isinstance(obj, base) for base in (str, bytes, bytearray))


def _non_stringlike_iterable(obj):  # TODO rename to _non_stringlike_iterable
    """Guess if an object could be a nested collection.

    The general heuristic is that an object must be iterable, but not stringlike
    so that an element can be arbitrary, like another collection.

    Since this is a simple check, there are false positives, but this works with
    basic types.
    >>> _non_stringlike_iterable([1])
    True
    >>> _non_stringlike_iterable({1:2})
    True
    >>> _non_stringlike_iterable(1)
    False
    >>> _non_stringlike_iterable("a")
    False
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
    del getitem_by_path(obj, path[:-1])[path[-1]]


def getitem_by_path_strict(obj, path):
    """Access a nested object in obj by iterable path.
    from https://stackoverflow.com/a/14692747/913080

    This function is provided as a faster alternative to get_by_path
    that offers no glob features.

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> getitem_by_path(obj, ["a", 1, "c"])
    'd'
    """
    return reduce(operator.getitem, path, obj)


def get_by_path_strict(obj, path, default=None):
    """Access a nested object in obj by iterable path.
    from https://stackoverflow.com/a/14692747/913080

    This function is provided as a faster alternative to get_by_path
    that offers no glob features.

    As with the standard dict.get, this returns an optional default or None
    rather than a KeyError.

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> get_by_path_strict(obj, ["a", 1, "c"])
    'd'
    >>> get_by_path_strict(obj, ["a", 1, "e"])

    >>> get_by_path_strict(obj, ["a", 1, "e"], "x")
    'x'
    """
    try:
        return reduce(operator.getitem, path, obj)
    except KeyError:
        return default


def _match(a, b):
    try:
        return fnmatchcase(a, b)
    except TypeError:  # fallback to normal eq
        return a == b


def _simplify_double_splats(path):
    """Return an equivalent path, removing any unnecessary double splats."""
    # remove ending "**"
    while True:
        if path and path[-1] == "**":
            del path[-1]
        else:
            break

    # Collapse consecutive "**"
    i = 0
    while i < len(path) - 1:
        if path[i] == "**" == path[i + 1]:
            del path[i]
        else:
            i = i + 1

    return path


def resolve_path(obj, path, recursive_match_all=True):
    """Yield all paths that match the given globbed path."""
    # Raise clear error early if path isn't iterable
    iter(path)

    if recursive_match_all and "**" in path:
        path = _simplify_double_splats(path)

    if recursive_match_all and "**" in path:
        # '**' can match any a path fragment of any length, including 0.
        double_splat_idx = path.index("**") + 1

        path_start = path[: double_splat_idx - 1]
        path_end = path[double_splat_idx:]

        if path_start:
            paths = list(resolve_path(obj, path_start))
            for p in paths:
                path_ends = list(paths_to_key(getitem_by_path_strict(obj, p), path_end))
                for end in path_ends:
                    yield p + end
        else:  # path started with "**"
            path_ends = list(paths_to_key(obj, path_end))
            yield from path_ends
    elif path:
        first_step = path[0]
        path_remainder = path[1:]

        keys = matched_keys(obj, first_step)

        if path_remainder:
            for key in keys:
                sub_obj = obj[key]
                smk = matched_keys(sub_obj, path_remainder[0])
                if smk:
                    yv = ([key] + sk for sk in resolve_path(sub_obj, path_remainder))
                    yield from yv
        else:
            yield from ([key] for key in keys)


def matched_keys(obj, key):
    """
    >>> matched_keys(1, '0')
    []
    >>> matched_keys([1], '0')
    []
    >>> matched_keys([1], 0)
    [0]
    >>> matched_keys({'a': 1} , 0)
    []
    >>> matched_keys({'a': 1} , 'a')
    ['a']
    >>> matched_keys({'a': 1} , '?')
    ['a']
    >>> matched_keys({'ab': 1, 'cde': 2} , '*')
    ['ab', 'cde']
    """
    rv = []

    try:
        iter(obj)
    except TypeError:
        return rv

    try:
        for k in obj.keys():
            if patterned(key):
                if k == key or match_glob(str(k), key):
                    rv.append(k)
            else:
                if k == key or match_glob(k, key):
                    rv.append(k)
    except AttributeError:
        for idx in range(len(obj)):
            if patterned(key):
                if idx == key or match_glob(str(idx), key):
                    rv.append(idx)
            else:
                if idx == key or match_glob(idx, key):
                    rv.append(idx)
    return rv


def match_glob(a, b):
    try:
        return fnmatchcase(a, b)
    except TypeError:  # e.g. b could be an int - not a match
        False


# rename to indicate globbing
# move into class?
def patterned(txt):
    return _stringlike(txt) and any(char in txt for char in ("*", "?", "["))


def getitem_by_path(obj, path: list):
    paths = list(resolve_path(obj, path))

    if len(paths) > 1:
        return [getitem_by_path_strict(obj, p) for p in paths]
    elif len(paths) == 1:
        return getitem_by_path_strict(obj, paths[0])

    # Check if any part of the path appears to use a pattern. If so, return an empty
    # list, rather than a KeyError/IndexError because 0 matched results.
    if any(patterned(p) for p in path):
        return paths

    return getitem_by_path_strict(obj, path)


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
        # branch = get_by_path(obj, [part])
        branch = getitem_by_path(obj, traversed)
        traversed.append(part)

        try:
            branch[part]
        except (IndexError, KeyError):
            branch[part] = {}

        if traversed == path:
            branch[part] = value


def paths_to_key(obj, key, current=None):
    """Return the path to a specified key in an object.
    A key may be simple or iterable, e.g. a str, int, list, dict, etc, as long as it
    can be used with one of the supported pattern matches,
    or supports an equality test.

    >>> list(paths_to_key({"x": "value"}, "x"))
    [['x']]
    >>> list(paths_to_key({"x": {"y": "value"}}, "y"))
    [['x', 'y']]
    >>> list(paths_to_key(["value"], "x"))
    []
    >>> list(paths_to_key([{"x": "value"}], "x"))
    [[0, 'x']]
    >>> list(paths_to_key({"x": ["a", "b", {"y": "value"}]}, "y"))
    [['x', 2, 'y']]
    >>> list(paths_to_key([{"x": {"y": "value", "z": {"y": "asdf"}}}], "y"))
    [[0, 'x', 'y'], [0, 'x', 'z', 'y']]
    >>> # compound keys
    >>> list(paths_to_key({"x": {"y": "value"}}, ["x", "y"]))
    [['x', 'y']]
    >>> list(paths_to_key([{"x": {"y": "value", "z": {"y": "asdf"}}}], ["x", "y"]))
    [[0, 'x', 'y']]
    >>> list(paths_to_key({"x": {"y": "value"}}, "y"))
    [['x', 'y']]
    >>> list(paths_to_key({"x": 0}, ["y"]))
    []
    """
    if current is None:
        current = []

    if not _non_stringlike_iterable(obj):
        raise TypeError(
            f"First argument must be able to be deep, not type '{type(obj)}'"
        )

    compound_key = _non_stringlike_iterable(key)
    if compound_key and len(key) > 1:
        resolved_paths = list(resolve_path(obj, key))
        if resolved_paths:
            for key in resolved_paths:
                yield current + key
        else:
            try:
                for k, v in obj.items():
                    if _non_stringlike_iterable(v):
                        yield from paths_to_key(v, key, current + [k])
            except AttributeError:
                for idx, i in enumerate(obj):
                    if _non_stringlike_iterable(i):
                        yield from paths_to_key(i, key, current + [idx])
    elif compound_key:
        for k in key:  # Only iterates once, but works for dict or list-like keys
            yield from paths_to_key(obj, k)
    else:  # key is simple; str, int, float, etc.
        try:
            for k, v in obj.items():
                if _non_stringlike_iterable(v):
                    yield from paths_to_key(v, key, current + [k])
                if _match(k, key):
                    yield current + [k]
        except AttributeError:  # no .items
            for idx, v in enumerate(obj):
                if _non_stringlike_iterable(v):
                    yield from paths_to_key(v, key, current + [idx])
                elif _match(idx, key):
                    yield current + [idx]


def paths_to_value(obj, value, current=None):
    """Return the path to a specified value in an object.
    A value may be simple or iterable, e.g. a str, int, list, dict, etc, as long as it
    can be used with one of the supported pattern matches,
    or supports an equality test.

    >>> list(paths_to_value({"x": "value"}, "value"))
    [['x']]
    >>> list(paths_to_value(["value"], "value"))
    [[0]]
    """
    if current is None:
        current = []

    if not _non_stringlike_iterable(obj):
        raise TypeError(
            f"First argument must be able to be deep, not type '{type(obj)}'"
        )

    if _match(obj, value):
        yield current
    elif _non_stringlike_iterable(value):  # e.g. list, dict. Can be another path
        try:
            gbp = getitem_by_path(obj, value)
        except (KeyError, IndexError, TypeError):
            try:
                for k, v in obj.items():
                    if _non_stringlike_iterable(v):
                        yield from paths_to_value(v, value, current + [k])
            except AttributeError:
                for idx, i in enumerate(obj):
                    if _non_stringlike_iterable(i):
                        yield from paths_to_value(i, value, current + [idx])
        else:
            yield current + list(value)
    else:  # value is simple; str, int, float, etc.
        try:
            for k, v in obj.items():
                if _non_stringlike_iterable(v):
                    yield from paths_to_value(v, value, current + [k])
                if _match(v, value):
                    yield current + [k]
        except AttributeError:  # no .items
            for idx, i in enumerate(obj):
                if _non_stringlike_iterable(i):
                    yield from paths_to_value(i, value, current + [idx])
                elif _match(i, value):
                    yield current + [idx]


def values_for_key(obj, key):
    """Generate all values for a given key.

    >>> list(values_for_key([{"x": {"y": "value", "z": {"y": "value"}}, "y": {1: 2}}], "y"))
    ['value', 'value', {1: 2}]
    """
    for path in paths_to_key(obj, key):
        yield getitem_by_path(obj, path)


def deduped_items(items):
    """Return a dedpued list of all items. This is not trivial
    since some values are dicts and thus are not hashable.

    >>> deduped_items(["a", {1:{2:{3:4}}}, {4}, {1:{2:{3:4}}}, {4}, {4}, 1, 1, "a"])
    [{1: {2: {3: 4}}}, {4}, 1, 'a']
    >>> deduped_items([{1:{2:{3:4}}}, {1:{2:{3:4}}}, {1:{2:{3:7}}}])
    [{1: {2: {3: 4}}}, {1: {2: {3: 7}}}]
    """
    try:
        return list(set(items))
    except TypeError:
        # next line from https://stackoverflow.com/a/9428041
        return [i for n, i in enumerate(items) if i not in items[n + 1 :]]  # noqa: E203


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

        # If a DC is given, we must use the original type as the parent_cls. We don't
        # want or need to nest DC types, and we if we don't flattten the inheritence
        # we get a metaclass conflict can't produce a consistent method resolution.
        if hasattr(obj, "_obj") and isinstance(obj, DeepCollection):
            dynamic_parent_cls = type(obj._obj)
        else:
            dynamic_parent_cls = type(obj)

        # Make a new_cls that inherits from the dynamic_parent_cls, and resolve any
        # potential metaclass conflicts, like when the object has its own metaclass
        # already, as when it's an ABC.
        try:
            # Resultant type is deep_collections.DeepCollection_[type]
            new_cls = type(
                f"{cls.__name__}_{dynamic_parent_cls.__name__}",
                (cls, dynamic_parent_cls),
                {},
            )
        except TypeError:
            # Resolve metaclass conflict.
            # Create a new metaclass on the fly, merging the two we have.
            mcls = type(cls)
            cls.__class__ = type(
                f"{mcls.__name__}_{dynamic_parent_cls.__name__}",
                (mcls, type(dynamic_parent_cls)),
                {},
            )
            # Resultant type is likely abc.DeepCollection_[type]
            new_cls = type(
                f"{cls.__name__}_{dynamic_parent_cls.__name__}",
                (cls, dynamic_parent_cls),
                {},
            )

        # Create the instance and initialize it with the given object.
        # Sets obj in instance for immutables like tuple
        # instance = new_cls.__new__(new_cls, obj, *args, **kwargs)
        instance = new_cls.__new__(new_cls, obj, *args, **kwargs)
        # Sets obj in instance for mutables like list
        instance.__init__(obj, *args, **kwargs)

        return instance

    def __instancecheck__(cls, inst):
        """If the dynamic parent subclasses an abc like UserList, the result
        __instancecheck__ would fail against the original base class.

        I think this is because our calculated class's __instancecheck__ would rely on
        ._abc_impl being implemented correctly on the immediate parent class, which is
        our base. Rather than trying to correctly implement a modified _abc_impl
        ourselves, we can use the naive method given in
        https://peps.python.org/pep-3119/#overloading-isinstance-and-issubclass
        """
        return any(cls.__subclasscheck__(c) for c in {type(inst), inst.__class__})

    def __subclasscheck__(cls, sub):
        """If the dynamic parent subclasses an abc like UserList, the result
        __subclasscheck__ would fail against the original base class.

        I think this is because our calculated class's __subclasscheck__ would rely on
        ._abc_impl being implemented correctly on the immediate parent class, which is
        our base. Rather than trying to correctly implement a modified _abc_impl
        ourselves, we can use the naive method given in
        https://peps.python.org/pep-3119/#overloading-isinstance-and-issubclass
        """
        candidates = cls.__dict__.get("__subclass__", set()) | {cls}
        return any(c in candidates for c in sub.mro())


class DeepCollection(metaclass=DynamicSubclasser):
    """A class intended to allow easy access to items of deep collections.

    >>> dc = DeepCollection({"a": ["i", "j", "k"]})
    >>> dc["a", 1]
    'j'
    """

    def __init__(self, obj, *args, return_deep=True, **kwargs):
        # Set instance vars first in case anything else (like super().__init__) accesses
        # methods that trigger our __getattribute__, which needs them present.
        #
        # Record the original object. Useful to avoid unnecessary, costly DC instantiation.
        # __getattribute__ override keeps this in sync with self
        # when self mutates, as in list.append.
        if hasattr(obj, "_obj") and isinstance(obj, DeepCollection):
            # A DC made from a DC should still record the real original object.
            self._obj = obj._obj
        else:
            self._obj = obj

        self.original_type = type(self._obj)
        self.return_deep = return_deep

        # This often sets the original value for `self` for mutable types.
        # I.e. it gives a new list its content.
        # Immutables like tuple often already have the base class set via __new__.
        try:
            super().__init__(self._obj, *args, **kwargs)
        except TypeError:  # self is immutable like tuple
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

            if isinstance(self._obj, Dotty):
                super().__init__(self._obj.to_dict(), *args, **kwargs)
            else:  # We have Dotty available, but that's not obj.
                raise e

    # Unique private methods
    def _ensure_post_call_sync(self, method):
        """Wrap any method to ensure that if if mutates self,
        self._obj is mutated to match. Inherited methods like list's `append` would act
        on self, but we also rely on composistion, so self._obj needs to be kept in sync.

        This decorator, used in __getattribute__, allows us to passively catch such
        cases without having to know ahead of time what these methods are. This gives
        us more generality, and also lets us not have to include such methods in this
        class. We also don't want an e.g. `append` here unless the parent has it.
        """

        @wraps(method)
        def wrapped(*args, **kwargs):
            rv = method(*args, **kwargs)  # may set self and not _obj

            # sync
            if self._obj != self:
                self._obj = type(self._obj)(self)

            return rv

        return wrapped

    # Common private methods
    def __getattribute__(self, name):
        """Overridden to ensure self._obj stays in sync with self if self mutates
        from an inherited method being called.

        See self._ensure_post_call_sync docstring for details.

        >>> dc = DeepCollection([1])
        >>> dc.append(2)  # list method that normaly just changes self
        >>> dc._obj
        [1, 2]
        """
        if (
            not name.startswith("_")
            and name not in dir(DeepCollection)
            and name in dir(self)
        ):
            method = object.__getattribute__(self, name)
            if callable(method):
                # wrapped
                return self._ensure_post_call_sync(method)
        return object.__getattribute__(self, name)

    def __getattr__(self, item):
        """This turns a missing dot attr access into a getitem attempt."""
        try:
            return self[item]
        except (KeyError, IndexError, TypeError):
            raise AttributeError(
                f"'DeepCollection' object, instance of '{type(self._obj)}', has no attribute '{item}'. "
            )

    def __getitem__(self, path):
        def get_raw():
            # Use self._obj instead of self to avoid unnecessary intermediate
            # DeepCollections. Just make a final conversion at the end.

            # Assume strs aren't supposed to be iterated through.
            if _stringlike(path):
                return self._obj[path]

            try:
                iter(path)
            except TypeError:
                return self._obj[path]

            return getitem_by_path(self._obj, path)

        rv = get_raw()

        if _non_stringlike_iterable(rv) and self.return_deep:
            return DeepCollection(rv)
        return rv

    def __delitem__(self, path):
        if _non_stringlike_iterable(path):
            del_by_path(self, path)
        else:
            super().__delitem__(path)
            del self._obj[path]

    def __setitem__(self, path, value):
        if _non_stringlike_iterable(path):
            set_by_path(self, path, value)
        else:
            super().__setitem__(path, value)
            self._obj[path] = value

    def __repr__(self):
        super_repr = super().__repr__()
        # Some collections types already display self when self isn't the original type,
        # but that's actually not what we want here, so if we find that, fix it.
        super_repr = super_repr.replace(
            self.__class__.__name__, self.original_type.__name__
        )
        return f"DeepCollection({super_repr})"

    # Common public methods
    def get(self, path, default=None):
        try:
            return self.__getitem__(path)
        except (KeyError, IndexError, TypeError):
            return default

    def items(self, *args, **kwargs):
        # XXX what about when it doesn't exist?
        return super().items(*args, **kwargs)

    # Unique public methods
    def paths_to_key(self, key):
        """
        >>> list(DeepCollection([{"x": {"y": "value", "z": {"y": "asdf"}}}]).paths_to_key("y"))
        [[0, 'x', 'y'], [0, 'x', 'z', 'y']]
        """
        yield from paths_to_key(self, key)

    def values_for_key(self, key):
        """
        >>> dc = DeepCollection([{"x": {"y": "v", "z": {"y": "v"}}, "y": {1: 2}}], return_deep=False)
        >>> list(dc.values_for_key("y"))
        ['v', 'v', {1: 2}]
        """
        yield from values_for_key(self, key)

    def deduped_values_for_key(self, key):
        """
        >>> dc = DeepCollection([{"x": {"y": "v", "z": {"y": "v"}}, "y": {1: 2}}], return_deep=False)
        >>> 'v' in dc.deduped_values_for_key("y")  # order not gaurunteed
        True
        >>> {1: 2} in dc.deduped_values_for_key("y")  # order not gaurunteed
        True
        """
        return deduped_items(list(values_for_key(self, key)))
