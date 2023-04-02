## Cumbersome data

```python
data = {
    "company": {
        "company.name": "Acme Corporation",
        "company.address": {
            "street": "1234 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip.code": "12345"
        },
        "employees": [
            {
                "email": "john.doe@example.com",
                "personal.info": {
                    "first.name": "John",
                    "last.name": "Doe",
                    "age": 30
                },
                "contact.info": {
                    "address": {
                        "street": "123 Main St.",
                        "city": "Anytown",
                        "state": "CA",
                        "zip.code": "12345"
                    },
                    "phone.numbers": [
                        "+1-555-555-5555",
                        "+1-555-555-5556"
                    ]
                },
                "work.info": {
                    "position": "Software Engineer",
                    "salary": 100000,
                    "projects": [
                        "Project A",
                        "Project B",
                        "Project C"
                    ]
                }
            },
            {
                "email": "jane.smith@example.com",
                "personal.info": {
                    "first.name": "Jane",
                    "last.name": "Smith",
                    "age": 25
                },
                "contact.info": {
                    "address": {
                        "street": "456 Broad St.",
                        "city": "Otherville",
                        "state": "NY",
                        "zip.code": "54321"
                    },
                    "phone.numbers": [
                        "+1-555-555-5555"
                    ]
                },
                "work.info": {
                    "position": "Marketing Manager",
                    "salary": 80000,
                    "projects": [
                        "Project D",
                        "Project E"]}}]}}
```

## Dotty Dict

### The Good

```python
from dotty_dict import dotty
dot = dotty(data)
dot['company']
dot['company.employees']
dot['company']['employees']
dot['company.employees.0']
```

### The Bad

#### Type

Is the dotty product a dict? What is it?

#### Input Issues

```python
dot['company.company.name']
dot = dotty(data, separator='/')

from dotty_dict import Dotty
dot = Dotty(data, separator='/')
dot['company/company.name']
```

```python
mixed = [
    {
        'name': 'Alice',
        'age': 30,
        'address': {
            'street': '123 Main St',
            'city': 'Anytown',
            'state': 'CA'
        },
        'interests': ['reading', 'hiking']
    },
    {
        'name': 'Bob',
        'age': 25,
        'address': {
            'street': '456 Elm St',
            'city': 'Othertown',
            'state': 'NY'
        },
        'interests': ['cooking', 'traveling']
    },
    {
        'name': 'Charlie',
        'age': 40,
        'address': {
            'street': '789 Oak St',
            'city': 'Somewhere',
            'state': 'TX'
        },
        'interests': ['painting', 'music']
    },
    {
        'name': 'Dave',
        'age': 35,
        'address': {
            'street': '321 Pine St',
            'city': 'Nowhere',
            'state': 'FL'
        },
    'interests': ['swimming', 'fishing']}]
```

```python
dot = dotty(mixed)
```

### Benedict

```python
from benedict import benedict
bene = benedict(data)
bene = benedict(data, keypath_separator="/")
```

#### The Good

```python
bene['company/company.name']
isinstance(bene, dict)

bene.search("Jane")
```

#### The Bad

#### Input Issues

Well, that separator thing by default still has edge cases. And

```python
bene = benedict(mixed)
```

## How can we do better?

### What do we really want?

#### Typing

- We want to be able to supply all kinds of collections, not just dict.
    - lists
    - tuple
    - deques
    - etc.
- I want _real_ dicts, list, etc
    - isinstance should work. A supplied dict should yield a dict instance.
    - A supplied list should work, _at all_, same for other collection types.
    - subclassing should be available.

#### Better Traversal

It would be nice if this path separator stuff was solved. How about an iterator that's not a string?

Instead of

```python
dot = Dotty(data, separator='/')
dot['company/company.name']
```

we can do

```python
dc = DeepCollection(data)
dc['company', 'company.name']
```

No seperator issue!

What if we're unsure of our data, or just want to type a quick shorthand?
Let's add a nice pattern matching traversal feature. We can handle globs, regex, etc.

```python
dc['**', '*zip*']
```

So, we have something similar to the separator issue before. What if we don't want to glob? Use strict traversal.

```python
dc = DeepCollection(data, strict=True)
dc['company', 'company.name']
dc['**', '*zip*']
```

I want native types to support better features surounding deep collections. For now though, I won't jump to C and make people actually run a fork of CPython. The next best thing is providing a way to add this functionality to all the existing types.

### Dynamic Inheritence

#### Via function-based class factory

```python
def deep_collection(obj):
    class DeepCollection(type(obj)):
        pass
    return DeepCollection(obj)

dc = deep_collection([1,2,3])
isinstance(dc, list)

dc = deep_collection({"a": 1})
isinstance(dc, dict)

# XXX direct access to DeepCollection? Customizing?
# XXX subclasses?
```

#### Via a metaclass

```python
# class type(name, bases, dict, **kwds)

class DynamicSubclasser(type):
    def __call__(cls, *args, **kwargs):
        obj = args[0]
        args = args[1:]

        dynamic_parent_cls = type(obj)

        new_cls = type(
            f"{cls.__name__}_{dynamic_parent_cls.__name__}",
            (cls, dynamic_parent_cls),
            {},
        )

        instance = new_cls.__new__(new_cls, *args, **kwargs)
        instance.__init__(obj, *args, **kwargs)
        return instance

class DeepCollection(metaclass=DynamicSubclasser):
    def __init__(
        self,
        obj,
        *args,
        **kwargs,
    ):
        super().__init__(obj, *args, **kwargs)

```

Check lists, dicts, tuples

```python
class DynamicSubclasser(type):
    def __call__(cls, *args, **kwargs):
        obj = args[0]
        args = args[1:]

        dynamic_parent_cls = type(obj)

        new_cls = type(
            f"{cls.__name__}_{dynamic_parent_cls.__name__}",
            (cls, dynamic_parent_cls),
            {},
        )

        instance = new_cls.__new__(new_cls, obj, *args, **kwargs)
        instance.__init__(obj, *args, **kwargs)
        return instance

class DeepCollection(metaclass=DynamicSubclasser):
    def __init__(
        self,
        obj,
        *args,
        **kwargs,
    ):
        try:
            super().__init__(obj, *args, **kwargs)
        except TypeError:
            pass
```

Yay, immutables!

### Traversal

We want to support a iterable based path traversal for all of the things.

- `get`
- `__getitem__` aka dc[x]
- `set`
- `__setitem__` aka dc[x] = y
- `del`
- `__delitem__` aka del dc[x]
- `paths_to_key`
- `paths_to_value`
- `values_for_key`
- ...

Tree traversal is (arguably) best done with recursion.

Excerpt from https://github.com/terminal-labs/deep_collections/blob/main/deep_collections/__init__.py

```python
def _paths_to_simple_key(obj, key, *args, match_with, \
    _current, **kwargs):
    ...
    if isinstance(obj, dict):
        for k, v in obj.items():
            if pathlike(v):
                yield from paths_to_key(...)
            if match_func(k, key):
                yield _current + [k]
    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            if pathlike(v):
                yield from paths_to_key(...)
            elif match_func(idx, key):
                yield _current + [idx]
    elif ...

def _paths_to_pathlike_key(...):
    ...
        yield from paths_to_key(...)

def paths_to_key(obj, key, ...):
    if pathlike(key):  # key is dict, defaultdict, etc.
        yield from _paths_to_pathlike_key(
            obj,
            key,
            ...
        )
    else:  # key is simple; str, int, float, etc.
        yield from _paths_to_simple_key(
            obj,
            key,
            ...
        )

```




Good enough, right? If something is quacking like a dict or list, treat it like one?
Nah, _really_ duck type it. Program to the interface.




```python
def _paths_to_simple_key(obj, key, *args, match_with, \
    _current, **kwargs):
    ...
    try:
        for k, v in obj.items():
            if pathlike(v):
                yield from paths_to_key(...)
            if match_func(k, key):
                yield _current + [k]
    except AttributeError:  # no .items
        for idx, v in enumerate(obj):
            if pathlike(v):
                yield from paths_to_key(...)
            elif match_func(idx, key):
                yield _current + [idx]
```

Generalizing is _hard_.

But it's possible. And it's _mostly_ testable. We can _exhaustively_ test the built-in types and collections module, and any 3rd party types we come across that seems worth it.

Ok, what do we have now?

```python
from deep_collections import DeepCollection
dc = DeepCollection(data)

dc['**', 'company.name']
dc['**', '*zip*']
dc.deduped_values_for_key("zip.code")

dc.paths_to_key("zip.code")
list(dc.paths_to_key("zip.code"))
dc[list(dc.paths_to_key("zip.code"))[1]]
```
