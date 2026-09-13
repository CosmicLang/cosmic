"""Tests for the bytecode compiler and VM."""
from cosmic.parser.parser import parse
from cosmic.backends.bytecode.compiler import BytecodeCompiler, CosmicVM, Op


def run(source: str):
    """Parse, compile, and run source in the VM."""
    ast = parse(source)
    compiler = BytecodeCompiler()
    instructions, constants = compiler.compile(ast)
    vm = CosmicVM()
    return vm.run(instructions, constants)


def run_output(source: str) -> str:
    """Run source and capture printed output."""
    ast = parse(source)
    compiler = BytecodeCompiler()
    instructions, constants = compiler.compile(ast)
    vm = CosmicVM()
    vm.run(instructions, constants)
    return "".join(vm.output_buffer)


def get_bytecode(source: str):
    """Parse and compile source, return (instructions, constants)."""
    ast = parse(source)
    compiler = BytecodeCompiler()
    return compiler.compile(ast)


class TestArithmetic:
    def test_add(self):
        assert "5" in run_output("println(2 + 3)")

    def test_sub(self):
        assert "6" in run_output("println(10 - 4)")

    def test_mul(self):
        assert "21" in run_output("println(3 * 7)")

    def test_div(self):
        assert "5.0" in run_output("println(10 / 2)")

    def test_mod(self):
        assert "1" in run_output("println(10 % 3)")

    def test_pow(self):
        assert "1024" in run_output("println(2 ** 10)")

    def test_floor_div(self):
        assert "3" in run_output("println(7 // 2)")

    def test_add_floats(self):
        assert "5.5" in run_output("println(2.5 + 3.0)")

    def test_negative_numbers(self):
        assert "-5" in run_output("println(-5)")

    def test_chained_add(self):
        assert "6" in run_output("println(1 + 2 + 3)")


class TestComparisons:
    def test_eq(self):
        assert "True" in run_output("println(5 == 5)")

    def test_neq(self):
        assert "True" in run_output("println(5 != 3)")

    def test_lt(self):
        assert "True" in run_output("println(3 < 5)")

    def test_gt(self):
        assert "True" in run_output("println(5 > 3)")

    def test_lte(self):
        assert "True" in run_output("println(3 <= 3)")

    def test_gte(self):
        assert "True" in run_output("println(5 >= 3)")

    def test_eq_false(self):
        assert "False" in run_output("println(5 == 3)")

    def test_string_eq(self):
        assert "True" in run_output('println("abc" == "abc")')


class TestBooleans:
    def test_and(self):
        assert "True" in run_output("println(true and true)")

    def test_or(self):
        assert "True" in run_output("println(false or true)")

    def test_not(self):
        assert "True" in run_output("println(not false)")

    def test_and_false(self):
        assert "False" in run_output("println(true and false)")

    def test_or_false(self):
        assert "False" in run_output("println(false or false)")


class TestUnaryOps:
    def test_neg(self):
        assert "-5" in run_output("println(-5)")

    def test_bit_not(self):
        assert "-1" in run_output("println(~0)")

    def test_double_neg(self):
        assert "5" in run_output("println(-(-5))")


class TestVariables:
    def test_let_and_load(self):
        assert "42" in run_output("let x = 42\nprintln(x)")

    def test_augmented_assign(self):
        assert "15" in run_output("let x = 10\nx += 5\nprintln(x)")

    def test_augmented_mul(self):
        assert "12" in run_output("let x = 3\nx *= 4\nprintln(x)")

    def test_augmented_sub(self):
        assert "7" in run_output("let x = 10\nx -= 3\nprintln(x)")

    def test_multiple_vars(self):
        assert "30" in run_output("let a = 10\nlet b = 20\nprintln(a + b)")


class TestFunctions:
    def test_simple_function(self):
        assert "5" in run_output("fn add(a, b) { return a + b }\nprintln(add(2, 3))")

    def test_recursive_factorial(self):
        assert "120" in run_output("""
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
println(factorial(5))
""")

    def test_recursive_fibonacci(self):
        assert "55" in run_output("""
fn fib(n) {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
println(fib(10))
""")

    def test_function_no_return(self):
        result = run("fn noop() { }\nprintln(noop())")
        assert result is None

    def test_function_with_default(self):
        result = run("fn greet(name) { println(name) }\ngreet(\"World\")")
        assert "World" in run_output("fn greet(name) { println(name) }\ngreet(\"World\")")


class TestControlFlow:
    def test_if_else(self):
        assert "1" in run_output("let x = 10\nif x > 5 { println(1) } else { println(0) }")

    def test_if_elif_else(self):
        assert "mid" in run_output("let x = 5\nif x > 10 { println('big') } elif x > 3 { println('mid') } else { println('small') }")

    def test_while_loop(self):
        assert "5" in run_output("let i = 0\nwhile i < 5 { i += 1 }\nprintln(i)")

    def test_for_loop(self):
        output = run_output("for i in range(3) { println(i) }")
        assert "0" in output and "1" in output and "2" in output

    def test_if_false_branch(self):
        assert "0" in run_output("let x = 2\nif x > 10 { println(1) } else { println(0) }")


class TestDataStructures:
    def test_list_literal(self):
        assert "3" in run_output("let arr = [1, 2, 3]\nprintln(len(arr))")

    def test_dict_literal(self):
        assert "2" in run_output('let d = {"a": 1, "b": 2}\nprintln(len(d))')

    def test_list_index(self):
        assert "20" in run_output("let arr = [10, 20, 30]\nprintln(arr[1])")

    def test_list_first(self):
        assert "10" in run_output("let arr = [10, 20, 30]\nprintln(arr[0])")

    def test_dict_access(self):
        assert "1" in run_output('let d = {"a": 1}\nprintln(d["a"])')

    def test_nested_list(self):
        assert "3" in run_output("let arr = [[1, 2], [3, 4]]\nprintln(arr[1][0])")


class TestBuiltins:
    def test_print(self):
        assert "42" in run_output("print(42)")

    def test_len(self):
        assert "3" in run_output("println(len([1, 2, 3]))")

    def test_int_cast(self):
        assert "3" in run_output("println(int(3.14))")

    def test_str_cast(self):
        assert "42" in run_output("println(str(42))")

    def test_range(self):
        output = run_output("for i in range(3) { print(i) }")
        assert "0" in output and "1" in output and "2" in output

    def test_len_string(self):
        assert "5" in run_output('println(len("hello"))')

    def test_is_none(self):
        assert "True" in run_output("println(none == none)")


class TestLambda:
    def test_lambda_call(self):
        assert "10" in run_output("let f = lambda x => x * 2\nprintln(f(5))")

    def test_lambda_multi_param(self):
        assert "7" in run_output("let add = lambda a, b => a + b\nprintln(add(3, 4))")


class TestTryCatch:
    def test_try_catch(self):
        assert "caught" in run_output("try { raise 'error' } catch e { println('caught') }")

    def test_try_no_error(self):
        assert "ok" in run_output("try { println('ok') } catch e { println('err') }")


class TestStringOperations:
    def test_string_concat(self):
        assert "helloworld" in run_output('println("hello" + "world")')

    def test_string_multiply(self):
        assert "ababab" in run_output('println("ab" * 3)')


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

    def test_constants_populated(self):
        instructions, constants = get_bytecode('println("hello")')
        assert "hello" in constants
