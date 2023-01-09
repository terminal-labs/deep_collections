import inspect
from itertools import chain

import pytest

from .parameters import getitem_dict_tests
from .parameters import getitem_tests
from deep_collections import getitem_by_path
from deep_collections import paths_to_key
from deep_collections import paths_to_value


@pytest.mark.parametrize(*getitem_tests)
def test_get_by_path(obj, path, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            getitem_by_path(obj, path)
    else:
        assert getitem_by_path(obj, path) == result


@pytest.mark.parametrize(
    "obj, key, result",
    [
        ({"a": 0}, None, []),
        ({"a": 0}, "", []),
        ({"a": 0}, "b", []),
        ({"a": 0}, "a", [["a"]]),
        ({"a": 0}, ["a"], [["a"]]),
        ({"a": [0]}, ["a"], [["a"]]),
        ({"a": {"b": 0}}, "b", [["a", "b"]]),
        ({"a": {"b": 0}}, ["a", "b"], [["a", "b"]]),
        ({"a": {"b": 0}}, {"b": 1}, [["a", "b"]]),
        ({"a": {"b": 0}, "c": {"b": 1}}, "b", [["a", "b"], ["c", "b"]]),
        ({"a": {"b": 0}, "c": {"d": {"b": 1}}}, "b", [["a", "b"], ["c", "d", "b"]]),
        ({"xa": {"b": 0}}, ["?a", "b"], [["xa", "b"]]),
        ({"xa": {"b": 0}, "ya": {"b": 1}}, ["?a", "b"], [["xa", "b"], ["ya", "b"]]),
        ({"b": {"c": {"xd": {"e": 0}}}}, ["?d", "e"], [["b", "c", "xd", "e"]]),
        (
            {"b": {"c": {"xd": {"e": 0}, "yd": {"e": 1}}}},
            ["?d", "e"],
            [["b", "c", "xd", "e"], ["b", "c", "yd", "e"]],
        ),
        (["a"], 0, [[0]]),
        (["a"], [0], [[0]]),
        (["a"], 1, []),
        (["a", ["b", "c", "d"]], 2, [[1, 2]]),
        (["a", ["b", "c", "d"]], 0, [[0], [1, 0]]),
        (["a", ["b", "c", "d"]], [1, 0], [[1, 0]]),
    ],
)
def test_paths_to_key(obj, key, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            list(paths_to_key(obj, key))
    else:
        assert list(paths_to_key(obj, key)) == result


@pytest.mark.parametrize(
    "obj, value, result",
    [
        ({"a": 0}, None, []),
        ({"a": 0}, "", []),
        ({"a": 0}, "b", []),
        ({"a": 0}, 0, [["a"]]),
        ({"a": 0}, "0", []),
        ({"a": [0]}, [0], [["a"]]),
        ({"a": {0}}, {0}, [["a"]]),
        ({"a": {0: 1}}, {0: 1}, [["a"]]),
        ({"a": {0: 1}}, {0: 2}, []),
        ({"a": {"b": 0}}, 0, [["a", "b"]]),
        ({"a": {"b": 0}, "c": {"d": {"b": 0}}}, 0, [["a", "b"], ["c", "d", "b"]]),
    ],
)
def test_paths_to_value(obj, value, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            list(paths_to_value(obj, value))
    else:
        assert list(paths_to_value(obj, value)) == result
