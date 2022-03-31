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
        ),
    ],
)
def test_getitem(obj, path, expected):
    dc = DeepCollection(obj)
    assert dc[path] == expected


def test_getattr():
    dc = DeepCollection({"nested": [{"thing": "spam"}]})
    assert dc.nested == [{"thing": "spam"}]
    assert dc.nested[0] == {"thing": "spam"}
    assert dc.nested[0].thing == "spam"

    with pytest.raises(AttributeError):
        dc.foo


def test_reinitialization():
    dc = DeepCollection({"nested": [{"thing": "spam"}]})

    assert DeepCollection(dc) == dc


def test_subclass():
    class Foo(DeepCollection):
        pass

    dc = Foo({"nested": [{"thing": "spam"}]})

    assert DeepCollection(dc) == dc
    assert isinstance(dc, Foo)
    assert isinstance(dc, DeepCollection)
    assert isinstance(dc, dict)
    assert issubclass(Foo, DeepCollection)
