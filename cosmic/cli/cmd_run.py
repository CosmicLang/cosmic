"""Cosmic CLI — run command."""
from __future__ import annotations
import sys
import time

from cosmic.cli.support import validate_file
from cosmic.compiler.pipeline import compile_file
from cosmic.backends.bytecode.compiler import CosmicVM


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

    if result.bytecode:
        try:
            instructions, constants = result.bytecode
            vm = CosmicVM()
            vm.run(instructions, constants)
        except Exception as e:
            print(f"Runtime error: {e}", file=sys.stderr)
            return 1
    elif result.python_code:
        try:
            exec(result.python_code, {'__name__': '__main__', '__file__': path})
        except Exception as e:
            print(f"Python error: {e}", file=sys.stderr)
            return 1
    else:
        print("Error: No output generated", file=sys.stderr)
        return 1

    print(f"\nExecuted in {elapsed*1000:.1f}ms")
    return 0
