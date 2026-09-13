"""Tests for the Python transpiler."""
import pytest
from cosmic.parser.parser import parse
from cosmic.backends.python.transpiler import transpile


def tc(source: str) -> str:
    """Parse and transpile source to Python."""
    return transpile(parse(source))


def check_valid_python(py_code: str):
    """Verify the generated code is valid Python."""
    compile(py_code, "<test>", "exec")


def run_transpiled(source: str) -> str:
    """Transpile Cosmic source, execute the Python, capture stdout."""
    import subprocess, tempfile, os
    py_code = tc(source)
    preamble = "println = print\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(preamble + py_code)
        f.flush()
        try:
            result = subprocess.run(
                ['python', f.name],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout + result.stderr
        finally:
            os.unlink(f.name)


class TestFunctions:
    def test_simple_function(self):
        code = tc("fn add(a, b) { return a + b }")
        assert "def add(a, b):" in code
        assert "return a + b" in code
        check_valid_python(code)

    def test_expression_body(self):
        code = tc("fn double(x) = x * 2")
        assert "def double(x):" in code
        assert "x * 2" in code

    def test_no_arg_function(self):
        code = tc("fn greet() { return 'hi' }")
        assert "def greet():" in code
        check_valid_python(code)


class TestVariables:
    def test_let_statement(self):
        code = tc("let x = 10")
        assert "x = 10" in code
        check_valid_python(code)

    def test_let_with_type(self):
        code = tc("let x: int = 10")
        assert "x = 10" in code

    def test_var_mutable(self):
        code = tc("var y = 20")
        assert "y = 20" in code


class TestControlFlow:
    def test_if_else(self):
        code = tc("if true { let x = 1 } else { let x = 2 }")
        assert "if True:" in code
        assert "x = 1" in code
        assert "else:" in code
        assert "x = 2" in code

    def test_while_loop(self):
        code = tc("while true { let x = 1 }")
        assert "while True:" in code

    def test_for_loop(self):
        code = tc("for i in range(10) { print(i) }")
        assert "for i in range(10):" in code
        check_valid_python(code)

    def test_break_continue(self):
        code = tc("loop { break }")
        assert "break" in code

    def test_for_with_continue(self):
        code = tc("for i in range(10) { continue }")
        assert "continue" in code


class TestLiterals:
    def test_int_literal(self):
        code = tc("42")
        assert "42" in code

    def test_string_literal(self):
        code = tc('"hello"')
        assert "hello" in code

    def test_bool_literal(self):
        code = tc("true")
        assert "True" in code

    def test_none_literal(self):
        code = tc("none")
        assert "None" in code

    def test_list_literal(self):
        code = tc("[1, 2, 3]")
        assert "[1, 2, 3]" in code
        check_valid_python(code)


class TestOperators:
    def test_binary_ops(self):
        code = tc("let z = x + y * 2")
        assert "x + " in code

    def test_comparison(self):
        code = tc("if a < b { }")
        assert "a < b" in code

    def test_and_or(self):
        code = tc("if a and b or c { }")
        assert "a" in code and "and" in code and "or" in code

    def test_not(self):
        code = tc("if not x { }")
        assert "not x" in code


class TestExpressions:
    def test_function_call(self):
        code = tc("add(1, 2)")
        assert "add(1, 2)" in code

    def test_lambda(self):
        code = tc("lambda x => x + 1")
        assert "lambda x:" in code
        assert "x + 1" in code

    def test_pipe(self):
        code = tc("x |> f")
        assert "f(x)" in code

    def test_index_expr(self):
        code = tc("arr[0]")
        assert "arr[0]" in code


class TestClasses:
    def test_simple_class(self):
        code = tc("class Animal { }")
        assert "class Animal:" in code
        check_valid_python(code)


class TestRecord:
    def test_record_to_dataclass(self):
        code = tc("record Point(x: int, y: int)")
        assert "dataclass" in code.lower() or "Point" in code


class TestEnum:
    def test_enum_declaration(self):
        code = tc("enum Color { RED, GREEN, BLUE }")
        assert "Color" in code
        check_valid_python(code)


class TestTryCatch:
    def test_try_catch(self):
        code = tc("try { x } catch e { y }")
        assert "try:" in code
        assert "except" in code
        check_valid_python(code)


class TestImport:
    def test_import(self):
        code = tc("import os")
        assert "import os" in code

    def test_from_import(self):
        code = tc("from os import path")
        assert "from os import path" in code


class TestComplex:
    def test_nested_if(self):
        code = tc("if a { if b { let x = 1 } }")
        check_valid_python(code)

    def test_function_with_class(self):
        code = tc("""
class Foo {
}
fn bar() {
    let f = Foo()
}
""")
        check_valid_python(code)


class TestEndToEnd:
    def test_addition(self):
        output = run_transpiled("println(2 + 3)")
        assert "5" in output

    def test_function_call(self):
        output = run_transpiled("fn add(a, b) { return a + b }\nprintln(add(2, 3))")
        assert "5" in output

    def test_if_else(self):
        output = run_transpiled("let x = 10\nif x > 5 { println('yes') } else { println('no') }")
        assert "yes" in output

    def test_while_loop(self):
        output = run_transpiled("let i = 0\nwhile i < 5 { i += 1 }\nprintln(i)")
        assert "5" in output

    def test_for_loop(self):
        output = run_transpiled("for i in range(3) { println(i) }")
        assert "0" in output and "1" in output and "2" in output

    def test_list_operations(self):
        output = run_transpiled("let arr = [1, 2, 3]\nprintln(len(arr))")
        assert "3" in output

    def test_lambda(self):
        output = run_transpiled("let f = lambda x => x * 2\nprintln(f(5))")
        assert "10" in output

    def test_record(self):
        output = run_transpiled("record Point(x: int, y: int)\nlet p = Point(1, 2)\nprintln(p.x)")
        assert "1" in output

    def test_enum(self):
        output = run_transpiled("enum Color { RED, GREEN, BLUE }\nlet c = Color.RED\nprintln(c)")
        assert "RED" in output

    def test_factorial(self):
        output = run_transpiled("""
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
println(factorial(5))
""")
        assert "120" in output

    def test_string_concat(self):
        output = run_transpiled('println("hello" + " " + "world")')
        assert "hello world" in output

    def test_pipe(self):
        output = run_transpiled("fn double(x) { return x * 2 }\nlet result = 5 |> double\nprintln(result)")
        assert "10" in output

    def test_nullish_coalesce(self):
        output = run_transpiled("let x: any = none\nlet y = x ?? 42\nprintln(y)")
        assert "42" in output
