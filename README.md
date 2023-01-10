## DeepCollection

[![PyPI version](https://badge.fury.io/py/deep-collections.svg)](https://pypi.org/project/deep-collections/)
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

deep_collections is a Python library that provides tooling for easy access to deep collections (dicts, lists, deques, etc), while maintaining a great portion of the collection's original API. The class DeepCollection class will automatically subclass the original collection that is provided, and add several quality of life extensions to make using deep collections much more enjoyable.

Got a bundle of JSON from an API? A large Python object from some data science problem? Some very lengthy set of instructions from some infrastructure as code like Ansible or SaltStack? Explore and modify it with ease.

DeepCollection can take virtually any kind of object including all built-in iterables, everything in the collections module, and [dotty-dicts](https://github.com/pawelzny/dotty_dict), and all of these nested in any fashion.

### Features

- Path traversal by supplying an list of path components as a key. This works for getting, setting, and deleting.
- Setting paths when parent parts do not exist.
- Path traversal through dict-like collections by dot chaining for getting
- Finding all paths to keys or subpaths
- Finding all values for keys or subpaths, and deduping them.
- Provide all of the above through a class that is:
    - easily instantiable
    - a native subclass of the type it was instantiated with
    - easily subclassable


### Path concept

DeepCollections has a concept of a "path" for nested collections, where a path is a sequence of keys or indices that if followed in order, traverse the deep collection. As a quick example, `{'a': ['b', {'c': 'd'}]}` could be traversed with the path `['a', 1, 'c']` to find the value `'d'`.

DeepCollections natively use paths as well as simple keys and indices. For `dc = DeepCollection(foo)`, items can be retrieved through the familiar `dc[path]` as normal if `path` is a simple key or index, or if it is an non-stringlike iterable path (strings are assumed to be literal keys). This is done with a custom `__getitem__` method. Similarly, `__delitem__` and `__setitem__` also support using a path. The same flexibility exists for the familiar methods like `.get`, which behaves the same as `dict.get`, but can accept a path as well as a key.

### DeepCollection object API

DeepCollections are instantiated as a normal class, optionally with a given initial collection as an arguement.

```python
from deep_collections import DeepCollection

dc = DeepCollection()
# or
dc = DeepCollection({"a": {"b": {"c": "d"}}})
# or
dc = DeepCollection(["a", ["b", ["c", "d"]]])
```

These are the noteworthy methods available on all DCs:

- `__getitem__`
- `__delitem__`
- `__setitem__`
- `get`
- `paths_to_value`
- `paths_to_key`
- `values_for_key`
- `deduped_values_for_key`

There are also corresponding functions availble that can use any native object that could be deep, but is not a `DeepCollection`, like a normal nested `dict` or `list`. This may be a convenient alternative to ad hoc traverse an object you already have, but it is also faster to use because it doesn't come with the initialization cost of a DeepCollection object. So if speed matters, use a function.

### deep_collections function API

All of the useful methods for DeepCollection objects are available as functions that can take a collection as an argument, as well as several other supporting functions, which are made plainly availble.

The core functions are focused on using the same path concept. The available functions and their related DC methods are:

- `getitem_by_path` - `DeepCollection().__getitem__`
- `get_by_path` - `DeepCollection().get`
- `set_by_path` - `DeepCollection().set_by_path`
- `del_by_path` - `DeepCollection().del_by_path`
- `paths_to_value` - `DeepCollection().paths_to_value`
- `paths_to_key` - `DeepCollection().paths_to_key`
- `values_for_key` - `DeepCollection().values_for_key`
- `deduped_values_for_key` - `DeepCollection().deduped_values_for_key`
- `dedupe_items`
- `resolve_path`
- `matched_keys`
