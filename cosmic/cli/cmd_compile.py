"""Cosmic CLI — compile command."""
from __future__ import annotations
import sys
import time

from cosmic.cli.support import validate_file
from cosmic.compiler.pipeline import compile_file


def run(args) -> int:
    path = validate_file(args.file)
    if path is None:
        return 1

    start = time.time()
    result = compile_file(path)
    elapsed = time.time() - start

    if result.errors:
        for err in result.errors:
            print(f"Error: {err}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, 'w') as f:
            f.write(result.python_code)
        print(f"Compiled to {args.output}")
    else:
        print(result.python_code)

    print(f"\nCompiled in {elapsed*1000:.1f}ms")
    return 0
