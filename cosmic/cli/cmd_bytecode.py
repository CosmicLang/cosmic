"""Cosmic CLI — bytecode command."""
from __future__ import annotations
import sys

from cosmic.cli.support import validate_file, read_source
from cosmic.compiler.pipeline import Compiler


def run(args) -> int:
    path = validate_file(args.file)
    if path is None:
        return 1

    try:
        source = read_source(path)
        if source is None:
            return 1
        compiler = Compiler(filename=path, check_types=False)
        result = compiler.compile_source(source)

        if result.errors:
            for err in result.errors:
                print(f"Error: {err}", file=sys.stderr)
            return 1

        if result.bytecode:
            instructions, constants = result.bytecode
            for i, instr in enumerate(instructions):
                print(f"  {i:4d}: {instr}")
        else:
            print("Error: Bytecode compilation failed", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
