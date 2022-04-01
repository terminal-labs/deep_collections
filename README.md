## DeepCollection

[![PyPI version](https://badge.fury.io/py/deep-collection.svg)](https://pypi.org/project/deep-collection/)
<a href="https://github.com/ambv/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

deep_collection is a Python library that provides tooling for easy access to deep collections (dicts, lists, deques, etc), while maintaining a great portion of the collection's original API. The class DeepCollection class will automatically subclass the original collection that is provided, and add several quality of life extensions to make using deep collections much more enjoyable.

Got a bundle of JSON from an API? A large Python object from some data science problem? Some very lengthy set of instructions from some infrastructure as code like Ansible or SaltStack? Explore and modify it with ease.

DeepCollection can take virtually any kind of object including all built-in iterables, everything in the collections module, and [dotty-dicts](https://github.com/pawelzny/dotty_dict), and all of these nested in any fashion.

### Features

- Path traversal by supplying an list of path components as a key. This works for getting, setting, and deleting.
- Setting paths when parent parts do not exist.
- Path traversal through dict-like collections by dot chaining for getting
- Finding all paths to fields
- Finding all values for fields, and deduping them.
- Provide all of the above through a class that is:
    - easily instantiable
    - a native subclass of the type it was instantiated with
    - easily subclassable
