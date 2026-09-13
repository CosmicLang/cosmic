"""Cosmic Language — A modern, powerful programming language."""
__version__ = "0.1.0"
__author__ = "Cosmic Team"

from .lexer.lexer import tokenize, Lexer
from .lexer.tokens import Token, TokenType
from .parser.parser import Parser, parse
from .ast.nodes import Program
from .types.checker import TypeChecker, type_check
from .backends.python.transpiler import PythonTranspiler, transpile
from .backends.bytecode.compiler import BytecodeCompiler, CosmicVM, Op
from .compiler.pipeline import Compiler, CompileResult, compile_source, compile_file

__all__ = [
    'tokenize', 'Lexer', 'Token', 'TokenType',
    'Parser', 'parse', 'Program',
    'TypeChecker', 'type_check',
    'PythonTranspiler', 'transpile',
    'BytecodeCompiler', 'CosmicVM', 'Op',
    'Compiler', 'CompileResult', 'compile_source', 'compile_file',
]
