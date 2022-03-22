from deep_collection import DeepCollection


def test_list_getitem():
    dc = DeepCollection(["nested", ["thing", "spam"]])

    assert dc[1] == ["thing", "spam"]
    assert dc[1, 1] == "spam"

    assert isinstance(dc[1], list)
    assert isinstance(dc[1], DeepCollection)
