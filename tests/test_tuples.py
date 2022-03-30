from deep_collection import DeepCollection
from tests.shared import immutable_sequence_tests


def test_sequence_shared():
    immutable_sequence_tests(DeepCollection((*range(10),)))
