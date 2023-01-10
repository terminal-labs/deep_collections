import jmespath

from deep_collections import DeepCollection


def test_search():
    dc = DeepCollection({"nested": {"thing": "spam"}})
    assert jmespath.search("nested.thing", dc) == "spam"
