import jmespath

from deep_collection import DeepCollection


def test_instantiation():
    dc = DeepCollection({"nested": {"thing": "spam"}})
    assert jmespath.search("nested.thing", dc) == "spam"
