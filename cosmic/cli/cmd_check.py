"""Cosmic CLI — check command (testable with injectable streams)."""
from __future__ import annotations
import sys

from cosmic.cli.support import validate_file
from cosmic.compiler.pipeline import compile_file


def run(args, out=sys.stdout, err=sys.stderr) -> int:
    path = validate_file(args.file)
    if path is None:
        return 1

    result = compile_file(path)
    if result.errors:
        for error in result.errors:
            print(f"Error: {error}", file=err)
        return 1

    if result.warnings:
        for warn in result.warnings:
            print(f"Warning: {warn}", file=out)
    else:
        print("No errors found.", file=out)
    return 0
