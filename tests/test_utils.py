import pytest

from deep_collection import get_by_path


@pytest.mark.parametrize(
    "obj, path, result",
    [
        ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "a", "*", "d"], 5),
        ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "b", "*", "d"], 5),
        ({"a": {"b": {"d": 5}}, "d": 4}, ["a", "*", "d"], 5),
        ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "d"], [5, 4]),
        ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "*", "d"], [5, 4]),
        ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "*", "*", "d"], [5, 4]),
        ({"a": 1}, ["*"], {"a": 1}),
        ({"a": 1}, ["a", "*"], 1),
        ({"a": 1}, [], {"a": 1}),
        ({"a": 1}, ["a", "*"], 1),
        ({"*": 1}, ["*"], {"*": 1}),
        ({"a": {"*": {"d": 5}}}, ["*", "d"], 5),
        ({"a": {"*": {"d": 5}}, "d": 4}, ["*", "d"], [5, 4]),
        ({"a": {"*": {"*": {"d": 5}}}, "d": 4}, ["*", "d"], [5, 4]),
        ({"*": {"d": 5}}, ["*", "d"], 5),
        ({"d": [5]}, ["d"], [5]),
        ([0, [1, [2, [3]]]], [1, 1, 0], 2),
        ([0, [1, [2, [3]]]], [1, 1], [2, [3]]),
        ([0, {"a": [1, 2]}], ["*", "a"], [1, 2]),
        ([0, {"a": [1, 2, {"b": "z"}]}], ["*", "b"], "z"),
        ([0, {"a": [1, 2], 1: "y"}], ["*", 1], [1, "y"]),
        ([0, {"a": [1, 2]}], ["*", 5], []),
        ({"a": None}, ["a"], None),
        ([1], ["a"], TypeError),
        ([1], [0, "a"], TypeError),
        ([[1]], [0, "a"], TypeError),
        # ([[1]], ['*'], TypeError),  # XXX pytest registers ['*'] as [] for some reason
        ([[1]], ["*", 1], 1),
        ([[1]], ["*", 0], []),
        ({"a": "b"}, ["*", "d"], []),
    ],
)
def test_get_by_path(obj, path, result):
    if result == TypeError:
        with pytest.raises(TypeError):
            get_by_path(obj, path)
    else:
        assert get_by_path(obj, path) == result
