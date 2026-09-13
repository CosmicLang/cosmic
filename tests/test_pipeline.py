"""Tests for the full compiler pipeline."""
import pytest
from cosmic.compiler.pipeline import Compiler, compile_source, CompileResult


class TestCompileSource:
    def test_returns_result(self):
        result = compile_source("let x = 10")
        assert isinstance(result, CompileResult)

    def test_has_ast(self):
        result = compile_source("let x = 10")
        assert result.ast is not None

    def test_has_python_code(self):
        result = compile_source("let x = 10")
        assert len(result.python_code) > 0

    def test_has_bytecode(self):
        result = compile_source("let x = 10")
        assert result.bytecode is not None

    def test_no_errors(self):
        result = compile_source("let x = 10")
        assert len(result.errors) == 0

    def test_empty_source(self):
        result = compile_source("")
        assert len(result.errors) == 0

    def test_function_and_call(self):
        result = compile_source("fn add(a, b) { return a + b }", filename="<test>")
        assert result.ast is not None
        assert result.python_code
        assert result.bytecode


class TestCompiler:
    def test_compiler_instance(self):
        c = Compiler()
        assert c is not None

    def test_compile_source(self):
        c = Compiler()
        result = c.compile_source("let x = 42")
        assert isinstance(result, CompileResult)
        assert result.ast is not None


class TestTranspile:
    def test_transpile_output(self):
        result = compile_source("fn f() { return 1 }\nf()")
        assert "def f():" in result.python_code
        assert "return 1" in result.python_code

    def test_transpile_control_flow(self):
        result = compile_source("if true { let x = 1 } else { let x = 2 }")
        assert "if" in result.python_code
        assert "else" in result.python_code


class TestBytecode:
    def test_bytecode_has_instructions(self):
        result = compile_source("42")
        assert result.bytecode is not None
        instructions, constants = result.bytecode
        assert len(instructions) > 0


class TestEndToEnd:
    def test_parse_transpile_valid_python(self):
        result = compile_source("let x = 1 + 2\nprint(x)")
        assert len(result.errors) == 0
        compile(result.python_code, "<test>", "exec")

    def test_complex_program(self):
        src = """
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
println(factorial(10))
"""
        result = compile_source(src)
        assert len(result.errors) == 0
        assert result.python_code
        assert result.bytecode
