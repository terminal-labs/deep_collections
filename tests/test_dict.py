from deep_collection import DeepCollection


def test_dict_getitem():
    dc = DeepCollection({"nested": {"thing": "spam"}})

    assert dc["nested"] == {"thing": "spam"}
    assert dc["nested", "thing"] == "spam"

    assert isinstance(dc["nested"], dict)
    assert isinstance(dc["nested"], DeepCollection)


def test_dict_get():
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
