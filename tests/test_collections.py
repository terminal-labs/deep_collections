from collections import Counter
from collections import deque
from collections import UserDict
from collections import UserList

import pytest

from tests.conftest import MappingTests
from tests.conftest import MutableSequenceTests


class TestUserList(MutableSequenceTests):
    _type = UserList


class TestUserDict(MappingTests):
    _type = UserDict


class TestDeque(MutableSequenceTests):
    _type = deque

    @pytest.mark.skip("N/A")
    def test_pop_arg(self):
        pass

    @pytest.mark.skip("N/A")
    def test_slice(self):
        pass

    @pytest.mark.skip("N/A")
    def test_sort(self):
        pass


# class TestCounter(MappingTests):
#     _type = Counter
