from fnmatch import fnmatchcase

from .utils import _stringlike


def match_style(style):
    if style == "glob":
        return GlobMatch
    elif style == "re":
        return REMatch


def safe_fnmatchcase(key, pattern):
    try:
        return fnmatchcase(key, pattern)
    except TypeError:  # e.g. pattern could be an int - not a match
        False


class GlobMatch:
    @staticmethod
    def patterned(txt):
        return _stringlike(txt) and any(char in txt for char in "*?[")

    @staticmethod
    def match(key, pattern):
        if GlobMatch.patterned(pattern):
            return key == pattern or safe_fnmatchcase(str(key), pattern)
        else:
            return key == pattern or safe_fnmatchcase(key, pattern)
