import pytest

from deep_collection import DeepCollection


@pytest.mark.parametrize(
    "obj, path, expected",
    [
        ([1], 0, 1),
        ([1], [0], 1),
        ((1,), [0], 1),
        ({4: "a"}, [4], "a"),
        (["x", [({"foo": "a"},)]], [1, 0, 0, "foo"], "a"),
        ([1], (0,), 1),
        (
            {"very": {"deeply": {"nested": ["thing", "spam"]}}},
            ["very", "deeply"],
            {"nested": ["thing", "spam"]},
        ),
        (
            {"very": {"deeply": {"nested": ["thing", "spam"]}}},
            ["very", "deeply", "nested", 1],
            "spam",
        ),
        (
            {"very": {"deeply": {"nested": ["thing", "spam"]}}},
            "very",
            {"deeply": {"nested": ["thing", "spam"]}},
        )
        # ([{"a": 1}], {0: [], "a": 3}, 1),
    ],
)
def test_dp_getitem(obj, path, expected):
    dc = DeepCollection(obj)
    assert dc[path] == expected
