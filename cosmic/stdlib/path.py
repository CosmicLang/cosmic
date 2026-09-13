"""Cosmic Standard Library — path module."""
from __future__ import annotations
import os
import glob as _glob
from typing import Any


def join(*parts: str) -> str:
    return os.path.join(*parts)


def dirname(path: str) -> str:
    return os.path.dirname(path)


def basename(path: str) -> str:
    return os.path.basename(path)


def ext(path: str) -> str:
    _, e = os.path.splitext(path)
    return e


def stem(path: str) -> str:
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    return name


def parent(path: str) -> str:
    return os.path.dirname(path)


def resolve(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def exists(path: str) -> bool:
    return os.path.exists(path)


def is_file(path: str) -> bool:
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    return os.path.isdir(path)


def is_absolute(path: str) -> bool:
    return os.path.isabs(path)


def relative(path: str, start: str = '.') -> str:
    return os.path.relpath(path, start)


def absolute(path: str) -> str:
    return os.path.abspath(path)


def mkdir_p(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def touch(path: str) -> None:
    if not os.path.exists(path):
        with open(path, 'w') as f:
            pass
    else:
        os.utime(path, None)


def read_text(path: str, encoding: str = 'utf-8') -> str:
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write_text(path: str, content: str, encoding: str = 'utf-8') -> None:
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def read_bytes(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


def write_bytes(path: str, content: bytes) -> None:
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)


def glob(pattern: str) -> list[str]:
    return _glob.glob(pattern, recursive=True)


def list_files(path: str = '.', recursive: bool = False) -> list[str]:
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
    lines = []
    entries = sorted(os.scandir(path), key=lambda e: e.name)
    entries = [e for e in entries if not e.name.startswith('.')]
    for i, entry in enumerate(entries):
        connector = '└── ' if i == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir() and (max_depth is None or max_depth > 0):
            extension = '    ' if i == len(entries) - 1 else '│   '
            sub = tree(entry.path, prefix + extension,
                       max_depth - 1 if max_depth else None)
            lines.append(sub)
    return '\n'.join(lines)


def home() -> str:
    return os.path.expanduser('~')


def cwd() -> str:
    return os.getcwd()


def temp() -> str:
    import tempfile
    return tempfile.gettempdir()


def size(path: str) -> int:
    return os.path.getsize(path)


def modified(path: str) -> float:
    return os.path.getmtime(path)


def copy(src: str, dst: str) -> None:
    import shutil
    shutil.copy2(src, dst)


def move(src: str, dst: str) -> None:
    import shutil
    shutil.move(src, dst)


def remove(path: str) -> None:
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        import shutil
        shutil.rmtree(path)


def rename(src: str, dst: str) -> None:
    os.rename(src, dst)


def split_all(path: str) -> list[str]:
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
    base, _ = os.path.splitext(path)
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    return base + new_ext


def with_name(path: str, new_name: str) -> str:
    return os.path.join(os.path.dirname(path), new_name)


def parts(path: str) -> dict[str, str]:
    drive, p = os.path.splitdrive(path)
    return {
        'drive': drive,
        'dir': os.path.dirname(p),
        'name': os.path.basename(p),
        'stem': os.path.splitext(os.path.basename(p))[0],
        'ext': os.path.splitext(p)[1],
    }
