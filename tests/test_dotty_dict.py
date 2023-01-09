import dotty_dict
import pytest
from dotty_dict import Dotty
from dotty_dict import dotty

from deep_collections import DeepCollection


def test_instantiation():
    dc = DeepCollection(dotty())
    assert isinstance(dc, DeepCollection)
    assert isinstance(dc, Dotty)


def test_Dotty_not_present(mocker):
    class Missing:
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError

    mocker.patch.object(dotty_dict, "Dotty", Missing)

    with pytest.raises(AttributeError):
        DeepCollection(dotty())


def test_unrelated_attrerror_still_raises():
    class Cls:
        def __init__(self, obj, *args, **kwargs):
            if obj == "raise":
                raise AttributeError

    with pytest.raises(AttributeError):
        DeepCollection(Cls("raise"))
