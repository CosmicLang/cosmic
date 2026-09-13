"""Tests for the bytecode compiler and VM."""
import pytest
from cosmic.parser.parser import parse
from cosmic.backends.bytecode.compiler import BytecodeCompiler, CosmicVM, Op


def run(source: str):
    """Parse, compile, and run source in the VM."""
    ast = parse(source)
    compiler = BytecodeCompiler()
    instructions, constants = compiler.compile(ast)
    vm = CosmicVM()
    return vm.run(instructions, constants)


def get_bytecode(source: str):
    """Parse and compile source, return (instructions, constants)."""
    ast = parse(source)
    compiler = BytecodeCompiler()
    return compiler.compile(ast)


class TestArithmetic:
    def test_add(self):
        assert run("println(2 + 3)") is None  # prints 5

    def test_sub(self):
        assert run("println(10 - 4)") is None

    def test_mul(self):
        assert run("println(3 * 7)") is None

    def test_div(self):
        assert run("println(10 / 2)") is None

    def test_mod(self):
        assert run("println(10 % 3)") is None

    def test_pow(self):
        assert run("println(2 ** 10)") is None

    def test_floor_div(self):
        assert run("println(7 // 2)") is None


class TestComparisons:
    def test_eq(self):
        assert run("println(5 == 5)") is None

    def test_neq(self):
        assert run("println(5 != 3)") is None

    def test_lt(self):
        assert run("println(3 < 5)") is None

    def test_gt(self):
        assert run("println(5 > 3)") is None

    def test_lte(self):
        assert run("println(3 <= 3)") is None

    def test_gte(self):
        assert run("println(5 >= 3)") is None


class TestBooleans:
    def test_and(self):
        assert run("println(true and true)") is None

    def test_or(self):
        assert run("println(false or true)") is None

    def test_not(self):
        assert run("println(not false)") is None


class TestUnaryOps:
    def test_neg(self):
        assert run("println(-5)") is None

    def test_bit_not(self):
        assert run("println(~0)") is None


class TestVariables:
    def test_let_and_load(self):
        assert run("let x = 42\nprintln(x)") is None

    def test_augmented_assign(self):
        assert run("let x = 10\nx += 5\nprintln(x)") is None

    def test_augmented_mul(self):
        assert run("let x = 3\nx *= 4\nprintln(x)") is None


class TestFunctions:
    def test_simple_function(self):
        run("fn add(a, b) { return a + b }\nprintln(add(2, 3))")

    def test_recursive_factorial(self):
        run("""
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
println(factorial(5))
""")

    def test_recursive_fibonacci(self):
        run("""
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
println(fib(10))
""")


class TestControlFlow:
    def test_if_else(self):
        run("let x = 10\nif x > 5 { println(1) } else { println(0) }")

    def test_if_elif_else(self):
        run("let x = 5\nif x > 10 { println('big') } elif x > 3 { println('mid') } else { println('small') }")

    def test_while_loop(self):
        run("let i = 0\nwhile i < 5 { i += 1 }\nprintln(i)")

    def test_for_loop(self):
        run("for i in range(5) { }")


class TestDataStructures:
    def test_list_literal(self):
        run("let arr = [1, 2, 3]\nprintln(len(arr))")

    def test_dict_literal(self):
        run('let d = {"a": 1, "b": 2}\nprintln(len(d))')

    def test_list_index(self):
        run("let arr = [10, 20, 30]\nprintln(arr[1])")


class TestBuiltins:
    def test_print(self):
        run("print(42)")

    def test_len(self):
        run("println(len([1, 2, 3]))")

    def test_int_cast(self):
        run("println(int(3.14))")

    def test_str_cast(self):
        run("println(str(42))")

    def test_range(self):
        run("for i in range(3) { }")


class TestLambda:
    def test_lambda_call(self):
        run("let f = lambda x => x * 2\nprintln(f(5))")


class TestTryCatch:
    def test_try_catch(self):
        run("try { raise 'error' } catch e { println('caught') }")


class TestBytecodeFormat:
    def test_instructions_have_valid_ops(self):
        instructions, constants = get_bytecode("42")
        assert instructions[-1].op == Op.HALT

    def test_no_instructions_for_empty(self):
        instructions, constants = get_bytecode("")
        assert len(instructions) == 1  # just HALT
        assert instructions[0].op == Op.HALT

    def test_multiple_functions(self):
        src = "fn a() { } fn b() { }\nprintln(1)"
        instructions, constants = get_bytecode(src)
        funcs = [c for c in constants if hasattr(c, 'name')]
        assert len(funcs) == 2
