"""File system path manipulation and file operations for the Cosmic Standard Library."""
from __future__ import annotations
import os
import glob as _glob
from typing import Any


def join(*parts: str) -> str:
    """Join path components into a single path."""
    return os.path.join(*parts)


def dirname(path: str) -> str:
    """Return the directory name of the path."""
    return os.path.dirname(path)


def basename(path: str) -> str:
    """Return the base name of the path."""
    return os.path.basename(path)


def ext(path: str) -> str:
    """Return the file extension including the dot."""
    _, e = os.path.splitext(path)
    return e


def stem(path: str) -> str:
    """Return the filename without its extension."""
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    return name


def parent(path: str) -> str:
    """Return the parent directory of the path."""
    return os.path.dirname(path)


def resolve(path: str) -> str:
    """Resolve to an absolute path, expanding ~ and variables."""
    return os.path.abspath(os.path.expanduser(path))


def exists(path: str) -> bool:
    """Check if the path exists."""
    return os.path.exists(path)


def is_file(path: str) -> bool:
    """Check if the path is a file."""
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    """Check if the path is a directory."""
    return os.path.isdir(path)


def is_absolute(path: str) -> bool:
    """Check if the path is absolute."""
    return os.path.isabs(path)


def relative(path: str, start: str = '.') -> str:
    """Return a relative path from start to path."""
    return os.path.relpath(path, start)


def absolute(path: str) -> str:
    """Return the absolute version of the path."""
    return os.path.abspath(path)


def mkdir_p(path: str) -> None:
    """Create directories recursively, ignoring if they exist."""
    os.makedirs(path, exist_ok=True)


def touch(path: str) -> None:
    """Create the file or update its modification time."""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            pass
    else:
        os.utime(path, None)


def read_text(path: str, encoding: str = 'utf-8') -> str:
    """Read the file contents as a string."""
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write_text(path: str, content: str, encoding: str = 'utf-8') -> None:
    """Write a string to the file, creating directories as needed."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def read_bytes(path: str) -> bytes:
    """Read the file contents as bytes."""
    with open(path, 'rb') as f:
        return f.read()


def write_bytes(path: str, content: bytes) -> None:
    """Write bytes to the file, creating directories as needed."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)


def glob(pattern: str) -> list[str]:
    """Return files matching the glob pattern."""
    return _glob.glob(pattern, recursive=True)


def list_files(path: str = '.', recursive: bool = False) -> list[str]:
    """Return a sorted list of file paths in the directory."""
    result = []
    if recursive:
        for root, dirs, files in os.walk(path):
            for f in files:
                result.append(os.path.join(root, f))
    else:
        for entry in os.scandir(path):
            if entry.is_file():
                result.append(entry.path)
    return sorted(result)


def tree(path: str = '.', prefix: str = '', max_depth: int | None = None) -> str:
    """Return a directory tree as a formatted string."""
    lines = []
    entries = sorted(os.scandir(path), key=lambda e: e.name)
    entries = [e for e in entries if not e.name.startswith('.')]
    for i, entry in enumerate(entries):
        connector = '└── ' if i == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and (max_depth is None or max_depth > 0):
            extension = '    ' if i == len(entries) - 1 else '│   '
            sub = tree(entry.path, prefix + extension,
                       max_depth - 1 if max_depth is not None else None)
            lines.append(sub)
    return '\n'.join(lines)


def home() -> str:
    """Return the user's home directory."""
    return os.path.expanduser('~')


def cwd() -> str:
    """Return the current working directory."""
    return os.getcwd()


def temp() -> str:
    """Return the system temporary directory path."""
    import tempfile
    return tempfile.gettempdir()


def size(path: str) -> int:
    """Return the file size in bytes."""
    return os.path.getsize(path)


def modified(path: str) -> float:
    """Return the last modification time as a timestamp."""
    return os.path.getmtime(path)


def copy(src: str, dst: str) -> None:
    """Copy a file or directory, preserving metadata."""
    import shutil
    shutil.copy2(src, dst)


def move(src: str, dst: str) -> None:
    """Move a file or directory."""
    import shutil
    shutil.move(src, dst)


def remove(path: str) -> None:
    """Remove a file or directory tree."""
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        import shutil
        shutil.rmtree(path)


def rename(src: str, dst: str) -> None:
    """Rename a file or directory."""
    os.rename(src, dst)


def split_all(path: str) -> list[str]:
    """Split the path into all components."""
    parts = []
    while True:
        head, tail = os.path.split(path)
        if tail:
            parts.append(tail)
        elif head and head != path:
            parts.append(head)
            break
        else:
            break
        path = head
    return list(reversed(parts))


def with_ext(path: str, new_ext: str) -> str:
    """Return the path with a new extension."""
    base, _ = os.path.splitext(path)
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    return base + new_ext


def with_name(path: str, new_name: str) -> str:
    """Return the path with a new filename."""
    return os.path.join(os.path.dirname(path), new_name)


def parts(path: str) -> dict[str, str]:
    """Return a dict with drive, dir, name, stem, and ext components."""
    drive, p = os.path.splitdrive(path)
    return {
        'drive': drive,
        'dir': os.path.dirname(p),
        'name': os.path.basename(p),
        'stem': os.path.splitext(os.path.basename(p))[0],
        'ext': os.path.splitext(p)[1],
    }
