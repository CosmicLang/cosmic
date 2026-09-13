"""Cosmic REPL — interactive Read-Eval-Print Loop."""
from __future__ import annotations
import sys
import os

from typing import Any

from cosmic.compiler.pipeline import Compiler, CompileResult
from cosmic.lexer.lexer import tokenize, LexError
from cosmic.parser.parser import ParseError
from cosmic.types.checker import TypeCheckError
from cosmic.backends.bytecode.compiler import CosmicVM, BytecodeCompiler


class REPL:
    BANNER = """  _____ _____ _____   _____         _
 / ____/ ____|  ___| |_   _|__  ___| |_ ___ _ __
| |   | (___ | |_      | |/ _ \\/ __| __/ _ \\ '__|
| |    \\___ \\|  _|     | |  __/\\__ \\ ||  __/ |
| |____ ____) | |       |_|\\___||___/\\__\\___|_|
 \\_____|_____/|_|       Cosmic Language v0.1.0

 Type 'help' for commands, 'exit' to quit.
"""

    HELP_TEXT = """
Commands:
  :help          Show this help
  :exit / :quit  Exit the REPL
  :clear         Clear the screen
  :history       Show command history
  :ast           Show AST of last expression
  :types         Show type info of last expression
  :python        Show Python transpilation of last expression
  :bytecode      Show bytecode of last expression
  :run <file>    Run a Cosmic file
  :load <file>   Load a file into the REPL
  :reset         Reset REPL state
  :vars          Show current variables
"""

    def __init__(self):
        self.compiler = Compiler()
        self.vm = CosmicVM()
        self.history: list[str] = []
        self.last_result: CompileResult | None = None
        self.variables: dict[str, Any] = {}

    def run(self) -> None:
        print(self.BANNER)
        while True:
            try:
                line = input("cosmic> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not line:
                continue

            self.history.append(line)

            if line.startswith(':'):
                if self.handle_command(line):
                    continue
                continue

            self.eval_expression(line)

    def handle_command(self, line: str) -> bool:
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''

        if cmd in (':exit', ':quit'):
            print("Goodbye!")
            sys.exit(0)
        elif cmd == ':help':
            print(self.HELP_TEXT)
        elif cmd == ':clear':
            os.system('clear' if os.name != 'nt' else 'cls')
        elif cmd == ':history':
            for i, h in enumerate(self.history[:-1], 1):
                print(f"  {i}: {h}")
        elif cmd == ':ast' and self.last_result and self.last_result.ast:
            try:
                print_ast(self.last_result.ast)
            except Exception:
                print(str(self.last_result.ast))
        elif cmd == ':types' and self.last_result and self.last_result.type_map:
            for node, type_info in self.last_result.type_map.items():
                print(f"  {type_info}")
        elif cmd == ':python' and self.last_result and self.last_result.python_code:
            print(self.last_result.python_code)
        elif cmd == ':bytecode' and self.last_result and self.last_result.bytecode:
            for instr in self.last_result.bytecode:
                print(f"  {instr}")
        elif cmd == ':run':
            if not arg:
                print("Usage: :run <filename>")
            elif os.path.isfile(arg):
                try:
                    result = self.compiler.compile_file(arg)
                    if result.errors:
                        for err in result.errors:
                            print(f"Error: {err}")
                    elif result.bytecode:
                        instructions, constants = result.bytecode
                        self.vm.run(instructions, constants)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print(f"File not found: {arg}")
        elif cmd == ':load':
            if not arg:
                print("Usage: :load <filename>")
            elif os.path.isfile(arg):
                try:
                    with open(arg, 'r') as f:
                        source = f.read()
                    self.eval_expression(source)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print(f"File not found: {arg}")
        elif cmd == ':reset':
            self.vm = CosmicVM()
            self.variables.clear()
            print("REPL state reset")
        elif cmd == ':vars':
            if not self.variables:
                print("No variables defined")
            else:
                for name, value in self.variables.items():
                    print(f"  {name} = {value!r}")
        else:
            print(f"Unknown command: {cmd}. Type :help for help.")
        return True

    def eval_expression(self, source: str) -> None:
        try:
            result = self.compiler.compile_source(source)
            self.last_result = result
            if result.errors:
                for err in result.errors:
                    print(f"Error: {err}")
            elif result.bytecode:
                instructions, constants = result.bytecode
                self.vm.run(instructions, constants)
        except LexError as e:
            print(f"Lex error: {e}")
        except ParseError as e:
            print(f"Parse error: {e}")
        except TypeCheckError as e:
            print(f"Type error: {e}")
        except Exception as e:
            print(f"Error: {e}")


def print_ast(node, indent: int = 0) -> None:
    prefix = "  " * indent
    name = type(node).__name__
    fields = {k: v for k, v in node.__dict__.items()
              if k not in ('line', 'column') and v is not None}
    if not fields:
        print(f"{prefix}{name}")
        return
    print(f"{prefix}{name}(")
    for key, value in fields.items():
        if hasattr(value, '__dict__') and hasattr(value, 'line'):
            print(f"{prefix}  {key}=")
            print_ast(value, indent + 2)
        elif isinstance(value, list):
            print(f"{prefix}  {key}=[")
            for item in value:
                if hasattr(item, '__dict__') and hasattr(item, 'line'):
                    print_ast(item, indent + 3)
                else:
                    print(f"{prefix}    {item!r}")
            print(f"{prefix}  ]")
        else:
            print(f"{prefix}  {key}={value!r}")
    print(f"{prefix})")


def main():
    repl = REPL()
    repl.run()


if __name__ == '__main__':
    main()
