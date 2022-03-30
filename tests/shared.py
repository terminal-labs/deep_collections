import pytest


def immutable_sequence_tests(dc):
    assert 4 in dc
    assert 12 not in dc

    assert dc[3] == 3
    assert min(dc) == 0
    assert max(dc) == 9

    dc = dc * 3
    assert dc.index(4) == 4
    assert dc.index(4, 5) == 14

    with pytest.raises(ValueError):
        dc.index(4, 5, 8)

    assert dc.count(4) == 3


def mutable_sequence_tests(dc):
    immutable_sequence_tests(dc)

    assert [-1] + dc + [10]
