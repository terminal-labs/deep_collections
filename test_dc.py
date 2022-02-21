import pytest

from deep import deep_collection


@pytest.mark.parametrize(
    "obj, path, expected",
    [
        ([1], [0], 1),
        ((1,), [0], 1),
        ({0: 'a'}, [0], 'a'),
    ],
)
def test_dp_getitem(obj, path, expected):
    dc = deep_collection(obj)
    assert dc[path] == expected
