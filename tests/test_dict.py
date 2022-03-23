import pytest

from deep_collection import DeepCollection


def test_getitem():
    dc = DeepCollection({"nested": {"thing": "spam"}})

    assert dc["nested"] == {"thing": "spam"}
    assert dc["nested", "thing"] == "spam"

    assert isinstance(dc["nested"], dict)
    assert isinstance(dc["nested"], DeepCollection)


def test_get():
    dc = DeepCollection({"nested": {"thing": "spam"}})

    assert dc.get("nested") == {"thing": "spam"}
    assert dc.get(["nested", "thing"]) == "spam"
    # arg 2 is a default val
    assert dc.get("foo", "bar") == "bar"
    assert dc.get("foo", default="bar") == "bar"

    # A gotcha! This is correct.
    assert dc.get("nested", "thing") == {"thing": "spam"}
    assert dc.get("nested", default="thing") == {"thing": "spam"}

    assert dc.get("nested", "foo") == {"thing": "spam"}
    assert dc.get(["nested", "foo"]) is None
    assert dc.get(["nested", "foo"], "bar") == "bar"

    assert isinstance(dc.get("nested"), dict)
    assert isinstance(dc.get("nested"), DeepCollection)


def test_getattr():
    dc = DeepCollection({"nested": {"thing": "spam"}, "pop": "tricky"})

    assert dc.nested == {"thing": "spam"}
    assert dc.nested.thing == "spam"

    assert isinstance(dc.nested, dict)
    assert isinstance(dc.nested, DeepCollection)

    with pytest.raises(AttributeError):
        dc.foo

    assert dc.pop != "tricky"


def test_setitem():
    dc = DeepCollection({"nested": {"thing": "spam"}, "pop": "tricky"})

    dc["foo"] = [3]
    assert dc["foo"] == [3]
    assert dc.get("foo") == [3]
    assert "foo" in dc

    dc["foo", 0] = 5
    assert dc["foo"] == [5]

    dc["foo"] = 3
    assert dc["foo"] == 3

    with pytest.raises(TypeError):
        dc["foo", "bar"] = [3]

    dc["bar", "baz"] = 3
    assert dc["bar", "baz"] == 3
    assert "bar" in dc
    assert "baz" in dc["bar"]


def test_delitem():
    dc = DeepCollection({"deeply": {"nested": {"thing": "spam"}}})

    del dc["deeply", "nested", "thing"]
    assert dc == {"deeply": {"nested": {}}}
    del dc["deeply"]
    assert dc == {}

    dc = DeepCollection({"deeply": [0, 1, {"nested": {"thing": "spam"}}]})
    del dc["deeply", 2, "nested", "thing"]
    assert dc == {"deeply": [0, 1, {"nested": {}}]}
    del dc["deeply", 1]
    assert dc == {"deeply": [0, {"nested": {}}]}
