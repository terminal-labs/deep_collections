from dotty_dict import Dotty
from dotty_dict import dotty

from deep_collection import DeepCollection


def test_instantiation():
    dc = DeepCollection(dotty())
    assert isinstance(dc, DeepCollection)
    assert isinstance(dc, Dotty)
