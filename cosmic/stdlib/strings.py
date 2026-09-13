"""String manipulation, transformation, and pattern matching utilities for the Cosmic Standard Library."""
from __future__ import annotations
import re
import unicodedata
from typing import Any


def escape(s: str) -> str:
    """Escape special characters in a string."""
    return s.encode('unicode_escape').decode('ascii')


def unescape(s: str) -> str:
    """Unescape special characters in a string."""
    return s.encode().decode('unicode_escape')


def contains(s: str, substr: str) -> bool:
    """Check if s contains substr."""
    return substr in s


def starts_with(s: str, prefix: str) -> bool:
    """Check if s starts with prefix."""
    return s.startswith(prefix)


def ends_with(s: str, suffix: str) -> bool:
    """Check if s ends with suffix."""
    return s.endswith(suffix)


def split(s: str, sep: str | None = None, maxsplit: int = -1) -> list[str]:
    """Split s by separator."""
    return s.split(sep, maxsplit)


def join(sep: str, parts: list[str]) -> str:
    """Join parts with separator."""
    return sep.join(parts)


def replace(s: str, old: str, new: str, count: int = -1) -> str:
    """Replace occurrences of old with new."""
    return s.replace(old, new, count)


def trim(s: str) -> str:
    """Strip leading and trailing whitespace."""
    return s.strip()


def trim_start(s: str) -> str:
    """Strip leading whitespace."""
    return s.lstrip()


def trim_end(s: str) -> str:
    """Strip trailing whitespace."""
    return s.rstrip()


def upper(s: str) -> str:
    """Convert string to uppercase."""
    return s.upper()


def lower(s: str) -> str:
    """Convert string to lowercase."""
    return s.lower()


def title(s: str) -> str:
    """Convert string to title case."""
    return s.title()


def capitalize(s: str) -> str:
    """Capitalize the first letter of the string."""
    return s.capitalize()


def snake_to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def camel_to_snake(s: str) -> str:
    """Convert camelCase to snake_case."""
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', result)
    return result.lower()


def pad(s: str, width: int, fillchar: str = ' ') -> str:
    """Center the string within the given width."""
    return s.center(width, fillchar) if len(s) < width else s


def pad_left(s: str, width: int, fillchar: str = ' ') -> str:
    """Pad the string on the left side."""
    return s.rjust(width, fillchar)


def pad_right(s: str, width: int, fillchar: str = ' ') -> str:
    """Pad the string on the right side."""
    return s.ljust(width, fillchar)


def repeat(s: str, count: int) -> str:
    """Repeat the string count times."""
    return s * count


def reverse(s: str) -> str:
    """Return the string reversed."""
    return s[::-1]


def is_empty(s: str) -> bool:
    """Check if the string is empty."""
    return len(s) == 0


def to_bytes(s: str, encoding: str = 'utf-8') -> bytes:
    """Encode string to bytes."""
    return s.encode(encoding)


def from_bytes(b: bytes, encoding: str = 'utf-8') -> str:
    """Decode bytes to string."""
    return b.decode(encoding)


def format_(s: str, *args: Any, **kwargs: Any) -> str:
    """Format the string with positional and keyword arguments."""
    return s.format(*args, **kwargs)


def interpolate(template: str, values: dict[str, Any]) -> str:
    """Replace ${key} placeholders with values from the dict."""
    result = template
    for key, value in values.items():
        result = result.replace(f"${{{key}}}", str(value))
    return result


def regex_match(pattern: str, s: str) -> re.Match | None:
    """Match a regex pattern at the start of the string."""
    return re.match(pattern, s)


def regex_replace(pattern: str, s: str, replacement: str) -> str:
    """Replace regex matches with replacement string."""
    return re.sub(pattern, replacement, s)


def regex_findall(pattern: str, s: str) -> list[str]:
    """Return all regex matches in the string."""
    return re.findall(pattern, s)


def levenshtein(s1: str, s2: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def diff(s1: str, s2: str) -> list[tuple[str, str]]:
    """Return unified diff between two strings."""
    import difflib
    differ = difflib.unified_diff(s1.splitlines(), s2.splitlines(), lineterm='')
    return [(line[:1], line[1:]) for line in differ if line.startswith(('+', '-'))]


def is_palindrome(s: str) -> bool:
    """Check if the string reads the same forwards and backwards (alphanumeric only)."""
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]


def word_count(s: str) -> int:
    """Return the number of words in the string."""
    return len(s.split())


def char_count(s: str, char: str) -> int:
    """Count occurrences of char in s."""
    return s.count(char)


def truncate(s: str, max_len: int, suffix: str = '...') -> str:
    """Truncate the string to max_len characters, appending suffix if truncated."""
    if len(s) <= max_len:
        return s
    return s[:max_len - len(suffix)] + suffix


def wrap(s: str, width: int) -> str:
    """Wrap text to the given width using textwrap."""
    import textwrap
    return textwrap.fill(s, width)


def is_alpha(s: str) -> bool:
    """Check if all characters are alphabetic."""
    return s.isalpha()


def is_alphanumeric(s: str) -> bool:
    """Check if all characters are alphanumeric."""
    return s.isalnum()


def is_numeric(s: str) -> bool:
    """Check if all characters are numeric."""
    return s.isnumeric()


def is_identifier(s: str) -> bool:
    """Check if the string is a valid Python identifier."""
    return s.isidentifier()


def extract_ints(s: str) -> list[int]:
    """Extract all integers from the string."""
    return [int(x) for x in re.findall(r'-?\d+', s)]


def extract_floats(s: str) -> list[float]:
    """Extract all floating-point numbers from the string."""
    return [float(x) for x in re.findall(r'-?\d+\.?\d*', s)]


def slugify(s: str) -> str:
    """Convert a string to a URL-friendly slug."""
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s


def wrap_tags(s: str, tag: str, attrs: str = '') -> str:
    """Wrap the string in an HTML/XML tag."""
    attr_str = f' {attrs}' if attrs else ''
    return f'<{tag}{attr_str}>{s}</{tag}>'


def center(s: str, width: int, fill: str = ' ') -> str:
    """Center the string within the given width."""
    return s.center(width, fill)


def count_substring(s: str, sub: str) -> int:
    """Count overlapping occurrences of substring."""
    count = 0
    start = 0
    while True:
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + 1
    return count


def remove_prefix(s: str, prefix: str) -> str:
    """Remove the given prefix from the string if present."""
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def remove_suffix(s: str, suffix: str) -> str:
    """Remove the given suffix from the string if present."""
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def quote(s: str) -> str:
    """Wrap the string in double quotes."""
    return f'"{s}"'


def indent(s: str, spaces: int = 4) -> str:
    """Indent each line of the string by the given number of spaces."""
    prefix = ' ' * spaces
    return '\n'.join(prefix + line for line in s.splitlines())


def dedent(s: str) -> str:
    """Remove common leading whitespace from each line."""
    import textwrap
    return textwrap.dedent(s)


def normalize(s: str, form: str = 'NFC') -> str:
    """Normalize Unicode string to the given form."""
    return unicodedata.normalize(form, s)
