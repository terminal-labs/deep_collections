from deep_collection import DeepCollection


def test_composition():
    dc = DeepCollection([1])
    assert dc._obj == [1]
    assert type(dc._obj) == list
    dc.append(2)  # list method that mutates self
    assert dc._obj == [1, 2]


def test_reinitialization():
    dc = DeepCollection({"nested": [{"thing": "spam"}]})
    new_dc = DeepCollection(dc)
    assert new_dc == dc
    assert type(new_dc._obj) == dict


def test_subclass():
    class Foo(DeepCollection):
        pass

    dc = Foo({"nested": [{"thing": "spam"}]})

    assert DeepCollection(dc) == dc
    assert isinstance(dc, Foo)
    assert isinstance(dc, DeepCollection)
    assert isinstance(dc, dict)
    assert issubclass(Foo, DeepCollection)
