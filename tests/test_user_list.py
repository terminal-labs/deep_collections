from collections import UserList

import pytest

from deep_collection import DeepCollection
from tests.shared import mutable_sequence_tests


@pytest.fixture(scope="function")
def dc_list():
    return DeepCollection(UserList([*range(10)]))


def test_getitem():
    dc = DeepCollection(UserList(["nested", UserList(["thing", "spam"])]))

    assert dc[1] == UserList(["thing", "spam"])
    assert dc[1, 1] == "spam"

    assert isinstance(dc[1], UserList)
    assert isinstance(dc[1], DeepCollection)
    assert issubclass(type(dc[1]), DeepCollection)
    assert issubclass(type(dc[1]), UserList)


def test_setitem():
    dc = DeepCollection(UserList(["nested", UserList(["thing", "spam"])]))

    dc[0] = "foo"
    assert dc == UserList(["foo", UserList(["thing", "spam"])])

    dc[1] = "bar"
    assert dc == UserList(["foo", "bar"])
    dc[1] = UserList(["baz"])
    assert dc == UserList(["foo", UserList(["baz"])])

    assert isinstance(dc[1], UserList)
    assert isinstance(dc[1], DeepCollection)
    assert issubclass(type(dc[1]), DeepCollection)
    assert issubclass(type(dc[1]), UserList)


def test_append():
    dc = DeepCollection(UserList())

    dc.append("foo")
    assert dc == UserList(["foo"])
    assert dc[0] == "foo"

    dc[0] = "bar"
    assert dc == UserList(["bar"])
    assert dc[0] == "bar"


def test_clear():
    dc = DeepCollection(UserList(["foo"]))
    dc.clear()
    assert dc == []


def test_sequence_shared(dc_list):
    mutable_sequence_tests(dc_list)


def test_mul(dc_list):
    assert dc_list * 2 == UserList([*range(10)]) * 2


def test_slicing(dc_list):
    assert dc_list[2:8] == UserList([2, 3, 4, 5, 6, 7])
    assert dc_list[2:8:2] == UserList([2, 4, 6])
