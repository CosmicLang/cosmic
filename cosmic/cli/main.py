"""Cosmic CLI — pure command dispatcher.

Modeled after Kof4j's Main.java: zero business logic beyond routing.
Each command is a dedicated module with a static run() entry point.
"""
from __future__ import annotations
import sys
import argparse


def main(argv: list[str] | None = None) -> int:
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
        'compile': lambda a: __import__('cosmic.cli.cmd_compile', fromlist=['run']).run(a),
        'run': lambda a: __import__('cosmic.cli.cmd_run', fromlist=['run']).run(a),
        'check': lambda a: __import__('cosmic.cli.cmd_check', fromlist=['run']).run(a),
        'transpile': lambda a: __import__('cosmic.cli.cmd_transpile', fromlist=['run']).run(a),
        'bytecode': lambda a: __import__('cosmic.cli.cmd_bytecode', fromlist=['run']).run(a),
        'tokens': lambda a: __import__('cosmic.cli.cmd_tokens', fromlist=['run']).run(a),
        'ast': lambda a: __import__('cosmic.cli.cmd_ast', fromlist=['run']).run(a),
        'repl': lambda a: __import__('cosmic.cli.cmd_repl', fromlist=['run']).run(a),
        'version': lambda a: __import__('cosmic.cli.cmd_version', fromlist=['run']).run(a),
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
