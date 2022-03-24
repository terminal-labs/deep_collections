from dpath.util import get

from deep_collection import DeepCollection


def test_instantiation():
    dc = DeepCollection({"nested": {"thing": "spam"}})
    assert get(dc, "nested/thing") == "spam"
