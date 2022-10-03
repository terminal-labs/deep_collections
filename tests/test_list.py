from tests.conftest import BaseSequence


class TestList(BaseSequence):
    def setup_method(self):
        self.obj = ["nested", ["thing", "spam"]]
