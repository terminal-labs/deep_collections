from abc import ABC
from abc import abstractmethod
from copy import deepcopy

import pytest

from deep_collection import DeepCollection


class BaseTests(ABC):
    """Probide a scaffolding so we only have to specify the base object in
    the actual test classes.

    Include common tests for all types.
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

    def test_iter(self, dc):
        assert list(iter(self.obj)) == list(iter(dc))

    def test_composition(self, dc):
        assert dc._obj == self.obj
        assert type(dc._obj) == type(self.obj)  # noqa: E721

    def test_reinitialization(self, dc):
        """Can we make a DC from a DC?"""
        new_dc = DeepCollection(dc)
        assert new_dc == dc
        assert type(new_dc._obj) == type(self.obj)  # noqa: E721

    def test_subclass(self):
        class Foo(DeepCollection):
            pass

        dc = Foo(self.obj)

        assert DeepCollection(dc) == dc
        assert isinstance(dc, Foo)
        assert isinstance(dc, DeepCollection)
        assert isinstance(dc, type(self.obj))
        assert issubclass(Foo, DeepCollection)


class MutableTests(BaseTests):
    def test_clear(self, dc):
        dc.clear()
        assert dc == self._type()

    def test_copy(self, dc):
        dc_new = dc.copy()
        assert self.obj == dc == dc_new

    def test_pop_arg(self):
        dc = DeepCollection(deepcopy(self.obj))
        dc.pop(1)
        self.obj.pop(1)
        assert dc == self.obj


class SequenceTests(BaseTests):
    """Test all common methods on sequences. i methods and r methods are just included
    in the normal test method. I.e. imul and rmul tests are in test_mul.

    Try to remove any explicit references to lists except in the setup_method
    so that this is reusable for list-like objects.
    """

    def setup_method(self):
        self.obj = self._type(["nested", self._type(["thing", "spam"])])

    def test_getitem(self, dc):
        assert dc[0] == "nested"
        assert dc[1, 1] == "spam"

        assert isinstance(dc[1], self._type)
        assert isinstance(dc[1], DeepCollection)

    def test_mul(self, dc):
        assert dc * 2 == self.obj * 2
        assert 2 * dc == 2 * self.obj

        dc *= 2
        assert dc == self.obj * 2

    def test_add(self, dc):
        x = self._type([1, 2])
        assert dc + x == self.obj + x
        assert x + dc == x + self.obj

        dc += x
        assert dc == self.obj + x

    def test_slice(self):
        dc = DeepCollection(self._type([*range(10)]))
        assert dc[2:8] == self._type([2, 3, 4, 5, 6, 7])
        assert dc[2:8:2] == self._type([2, 4, 6])

    def test_contains(self, dc):
        assert self.obj[1] in dc

    def test_count(self, dc):
        assert dc.count("nested") == 1

    def test_index(self, dc):
        assert dc.index("nested") == 0

        dc = self._type([1, 2, 3, 4, 1, 1, 1, 4, 5])
        assert dc.index(4, 4, 8) == 7


class MutableSequenceTests(SequenceTests, MutableTests):
    def test_delitem(self):
        dc = DeepCollection(deepcopy(self.obj))
        del dc[0]
        del self.obj[0]

        assert dc == self.obj

    def test_setitem(self, dc):
        dc[0] = "foo"
        assert dc[0] == "foo"

        dc[1, 0] = "bar"
        assert dc[1, 0] == "bar"

        dc[1] = self._type(["baz"])
        dc[1, 0] = "bar"
        assert dc[0] == "foo"
        assert dc[1, 0] == "bar"

        assert isinstance(dc[1], self._type)
        assert isinstance(dc[1], DeepCollection)

    def test_append(self, dc):
        dc.append("foo")
        self.obj.append("foo")
        assert dc == self.obj
        assert dc._obj == self.obj  # test composition stays in sync on mutation

    def test_extend(self, dc):
        dc.extend(self._type([1, 2]))
        self.obj.extend([1, 2])
        assert dc == self.obj

    def test_insert(self, dc):
        dc.insert(1, 5)
        self.obj.insert(1, 5)
        assert dc == self.obj

    def test_pop_no_arg(self):
        dc = DeepCollection(deepcopy(self.obj))
        dc.pop()
        self.obj.pop()
        assert dc == self.obj

    def test_remove(self, dc):
        dc.remove("nested")
        self.obj.remove("nested")
        assert dc == self.obj

    def test_reverse(self, dc):
        dc.reverse()
        self.obj.reverse()
        assert dc == self.obj

    def test_sort(self):
        x = self._type([1, 5, 3, 6])
        dc = DeepCollection(x)
        dc.sort()
        x.sort()
        assert dc == x


class MappingTests(MutableTests):
    def setup_method(self):
        self.obj = self._type(
            {
                "nested": self._type({"thing": "spam"}),
                "pop": "mthd_name",
                1: "integer",
            }
        )

    def test_getitem(self, dc):
        assert dc["nested"] == self.obj["nested"]
        assert dc["nested", "thing"] == self.obj["nested"]["thing"]

        assert isinstance(dc["nested"], type(self.obj))
        assert isinstance(dc["nested"], DeepCollection)

    def test_getitem_glob(self):
        dc = DeepCollection({"a": {"b": {"d": 5}}, "d": 4})
        assert dc["*", "d"] == [5, 4]

        assert isinstance(dc["*", "d"], list)
        assert isinstance(dc["*", "d"], DeepCollection)

    def test_get(self, dc):
        assert dc.get("nested") == self.obj["nested"]
        assert dc.get(["nested", "thing"]) == "spam"
        # arg 2 is a default val when it exists
        assert dc.get("foo", "bar") == "bar"
        assert dc.get("foo", default="bar") == "bar"

        # arg 2 is the 2nd element of the tuple of keys when it does exist
        assert dc.get("nested", "thing") == self.obj["nested"]
        assert dc.get("nested", default="thing") == self.obj["nested"]

        assert dc.get("nested", "foo") == self.obj["nested"]
        assert dc.get(["nested", "foo"]) is None
        assert dc.get(["nested", "foo"], "bar") == "bar"

        assert isinstance(dc.get("nested"), type(self.obj))
        assert isinstance(dc.get("nested"), DeepCollection)

    def test_getattr(self, dc):
        assert dc.nested == self.obj["nested"]
        assert dc.nested.thing == "spam"

        assert isinstance(dc.nested, type(self.obj))
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
        dc = DeepCollection(deepcopy(self.obj))
        del dc["nested", "thing"]
        del self.obj["nested"]["thing"]
        assert dc == self.obj

        del dc["nested"]
        del self.obj["nested"]
        assert dc == self.obj
