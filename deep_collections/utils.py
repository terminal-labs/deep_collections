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
