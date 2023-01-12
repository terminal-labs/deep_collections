import re
from abc import ABC
from abc import abstractmethod
from fnmatch import fnmatchcase

from .utils import _stringlike


def match_style(style):
    """Return a match style class by lookup. If a"""
    style_map = {
        "equality": EqualityMatch,
        "glob": GlobMatch,
        "glob+regex": GlobOrRegexMatch,
        "hash": HashMatch,
        "regex": RegexMatch,
    }

    style_class = style_map.get(style, style)

    if issubclass(style_class, BaseMatch):
        return style_class
    else:
        raise ValueError(f"Style given is not a listed match class, or a subclass of BaseMatch: {style}")


def safe_match(func, key, pattern):
    try:
        return func(key, pattern)
    except TypeError:  # e.g. pattern could be an int - not a match
        False


class BaseMatch(ABC):
    @staticmethod
    @abstractmethod
    def patterned(txt, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def match(*args, **kwargs):
        raise NotImplementedError


class HashMatch(BaseMatch):
    @staticmethod
    def patterned(txt, *args, **kwargs):
        return True

    @classmethod
    def match(cls, key, pattern, *args, **kwargs):
        return hash(key) == hash(pattern)


class EqualityMatch(BaseMatch):
    @staticmethod
    def patterned(txt, *args, **kwargs):
        return True

    @classmethod
    def match(cls, key, pattern, *args, **kwargs):
        return key == pattern


class GlobMatch(EqualityMatch):
    @staticmethod
    def patterned(txt, *args, **kwargs):
        if kwargs.get("case_sensitive") is False:
            return True
        return _stringlike(txt) and any(char in txt for char in "*?[")

    @classmethod
    def match(cls, key, pattern, *args, case_sensitive=True, **kwargs):
        if super().match(key, pattern, *args, **kwargs):
            return True

        if cls.patterned(pattern):  # Make matching work on indices and numeric keys
            if case_sensitive:
                return safe_match(fnmatchcase, str(key), pattern)
            return safe_match(fnmatchcase, str(key).lower(), pattern.lower())

        if case_sensitive:
            return safe_match(fnmatchcase, key, pattern)
        return safe_match(fnmatchcase, key.lower(), pattern.lower())


class RegexMatch(EqualityMatch):
    @staticmethod
    def patterned(txt, *args, **kwargs):
        return _stringlike(txt) and any(char in txt for char in r".^$*+?{}[]\|()")

    @classmethod
    def match(cls, key, pattern, *args, **kwargs):
        def re_match(key, pattern, **kwargs):
            try:
                if re.compile(pattern).match(key, *args, **kwargs):
                    return True
                return False
            except re.error as e:
                e.args += (f"Path element is not valid Regular Expression: '{pattern}'",)
                raise  # e(

        if super().match(key, pattern, *args, **kwargs):
            return True

        if cls.patterned(pattern):  # Make matching work on indices and numeric keys
            return safe_match(re_match, str(key), pattern)
        return safe_match(re_match, key, pattern)

        return False


class GlobOrRegexMatch(RegexMatch):
    @classmethod
    def match(cls, key, pattern, *args, **kwargs):
        return GlobMatch.match(key, pattern, *args, **kwargs) or RegexMatch.match(key, pattern, *args, **kwargs)
