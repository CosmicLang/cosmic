"""Golden file tests — compile+run .cos files and compare output to expected.txt."""
import os
import pytest
from cosmic.parser.parser import parse
from cosmic.backends.bytecode.compiler import BytecodeCompiler, CosmicVM

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")


def run_cosmic(source: str) -> str:
    """Run Cosmic source and capture output."""
    import io, sys
    ast = parse(source)
    compiler = BytecodeCompiler()
    instructions, constants = compiler.compile(ast)
    vm = CosmicVM()
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        vm.run(instructions, constants)
    except Exception:
        pass
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    return output


def get_test_cases():
    """Discover all golden test cases."""
    cases = []
    for name in sorted(os.listdir(GOLDEN_DIR)):
        case_dir = os.path.join(GOLDEN_DIR, name)
        if os.path.isdir(case_dir):
            cos_file = os.path.join(case_dir, "main.cos")
            expected_file = os.path.join(case_dir, "expected.txt")
            if os.path.isfile(cos_file) and os.path.isfile(expected_file):
                cases.append((name, cos_file, expected_file))
    return cases


@pytest.mark.golden
@pytest.mark.parametrize("name,cos_file,expected_file", get_test_cases(),
                         ids=[c[0] for c in get_test_cases()])
def test_golden(name, cos_file, expected_file):
    with open(cos_file, 'r') as f:
        source = f.read()
    with open(expected_file, 'r') as f:
        expected = f.read()

    output = run_cosmic(source)
    assert output == expected, f"Golden test '{name}' failed.\nExpected:\n{expected!r}\nGot:\n{output!r}"
