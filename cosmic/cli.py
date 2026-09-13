"""Cosmic CLI — command-line interface."""
from __future__ import annotations
import sys
import os
import argparse
import time

from cosmic.compiler.pipeline import Compiler, compile_file, compile_source, transpile_to_python
from cosmic.lexer.lexer import tokenize
from cosmic.backends.bytecode.compiler import CosmicVM


def cmd_compile(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
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


def cmd_run(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
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


def cmd_check(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    result = compile_file(path)
    if result.errors:
        for err in result.errors:
            print(f"Error: {err}", file=sys.stderr)
        return 1

    if result.warnings:
        for warn in result.warnings:
            print(f"Warning: {warn}")
    else:
        print("No errors found.")
    return 0


def cmd_transpile(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with open(path, 'r') as f:
            source = f.read()
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


def cmd_bytecode(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with open(path, 'r') as f:
            source = f.read()
        compiler = Compiler(filename=path, check_types=False)
        result = compiler.compile_source(source)

        if result.errors:
            for err in result.errors:
                print(f"Error: {err}", file=sys.stderr)
            return 1

        if result.bytecode:
            for i, instr in enumerate(result.bytecode):
                print(f"  {i:4d}: {instr}")
        else:
            print("Error: Bytecode compilation failed", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_tokens(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with open(path, 'r') as f:
            source = f.read()
        tokens = tokenize(source, path)
        for tok in tokens:
            print(f"  {tok.type.name:20s} {tok.value!r:30s} L{tok.line}:{tok.column}")
        print(f"\n  Total: {len(tokens)} tokens")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_ast(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with open(path, 'r') as f:
            source = f.read()
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


def cmd_repl(args):
    from cosmic.REPL import main
    main()
    return 0


def cmd_version(args):
    print("Cosmic Language v0.1.0")
    return 0


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog='cosmic',
        description='Cosmic Language — A modern, powerful language',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cosmic run main.cos           Run a Cosmic file
  cosmic compile main.cos      Compile to Python
  cosmic transpile main.cos    Transpile to Python
  cosmic check main.cos        Type-check a file
  cosmic tokens main.cos       Show tokens
  cosmic ast main.cos          Show AST
  cosmic bytecode main.cos     Show bytecode
  cosmic repl                  Start interactive REPL
  cosmic version               Show version
"""
    )

    sub = parser.add_subparsers(dest='command', help='Available commands')

    p_compile = sub.add_parser('compile', help='Compile a .cos file to Python')
    p_compile.add_argument('file', help='Source file to compile')
    p_compile.add_argument('-o', '--output', help='Output file')

    p_run = sub.add_parser('run', help='Run a .cos file')
    p_run.add_argument('file', help='Source file to run')

    p_check = sub.add_parser('check', help='Type-check a .cos file')
    p_check.add_argument('file', help='Source file to check')

    p_transpile = sub.add_parser('transpile', help='Transpile to Python')
    p_transpile.add_argument('file', help='Source file to transpile')
    p_transpile.add_argument('-o', '--output', help='Output file')

    p_bytecode = sub.add_parser('bytecode', help='Show bytecode for a .cos file')
    p_bytecode.add_argument('file', help='Source file')

    p_tokens = sub.add_parser('tokens', help='Show tokens for a .cos file')
    p_tokens.add_argument('file', help='Source file')

    p_ast = sub.add_parser('ast', help='Show AST for a .cos file')
    p_ast.add_argument('file', help='Source file')

    sub.add_parser('repl', help='Start interactive REPL')
    sub.add_parser('version', help='Show version')

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        'compile': cmd_compile,
        'run': cmd_run,
        'check': cmd_check,
        'transpile': cmd_transpile,
        'bytecode': cmd_bytecode,
        'tokens': cmd_tokens,
        'ast': cmd_ast,
        'repl': cmd_repl,
        'version': cmd_version,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
