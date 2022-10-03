from tests.conftest import BaseMapping


class TestDict(BaseMapping):
    def setup_method(self):
        self.obj = {"nested": {"thing": "spam"}, "pop": "mthd_name"}
