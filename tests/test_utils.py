import inspect
import re
from itertools import chain

import pytest

from .parameters import getitem_dict_tests
from .parameters import getitem_tests
from deep_collections import getitem_by_path
from deep_collections import paths_to_key
from deep_collections import paths_to_value


@pytest.mark.parametrize(*getitem_tests)
def test_getitem_by_path(obj, path, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            getitem_by_path(obj, path)
    else:
        assert getitem_by_path(obj, path) == result


# Needed for next hash match test
class FunkyInt(int):
    def __hash__(self):
        return -self


fun_five = FunkyInt(5)

# Basic tests of various match styles
@pytest.mark.parametrize(
    "obj, path, match_with, kwargs, result",
    [
        ({5: 1}, -5, "hash", {}, []),
        ({fun_five: 1}, -5, "hash", {}, 1),
        ({"foo!": 1}, "foo!", "equality", {}, 1),
        ({1: 1}, 0, "equality", {}, []),
        ({"accccb": 1}, "a[bcd]*b", "regex", {}, 1),
        ({"xd": 1}, "xd", "regex", {}, 1),
        ({"xd": 1}, "?d", "regex", {}, re.error),
        ({"xd": 1}, "?d", None, {}, 1),
        ({"xd": 1}, "?d", None, {}, 1),
        ({"xd": 1}, "Xd", None, {"case_sensitive": False}, 1),
        (
            {"b": {"accccb": {"xd": {"e": 0}}}},
            ["**", "a[bcd]*b", "?d", "e"],
            "glob+regex",
            {},
            0,
        ),
    ],
)
def test_getitem_by_path_styles(obj, path, match_with, kwargs, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            if match_with:
                getitem_by_path(obj, path, match_with, **kwargs)
            else:
                getitem_by_path(obj, path, **kwargs)
    else:
        if match_with:
            assert getitem_by_path(obj, path, match_with, **kwargs) == result
        else:
            assert getitem_by_path(obj, path, **kwargs) == result


@pytest.mark.parametrize(
    "obj, key, result",
    [
        ("a", "a", TypeError),
        (1, 1, TypeError),
        ({1: None}, 1, [[1]]),
        ({None: 1}, None, [[None]]),
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
        ("a", "a", TypeError),
        (1, 1, TypeError),
        ({1: None}, None, [[1]]),
        ({None: 1}, 1, [[None]]),
        ({"a": 0}, None, []),
        ({"a": 0}, "", []),
        ({"a": 0}, "b", []),
        ({"a": 0}, 0, [["a"]]),
        ({"a": 0}, "0", []),
        (["a", ["value", "x"]], "x", [[1, 1]]),
        ([["value", "x"]], ["value", "x"], [[0]]),
        ({"a": ["value", "x"]}, ["value", "x"], [["a"]]),
        ({"a": [0]}, [0], [["a"]]),
        ({"a": {0}}, {0}, [["a"]]),
        ({"a": {0: 1}}, {0: 1}, [["a"]]),
        ({"a": {0: 1}}, {0: 2}, []),
        ({"a": {"b": 0}}, 0, [["a", "b"]]),
        ({"a": {"b": 0}, "c": {"d": {"b": 0}}}, 0, [["a", "b"], ["c", "d", "b"]]),
        ({"a": {"b": 0}, "c": {"d": {"b": 0}}}, {"b": 0}, [["a"], ["c", "d"]]),
    ],
)
def test_paths_to_value(obj, value, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            list(paths_to_value(obj, value))
    else:
        assert list(paths_to_value(obj, value)) == result


@pytest.mark.parametrize(
    "obj, key, match_with, result",
    [
        ({5: 1}, -5, "hash", []),
        ({fun_five: 1}, -5, "hash", [[fun_five]]),
        ({"foo!": 1}, "foo!", "equality", [["foo!"]]),
        ({1: 1}, 0, "equality", []),
        (
            {"b": {"accccb": {"xd": {"e": 0}}}},
            ["a[bcd]*b", "xd", "e"],
            "regex",
            [["b", "accccb", "xd", "e"]],
        ),
        (
            {"b": {"accccb": {"xd": {"e": 0}}}},
            ["a[bcd]*b", "?d", "e"],
            "glob+regex",
            [["b", "accccb", "xd", "e"]],
        ),
    ],
)
def test_paths_to_key_match_withs(obj, key, match_with, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            list(paths_to_key(obj, key, match_with))
    else:
        assert list(paths_to_key(obj, key, match_with)) == result


@pytest.mark.parametrize(
    "obj, value, match_with, result",
    [
        (
            {"a": {"b": 0}, "c": {"d": {"b": "0"}}},
            "^0",
            "regex",
            [["a", "b"], ["c", "d", "b"]],
        ),
    ],
)
def test_paths_to_value_match_withs(obj, value, match_with, result):
    if inspect.isclass(result) and issubclass(result, Exception):
        with pytest.raises(result):
            list(paths_to_value(obj, value, match_with))
    else:
        assert list(paths_to_value(obj, value, match_with)) == result
