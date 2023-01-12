import operator
from functools import reduce
from functools import wraps

from .matching import match_style
from .utils import pathlike


def del_by_path(obj, path, match_with="glob", recursive_match_all=True, **kwargs):
    """Delete a key-value in a nested object in root by item sequence.
    from https://stackoverflow.com/a/14692747/913080

    >>> obj = {"a": ["b", {"c": "d"}]}
    >>> del_by_path(obj, ("a", 0))
    >>> obj
    {'a': [{'c': 'd'}]}
    """
    del getitem_by_path(obj, path[:-1], match_with, recursive_match_all, **kwargs)[path[-1]]


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


def resolve_path(obj, path, *args, match_with="glob", recursive_match_all=True, **kwargs):
    """Yield all paths that match the given globbed path."""
    if recursive_match_all and "**" in path:
        path = _simplify_double_splats(path)

    if recursive_match_all and "**" in path:
        # '**' can match any a path fragment of any length, including 0.
        double_splat_idx = path.index("**") + 1

        path_start = path[: double_splat_idx - 1]
        path_end = path[double_splat_idx:]

        if path_start:
            paths = list(
                resolve_path(
                    obj,
                    path_start,
                    *args,
                    match_with=match_with,
                    recursive_match_all=recursive_match_all,
                    **kwargs,
                )
            )
            for p in paths:
                path_ends = list(
                    paths_to_key(
                        getitem_by_path_strict(obj, p),
                        path_end,
                        *args,
                        match_with=match_with,
                        recursive_match_all=recursive_match_all,
                        **kwargs,
                    )
                )
                for end in path_ends:
                    yield p + end
        else:  # path started with "**"
            path_ends = list(
                paths_to_key(
                    obj,
                    path_end,
                    *args,
                    match_with=match_with,
                    recursive_match_all=recursive_match_all,
                    **kwargs,
                )
            )
            yield from path_ends
    elif path:
        first_step = path[0]
        path_remainder = path[1:]

        keys = matched_keys(obj, first_step, *args, match_with=match_with, **kwargs)

        if path_remainder:
            for key in keys:
                sub_obj = obj[key]
                smk = matched_keys(sub_obj, path_remainder[0], match_with, **kwargs)
                if smk:
                    yv = (
                        [key] + sk
                        for sk in resolve_path(
                            sub_obj,
                            path_remainder,
                            *args,
                            match_with=match_with,
                            recursive_match_all=recursive_match_all,
                            **kwargs,
                        )
                    )
                    yield from yv
        else:
            yield from ([key] for key in keys)


def matched_keys(obj, pattern, *args, match_with="glob", **kwargs):
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
    match_func = match_style(match_with).match

    try:
        iter(obj)
    except TypeError:
        return rv

    try:
        for key in obj.keys():
            if match_func(key, pattern, *args, **kwargs):
                rv.append(key)
    except AttributeError:
        for idx in range(len(obj)):
            if match_func(idx, pattern, *args, **kwargs):
                rv.append(idx)
    return rv


def getitem_by_path(obj, path, *args, match_with="glob", **kwargs):
    if not pathlike(path):  # e.g. str or int
        if not match_style(match_with).patterned(path, *args, **kwargs):
            return obj[path]
        path = [path]

    paths = list(resolve_path(obj, path, *args, match_with=match_with, **kwargs))

    if len(paths) > 1:
        return [getitem_by_path_strict(obj, p) for p in paths]
    elif len(paths) == 1:
        return getitem_by_path_strict(obj, paths[0])

    # Check if any part of the path appears to use a pattern. If so, return an empty
    # list, rather than a KeyError/IndexError because 0 matched results.

    if any(match_style(match_with).patterned(p, *args, **kwargs) for p in path):
        return paths

    return getitem_by_path_strict(obj, path)


def set_by_path(obj, path, value, *args, match_with="glob", recursive_match_all=True, **kwargs):
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
    # needed for later equality checks. In general paths don't need to be lists.
    path = list(path)

    traversed = []
    for part in path:
        # branch = get_by_path(obj, [part])
        branch = getitem_by_path(
            obj,
            traversed,
            *args,
            match_with=match_with,
            recursive_match_all=recursive_match_all,
            **kwargs,
        )
        traversed.append(part)

        try:
            branch[part]
        except (IndexError, KeyError):
            branch[part] = {}

        if traversed == path:
            branch[part] = value


def _paths_to_pathlike_key(obj, key, *args, match_with, _current, **kwargs):
    if len(key) > 1:
        resolved_paths = list(resolve_path(obj, key, *args, match_with=match_with, **kwargs))
        if resolved_paths:
            for path in resolved_paths:
                yield _current + path
        else:
            try:
                for k, v in obj.items():
                    if pathlike(v):
                        yield from paths_to_key(
                            v,
                            key,
                            *args,
                            match_with=match_with,
                            _current=_current + [k],
                            **kwargs,
                        )
            except AttributeError:
                for idx, i in enumerate(obj):
                    if pathlike(i):
                        yield from paths_to_key(
                            i,
                            key,
                            *args,
                            match_with=match_with,
                            _current=_current + [idx],
                            **kwargs,
                        )
    else:
        yield from paths_to_key(
            obj,
            next(iter(key)),
            *args,
            match_with=match_with,
            _current=_current,
            **kwargs,
        )


def _paths_to_simple_key(obj, key, *args, match_with, _current, **kwargs):
    match_func = match_style(match_with).match
    try:
        for k, v in obj.items():
            if pathlike(v):
                yield from paths_to_key(v, key, match_with=match_with, _current=_current + [k], **kwargs)
            if match_func(k, key):
                yield _current + [k]
    except AttributeError:  # no .items
        for idx, v in enumerate(obj):
            if pathlike(v):
                yield from paths_to_key(v, key, match_with=match_with, _current=_current + [idx], **kwargs)
            elif match_func(idx, key):
                yield _current + [idx]


def paths_to_key(
    obj,
    key,
    *args,
    match_with="glob",
    recursive_match_all=True,
    _current=None,
    **kwargs,
):
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
    if not pathlike(obj):
        raise TypeError(f"First argument must be able to be deep, not type '{type(obj)}'")

    if _current is None:
        _current = []

    if pathlike(key):
        yield from _paths_to_pathlike_key(
            obj,
            key,
            *args,
            match_with=match_with,
            _current=_current,
            recursive_match_all=recursive_match_all,
            **kwargs,
        )
    else:  # key is simple; str, int, float, etc.
        yield from _paths_to_simple_key(
            obj,
            key,
            *args,
            match_with=match_with,
            _current=_current,
            recursive_match_all=recursive_match_all,
            **kwargs,
        )


def _paths_to_pathlike_value(obj, value, *args, match_with, _current, **kwargs):
    # Don't test non-pathlike obj elements since they can't match a pathlike value.
    # Being pathlike is a proxy test for being deep. If something isn't pathlike, it can't be deep.
    try:
        for k, v in obj.items():
            if pathlike(v):
                yield from paths_to_value(v, value, *args, match_with=match_with, _current=_current + [k], **kwargs)
    except AttributeError:
        for idx, i in enumerate(obj):
            if pathlike(i):
                yield from paths_to_value(i, value, *args, match_with=match_with, _current=_current + [idx], **kwargs)


def _paths_to_simple_value(obj, value, *args, match_with, _current, **kwargs):
    match_func = match_style(match_with).match

    try:
        for k, v in obj.items():
            if pathlike(v):
                yield from paths_to_value(v, value, *args, match_with=match_with, _current=_current + [k], **kwargs)
            if match_func(v, value, *args, **kwargs):
                yield _current + [k]
    except AttributeError:  # no .items
        for idx, i in enumerate(obj):
            if pathlike(i):
                yield from paths_to_value(i, value, *args, match_with=match_with, _current=_current + [idx], **kwargs)
            elif match_func(i, value, *args, **kwargs):
                yield _current + [idx]


def paths_to_value(
    obj,
    value,
    *args,
    match_with="glob",
    recursive_match_all=True,
    _current=None,
    **kwargs,
):
    """Return the path to a specified value in an object.
    A value may be simple or iterable, e.g. a str, int, list, dict, etc, as long as it
    can be used with one of the supported pattern matches,
    or supports an equality test.

    >>> list(paths_to_value({"x": "value"}, "value"))
    [['x']]
    >>> list(paths_to_value(["value"], "value"))
    [[0]]
    """
    if not pathlike(obj):
        raise TypeError(f"First argument must be able to be deep, not type '{type(obj)}'")

    match_func = match_style(match_with).match

    if _current is None:
        _current = []

    if match_func(obj, value, *args, **kwargs):
        yield _current
    # if no match, recurse
    elif pathlike(value):  # e.g. list, dict. Can be another path
        yield from _paths_to_pathlike_value(
            obj,
            value,
            *args,
            match_with=match_with,
            _current=_current,
            recursive_match_all=recursive_match_all,
            **kwargs,
        )
    else:  # value is simple; str, int, float, etc.
        yield from _paths_to_simple_value(
            obj,
            value,
            *args,
            match_with=match_with,
            _current=_current,
            recursive_match_all=recursive_match_all,
            **kwargs,
        )


def values_for_key(obj, key, *args, match_with="glob", recursive_match_all=True, **kwargs):
    """Generate all values for a given key.

    >>> list(values_for_key([{"x": {"y": "value", "z": {"y": "value"}}, "y": {1: 2}}], "y"))
    ['value', 'value', {1: 2}]
    """
    for path in paths_to_key(
        obj,
        key,
        *args,
        match_with=match_with,
        recursive_match_all=recursive_match_all,
        **kwargs,
    ):
        yield getitem_by_path(
            obj,
            path,
            *args,
            match_with=match_with,
            recursive_match_all=recursive_match_all,
            **kwargs,
        )


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
    >>> foo = Foo([5])
    >>> foo == [5]
    True
    >>> isinstance(foo, list)
    True
    >>> foo = Foo()
    >>> foo == {}
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

    def __init__(
        self,
        obj,
        *args,
        return_deep=True,
        match_with="glob",
        recursive_match_all=True,
        match_args=None,
        match_kwargs=None,
        **kwargs,
    ):
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
        self.match_with = match_with
        self.recursive_match_all = recursive_match_all
        self.match_args = match_args or ()
        self.match_kwargs = match_kwargs or {}

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
        if not name.startswith("_") and name not in dir(DeepCollection) and name in dir(self):
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
        # Use self._obj instead of self to avoid unnecessary intermediate
        # DeepCollections. Just make a final conversion at the end.

        rv = getitem_by_path(
            self._obj,
            path,
            *self.match_args,
            match_with=self.match_with,
            recursive_match_all=self.recursive_match_all,
            **self.match_kwargs,
        )

        if pathlike(rv) and self.return_deep:
            return DeepCollection(
                rv,
                match_with=self.match_with,
                recursive_match_all=self.recursive_match_all,
                match_args=self.match_args,
                match_kwargs=self.match_kwargs,
            )
        return rv

    def __delitem__(self, path):
        if pathlike(path):
            del_by_path(
                self,
                path,
                *self.match_args,
                match_with=self.match_with,
                recursive_match_all=self.recursive_match_all,
                **self.match_kwargs,
            )
        else:
            super().__delitem__(path)
            del self._obj[path]

    def __setitem__(self, path, value):
        if pathlike(path):
            set_by_path(
                self,
                path,
                value,
                *self.match_args,
                match_with=self.match_with,
                recursive_match_all=self.recursive_match_all,
                **self.match_kwargs,
            )
        else:
            super().__setitem__(path, value)
            self._obj[path] = value

    def __repr__(self):
        super_repr = super().__repr__()
        # Some collections types already display self when self isn't the original type,
        # but that's actually not what we want here, so if we find that, fix it.
        super_repr = super_repr.replace(self.__class__.__name__, self.original_type.__name__)
        return f"DeepCollection({super_repr})"

    # Common public methods
    def get(self, path, default=None, *, match_args=None, match_with=None, recursive_match_all=None, match_kwargs=None):
        # These are one-offs and should not mutate self
        match_args = match_args or self.match_args
        match_with = match_with or self.match_with
        match_kwargs = match_kwargs or self.match_kwargs
        if recursive_match_all is None:
            recursive_match_all = self.recursive_match_all

        try:
            rv = getitem_by_path(
                self._obj,
                path,
                *match_args,
                match_with=match_with,
                recursive_match_all=recursive_match_all,
                **match_kwargs,
            )
        except (KeyError, IndexError, TypeError):
            return default

        if pathlike(rv) and self.return_deep:  # pathlike is a proxy test for an object being deepable
            # retain settings from self, not the one-off values
            return DeepCollection(
                rv,
                match_with=self.match_with,
                recursive_match_all=self.recursive_match_all,
                match_args=self.match_args,
                match_kwargs=self.match_kwargs,
            )
        return rv

    def items(self, *args, **kwargs):
        # XXX what about when it doesn't exist?
        return super().items(*args, **kwargs)

    # Unique public methods
    def paths_to_key(self, key, *args, match_with=None, recursive_match_all=None, **kwargs):
        """
        >>> list(DeepCollection([{"x": {"y": "value", "z": {"y": "asdf"}}}]).paths_to_key("y"))
        [[0, 'x', 'y'], [0, 'x', 'z', 'y']]
        """
        match_with = match_with or self.match_with
        match_args = args or self.match_args
        match_kwargs = kwargs or self.match_kwargs
        if recursive_match_all is None:
            recursive_match_all = self.recursive_match_all

        yield from paths_to_key(
            self, key, *match_args, match_with=match_with, recursive_match_all=recursive_match_all, **match_kwargs
        )

    def values_for_key(self, key, *args, match_with=None, recursive_match_all=None, **kwargs):
        """
        >>> dc = DeepCollection([{"x": {"y": "v", "z": {"y": "v"}}, "y": {1: 2}}], return_deep=False)
        >>> list(dc.values_for_key("y"))
        ['v', 'v', {1: 2}]
        """
        match_with = match_with or self.match_with
        match_args = args or self.match_args
        match_kwargs = kwargs or self.match_kwargs
        if recursive_match_all is None:
            recursive_match_all = self.recursive_match_all

        yield from values_for_key(
            self, key, *match_args, match_with=match_with, recursive_match_all=recursive_match_all, **match_kwargs
        )

    def deduped_values_for_key(self, key, *args, match_with=None, recursive_match_all=None, **kwargs):
        """
        >>> dc = DeepCollection([{"x": {"y": "v", "z": {"y": "v"}}, "y": {1: 2}}], return_deep=False)
        >>> 'v' in dc.deduped_values_for_key("y")  # order not gaurunteed
        True
        >>> {1: 2} in dc.deduped_values_for_key("y")  # order not gaurunteed
        True
        """
        match_with = match_with or self.match_with
        match_args = args or self.match_args
        match_kwargs = kwargs or self.match_kwargs
        if recursive_match_all is None:
            recursive_match_all = self.recursive_match_all

        return deduped_items(
            list(
                values_for_key(
                    self,
                    key,
                    *match_args,
                    match_with=match_with,
                    recursive_match_all=recursive_match_all,
                    **match_kwargs,
                )
            )
        )
