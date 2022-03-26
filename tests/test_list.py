from deep_collection import DeepCollection


def test_getitem():
    dc = DeepCollection(["nested", ["thing", "spam"]])

    assert dc[1] == ["thing", "spam"]
    assert dc[1, 1] == "spam"

    assert isinstance(dc[1], list)
    assert isinstance(dc[1], DeepCollection)


def test_setitem():
    dc = DeepCollection(["nested", ["thing", "spam"]])

    dc[0] = "foo"
    assert dc == ["foo", ["thing", "spam"]]

    dc[1] = "bar"
    assert dc == ["foo", "bar"]
    dc[1] = ["baz"]
    assert dc == ["foo", ["baz"]]

    assert isinstance(dc[1], list)
    assert isinstance(dc[1], DeepCollection)


def test_append():
    dc = DeepCollection([])

    dc.append("foo")
    assert dc == ["foo"]
    assert dc[0] == "foo"

    dc[0] = "bar"
    assert dc == ["bar"]
    assert dc[0] == "bar"
