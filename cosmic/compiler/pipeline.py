"""Cosmic Compiler Pipeline — orchestrates all phases."""
from __future__ import annotations
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

from ..lexer.lexer import tokenize
from ..lexer.tokens import Token
from ..parser.parser import Parser, parse
from ..ast.nodes import Program
from ..types.checker import TypeChecker, type_check
from ..backends.python.transpiler import PythonTranspiler, transpile
from ..backends.bytecode.compiler import BytecodeCompiler, CosmicVM


@dataclass
class CompileResult:
    ast: Program | None = None
    python_code: str = ''
    bytecode: tuple | None = None
    type_map: dict | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Compiler:
    def __init__(self, filename: str = '<stdin>', check_types: bool = True):
        self.filename = filename
        self.check_types = check_types

    def compile_source(self, source: str) -> CompileResult:
        result = CompileResult()
        try:
            tokens = tokenize(source, self.filename)
            parser = Parser(tokens, self.filename)
            ast = parser.parse()
            result.ast = ast
        except Exception as e:
            result.errors.append(f"Parse error: {e}")
            return result

        if self.check_types:
            try:
                type_map, type_errors = type_check(ast)
                result.type_map = type_map
                result.warnings.extend(type_errors)
            except Exception as e:
                result.warnings.append(f"Type check warning: {e}")

        try:
            result.python_code = transpile(ast)
        except Exception as e:
            result.errors.append(f"Python transpile error: {e}")

        try:
            compiler = BytecodeCompiler()
            instructions, constants = compiler.compile(ast)
            result.bytecode = (instructions, constants)
        except Exception as e:
            result.warnings.append(f"Bytecode warning: {e}")

        return result

    def compile_file(self, path: str) -> CompileResult:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        return self.compile_source(source)

    def to_python(self, source: str) -> str:
        result = self.compile_source(source)
        if result.errors:
            raise RuntimeError('\n'.join(result.errors))
        return result.python_code

    def to_bytecode(self, source: str) -> tuple:
        result = self.compile_source(source)
        if result.errors:
            raise RuntimeError('\n'.join(result.errors))
        if result.bytecode is None:
            raise RuntimeError("Bytecode compilation failed")
        return result.bytecode

    def run_bytecode(self, source: str) -> Any:
        instructions, constants = self.to_bytecode(source)
        vm = CosmicVM()
        return vm.run(instructions, constants)


def compile_file(path: str) -> CompileResult:
    return Compiler(filename=path).compile_file(path)


def compile_source(source: str, filename: str = '<stdin>') -> CompileResult:
    return Compiler(filename=filename).compile_source(source)


def run_source(source: str) -> Any:
    return Compiler().run_bytecode(source)


def transpile_to_python(source: str, filename: str = '<stdin>') -> str:
    return Compiler(filename=filename).to_python(source)
