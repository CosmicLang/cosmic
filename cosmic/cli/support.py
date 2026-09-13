"""Shared CLI utilities — file validation, output helpers."""
from __future__ import annotations
import os
import sys


def validate_file(path: str) -> str | None:
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        return None
    return path


def read_source(path: str) -> str | None:
    validated = validate_file(path)
    if validated is None:
        return None
    with open(validated, 'r', encoding='utf-8') as f:
        return f.read()
