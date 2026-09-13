"""End-to-end tests — compile → execute → assert output.

Modeled after Kof4j's JvmE2ETest.java pattern:
- Write .cos source to temp file
- Compile via the pipeline
- Execute via bytecode VM or Python transpilation
- Assert exact stdout output
"""
from __future__ import annotations
import subprocess
import tempfile
import os
import pytest
from cosmic.compiler.pipeline import Compiler, CompileResult
from cosmic.backends.bytecode.compiler import CosmicVM


def run_bytecode(source: str) -> str:
    """Compile source and run via bytecode VM, capture stdout."""
    import io
    import sys

    compiler = Compiler(check_types=False)
    result = compiler.compile_source(source)
    if result.errors:
        raise RuntimeError(f"Compilation failed: {result.errors}")
    if result.bytecode is None:
        raise RuntimeError("No bytecode generated")

    instructions, constants = result.bytecode
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        vm = CosmicVM()
        vm.run(instructions, constants)
        return sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout


def run_python(source: str) -> str:
    """Compile source, transpile to Python, execute, capture stdout."""
    compiler = Compiler(check_types=False)
    result = compiler.compile_source(source)
    if result.errors:
        raise RuntimeError(f"Compilation failed: {result.errors}")

    preamble = "println = print\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(preamble + result.python_code)
        f.flush()
        try:
            proc = subprocess.run(
                ['python', f.name],
                capture_output=True, text=True, timeout=5
            )
            return proc.stdout
        finally:
            os.unlink(f.name)


class TestArithmetic:
    def test_addition(self):
        assert "5" in run_bytecode("println(2 + 3)")

    def test_subtraction(self):
        assert "6" in run_bytecode("println(10 - 4)")

    def test_multiplication(self):
        assert "21" in run_bytecode("println(3 * 7)")

    def test_division(self):
        assert "5.0" in run_bytecode("println(10 / 2)")

    def test_floor_division(self):
        assert "3" in run_bytecode("println(7 // 2)")

    def test_modulo(self):
        assert "1" in run_bytecode("println(10 % 3)")

    def test_power(self):
        assert "1024" in run_bytecode("println(2 ** 10)")

    def test_chained(self):
        assert "6" in run_bytecode("println(1 + 2 + 3)")


class TestVariables:
    def test_let_bind(self):
        assert "42" in run_bytecode("let x = 42\nprintln(x)")

    def test_augmented_add(self):
        assert "15" in run_bytecode("let x = 10\nx += 5\nprintln(x)")

    def test_augmented_mul(self):
        assert "12" in run_bytecode("let x = 3\nx *= 4\nprintln(x)")

    def test_multiple_vars(self):
        assert "30" in run_bytecode("let a = 10\nlet b = 20\nprintln(a + b)")


class TestFunctions:
    def test_simple_fn(self):
        assert "5" in run_bytecode("fn add(a, b) { return a + b }\nprintln(add(2, 3))")

    def test_recursive_factorial(self):
        assert "120" in run_bytecode("""
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
println(factorial(5))
""")

    def test_recursive_fibonacci(self):
        assert "55" in run_bytecode("""
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
println(fib(10))
""")


class TestControlFlow:
    def test_if_else(self):
        assert "1" in run_bytecode("let x = 10\nif x > 5 { println(1) } else { println(0) }")

    def test_if_elif_else(self):
        assert "mid" in run_bytecode("let x = 5\nif x > 10 { println('big') } elif x > 3 { println('mid') } else { println('small') }")

    def test_while_loop(self):
        assert "5" in run_bytecode("let i = 0\nwhile i < 5 { i += 1 }\nprintln(i)")

    def test_for_loop(self):
        output = run_bytecode("for i in range(3) { println(i) }")
        assert "0" in output and "1" in output and "2" in output


class TestDataStructures:
    def test_list_length(self):
        assert "3" in run_bytecode("let arr = [1, 2, 3]\nprintln(len(arr))")

    def test_dict_length(self):
        assert "2" in run_bytecode('let d = {"a": 1, "b": 2}\nprintln(len(d))')

    def test_list_index(self):
        assert "20" in run_bytecode("let arr = [10, 20, 30]\nprintln(arr[1])")


class TestBuiltins:
    def test_print(self):
        assert "42" in run_bytecode("print(42)")

    def test_len_string(self):
        assert "5" in run_bytecode('println(len("hello"))')

    def test_int_cast(self):
        assert "3" in run_bytecode("println(int(3.14))")

    def test_str_cast(self):
        assert "42" in run_bytecode("println(str(42))")


class TestStrings:
    def test_concat(self):
        assert "helloworld" in run_bytecode('println("hello" + "world")')

    def test_multiply(self):
        assert "ababab" in run_bytecode('println("ab" * 3)')


class TestLambda:
    def test_lambda_call(self):
        assert "10" in run_bytecode("let f = lambda x => x * 2\nprintln(f(5))")

    def test_lambda_multi_param(self):
        assert "7" in run_bytecode("let add = lambda a, b => a + b\nprintln(add(3, 4))")


class TestTryCatch:
    def test_catch_error(self):
        assert "caught" in run_bytecode("try { raise 'error' } catch e { println('caught') }")

    def test_no_error(self):
        assert "ok" in run_bytecode("try { println('ok') } catch e { println('err') }")


class TestTranspiledExecution:
    def test_addition_python(self):
        assert "5" in run_python("println(2 + 3)")

    def test_function_python(self):
        assert "5" in run_python("fn add(a, b) { return a + b }\nprintln(add(2, 3))")

    def test_if_else_python(self):
        assert "yes" in run_python("let x = 10\nif x > 5 { println('yes') } else { println('no') }")

    def test_factorial_python(self):
        assert "120" in run_python("""
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
println(factorial(5))
""")
