"""Cosmic CLI — transpile command."""
from __future__ import annotations
import sys

from cosmic.cli.support import validate_file, read_source
from cosmic.compiler.pipeline import transpile_to_python


def run(args) -> int:
    path = validate_file(args.file)
    if path is None:
        return 1

    try:
        source = read_source(path)
        if source is None:
            return 1
        python_code = transpile_to_python(source, path)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(python_code)
            print(f"Transpiled to {args.output}")
        else:
            print(python_code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
