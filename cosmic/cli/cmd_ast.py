"""Cosmic CLI — ast command."""
from __future__ import annotations
import sys

from cosmic.cli.support import validate_file, read_source
from cosmic.compiler.pipeline import compile_source


def run(args) -> int:
    path = validate_file(args.file)
    if path is None:
        return 1

    try:
        source = read_source(path)
        if source is None:
            return 1
        result = compile_source(source, path)
        if result.ast:
            from cosmic.REPL import print_ast
            print_ast(result.ast)
        else:
            print("Error: No AST generated", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
