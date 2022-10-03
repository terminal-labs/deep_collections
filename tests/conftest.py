from abc import ABC
from abc import abstractmethod

import pytest

from deep_collection import DeepCollection


class Base(ABC):
    """Probide a scaffolding so we only have to specify the base object in
    the actual test classes.
    """

    @pytest.fixture()
    def dc(self):
        yield DeepCollection(self.obj)

    @abstractmethod
    def setup_method(self):
        """Set self.obj to an instance of the object type used to initialize the dc in
        the test. I.e., to test lists,

        self.obj = [...]
        """
        return NotImplemented

    @property
    def original_type(self):
        return type(self.obj)


class BaseSequence(Base):
    """Try to remove any explicit references to lists except in the setup_method
    so that this is reusable for list-like objects.
    """

    def test_getitem(self, dc):
        assert dc[0] == "nested"
        assert dc[1, 1] == "spam"

        assert isinstance(dc[1], self.original_type)
        assert isinstance(dc[1], DeepCollection)

    def test_setitem(self, dc):
        dc[0] = "foo"
        assert dc[0] == "foo"

        dc[1, 0] = "bar"
        assert dc[1, 0] == "bar"

        dc[1] = self.original_type(["baz"])
        dc[1, 0] = "bar"
        assert dc[0] == "foo"
        assert dc[1, 0] == "bar"

        assert isinstance(dc[1], self.original_type)
        assert isinstance(dc[1], DeepCollection)

    def test_append(self, dc):
        dc.append("foo")
        assert dc == ["nested", ["thing", "spam"], "foo"]


class BaseMapping(Base):
    @abstractmethod
    def setup_method(self):
        return NotImplemented

    def test_getitem(self, dc):
        assert dc["nested"] == {"thing": "spam"}
        assert dc["nested", "thing"] == "spam"

        assert isinstance(dc["nested"], dict)
        assert isinstance(dc["nested"], DeepCollection)

    def test_get(self, dc):
        assert dc.get("nested") == {"thing": "spam"}
        assert dc.get(["nested", "thing"]) == "spam"
        # arg 2 is a default val when it exists
        assert dc.get("foo", "bar") == "bar"
        assert dc.get("foo", default="bar") == "bar"

        # arg 2 is the 2nd element of the tuple of keys when it does exist
        assert dc.get("nested", "thing") == {"thing": "spam"}
        assert dc.get("nested", default="thing") == {"thing": "spam"}

        assert dc.get("nested", "foo") == {"thing": "spam"}
        assert dc.get(["nested", "foo"]) is None
        assert dc.get(["nested", "foo"], "bar") == "bar"

        assert isinstance(dc.get("nested"), dict)
        assert isinstance(dc.get("nested"), DeepCollection)

    def test_getattr(self, dc):
        assert dc.nested == {"thing": "spam"}
        assert dc.nested.thing == "spam"

        assert isinstance(dc.nested, dict)
        assert isinstance(dc.nested, DeepCollection)

        with pytest.raises(AttributeError):
            dc.foo

        assert dc.pop != "mthd_name"

    def test_setitem(self, dc):
        dc["foo"] = [3]
        assert dc["foo"] == [3]
        assert dc.get("foo") == [3]
        assert "foo" in dc

        dc["foo", 0] = 5
        assert dc["foo"] == [5]

        dc["foo"] = 3
        assert dc["foo"] == 3

        with pytest.raises(TypeError):
            dc["foo", "bar"] = [3]

        dc["bar", "baz"] = 3
        assert dc["bar", "baz"] == 3
        assert "bar" in dc
        assert "baz" in dc["bar"]

    def test_delitem(self, dc):
        del dc["nested", "thing"]
        assert dc == {"nested": {}, "pop": "mthd_name"}
        del dc["nested"]
        assert dc == {"pop": "mthd_name"}
