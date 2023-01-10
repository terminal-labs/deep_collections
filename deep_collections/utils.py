def _stringlike(obj):
    """Return True if obj is an instance of str, bytes, or bytearray
    >>> _stringlike("a")
    True
    >>> _stringlike(b"a")
    True
    >>> _stringlike(1)
    False
    """
    return any(isinstance(obj, base) for base in (str, bytes, bytearray))


def pathlike(obj):
    """Guess if an object could be a nested collection.

    The general heuristic is that an object must be iterable, but not stringlike
    so that an element can be arbitrary, like another collection.

    Since this is a simple check, there are false positives, but this works with
    basic types.
    >>> pathlike([1])
    True
    >>> pathlike({1:2})
    True
    >>> pathlike(1)
    False
    >>> pathlike("a")
    False
    """
    if _stringlike(obj):
        return False

    try:
        iter(obj)
    except TypeError:
        return False

    return True
