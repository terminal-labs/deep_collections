import pytest

from tests.conftest import BaseSequence


class TestTuple(BaseSequence):
    def setup_method(self):
        self.obj = ("nested", ("thing", "spam"))

    @pytest.mark.skip("N/A")
    def test_setitem(self):
        pass

    @pytest.mark.skip("N/A")
    def test_append(self):
        pass
