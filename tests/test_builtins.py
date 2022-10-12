from tests.conftest import MappingTests
from tests.conftest import MutableSequenceTests
from tests.conftest import SequenceTests


class TestList(MutableSequenceTests):
    _type = list


class TestTuple(SequenceTests):
    _type = tuple


class TestDict(MappingTests):
    _type = dict
