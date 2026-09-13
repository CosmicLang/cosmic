"""Cosmic Standard Library — regex module."""
from __future__ import annotations
import re
from typing import Any, Iterator


class Pattern:
    def __init__(self, pattern: str, flags: int = 0):
        self._pattern = re.compile(pattern, flags)
        self.pattern_str = pattern

    def match(self, string: str, pos: int = 0) -> re.Match | None:
        return self._pattern.match(string, pos)

    def search(self, string: str, pos: int = 0) -> re.Match | None:
        return self._pattern.search(string, pos)

    def findall(self, string: str) -> list[str]:
        return self._pattern.findall(string)

    def finditer(self, string: str) -> Iterator[re.Match]:
        return self._pattern.finditer(string)

    def sub(self, replacement: str, string: str, count: int = 0) -> str:
        return self._pattern.sub(replacement, string, count)

    def split(self, string: str, maxsplit: int = 0) -> list[str]:
        return self._pattern.split(string, maxsplit)

    def fullmatch(self, string: str) -> re.Match | None:
        return self._pattern.fullmatch(string)

    def __repr__(self) -> str:
        return f"Pattern({self.pattern_str!r})"


def compile(pattern: str, flags: int = 0) -> Pattern:
    return Pattern(pattern, flags)


def match(pattern: str, string: str, flags: int = 0) -> re.Match | None:
    return re.match(pattern, string, flags)


def search(pattern: str, string: str, flags: int = 0) -> re.Match | None:
    return re.search(pattern, string, flags)


def findall(pattern: str, string: str, flags: int = 0) -> list[str]:
    return re.findall(pattern, string, flags)


def finditer(pattern: str, string: str, flags: int = 0) -> Iterator[re.Match]:
    return re.finditer(pattern, string, flags)


def sub(pattern: str, replacement: str, string: str, count: int = 0, flags: int = 0) -> str:
    return re.sub(pattern, replacement, string, count, flags)


def subn(pattern: str, replacement: str, string: str, count: int = 0, flags: int = 0) -> tuple[str, int]:
    return re.subn(pattern, replacement, string, count, flags)


def split(pattern: str, string: str, maxsplit: int = 0, flags: int = 0) -> list[str]:
    return re.split(pattern, string, maxsplit, flags)


def fullmatch(pattern: str, string: str, flags: int = 0) -> re.Match | None:
    return re.fullmatch(pattern, string, flags)


def escape(string: str) -> str:
    return re.escape(string)


def group(match_obj: re.Match, group: int | str = 0) -> str | None:
    return match_obj.group(group)


def groups(match_obj: re.Match) -> tuple[str, ...]:
    return match_obj.groups()


def start(match_obj: re.Match) -> int:
    return match_obj.start()


def end(match_obj: re.Match) -> int:
    return match_obj.end()


def span(match_obj: re.Match) -> tuple[int, int]:
    return match_obj.span()


IGNORECASE = re.IGNORECASE
MULTILINE = re.MULTILINE
DOTALL = re.DOTALL
VERBOSE = re.VERBOSE
ASCII = re.ASCII
UNICODE = re.UNICODE
