"""Cosmic CLI — tokens command."""
from __future__ import annotations
import sys

from cosmic.cli.support import validate_file, read_source
from cosmic.lexer.lexer import tokenize


def run(args) -> int:
    path = validate_file(args.file)
    if path is None:
        return 1

    try:
        source = read_source(path)
        if source is None:
            return 1
        tokens = tokenize(source, path)
        for tok in tokens:
            print(f"  {tok.type.name:20s} {tok.value!r:30s} L{tok.line}:{tok.column}")
        print(f"\n  Total: {len(tokens)} tokens")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
