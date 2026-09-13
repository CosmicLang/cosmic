"""Lightweight test framework with assertions and test suites for the Cosmic Standard Library."""
from __future__ import annotations
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class TestResult:
    name: str
    passed: bool
    error: str = ''
    duration: float = 0.0
    skipped: bool = False


@dataclass
class TestSuite:
    name: str = "CosmicTests"
    _tests: list[tuple[str, Callable]] = field(default_factory=list)
    _results: list[TestResult] = field(default_factory=list)

    def add(self, name: str, func: Callable) -> None:
        """Add a named test function to the suite."""
        self._tests.append((name, func))

    def run(self, verbose: bool = True) -> list[TestResult]:
        """Run all tests and return results."""
        self._results = []
        total = len(self._tests)
        passed = 0
        failed = 0
        start = time.time()

        for name, func in self._tests:
            result_start = time.time()
            try:
                func()
                duration = time.time() - result_start
                self._results.append(TestResult(name=name, passed=True, duration=duration))
                passed += 1
                if verbose:
                    print(f"  \033[92m✓\033[0m {name} ({duration*1000:.1f}ms)")
            except AssertionError as e:
                duration = time.time() - result_start
                self._results.append(TestResult(name=name, passed=False, error=str(e), duration=duration))
                failed += 1
                if verbose:
                    print(f"  \033[91m✗\033[0m {name}: {e}")
            except Exception as e:
                duration = time.time() - result_start
                self._results.append(TestResult(name=name, passed=False, error=str(e), duration=duration))
                failed += 1
                if verbose:
                    print(f"  \033[91m✗\033[0m {name}: {type(e).__name__}: {e}")

        total_duration = time.time() - start
        if verbose:
            print(f"\n  {passed} passed, {failed} failed in {total_duration*1000:.1f}ms")
        return self._results

    def report(self) -> str:
        """Return a formatted test report string."""
        lines = [f"Test Suite: {self.name}"]
        lines.append(f"{'='*50}")
        for r in self._results:
            status = "\033[92mPASS\033[0m" if r.passed else "\033[91mFAIL\033[0m"
            lines.append(f"  [{status}] {r.name} ({r.duration*1000:.1f}ms)")
            if r.error:
                lines.append(f"         {r.error}")
        passed = sum(1 for r in self._results if r.passed)
        failed = sum(1 for r in self._results if not r.passed)
        lines.append(f"\n  {passed}/{len(self._results)} passed")
        return '\n'.join(lines)


def assert_equal(actual: Any, expected: Any, msg: str = '') -> None:
    """Assert that actual equals expected."""
    if actual != expected:
        raise AssertionError(msg or f"Expected {expected!r}, got {actual!r}")


def assert_not_equal(actual: Any, expected: Any, msg: str = '') -> None:
    """Assert that actual does not equal expected."""
    if actual == expected:
        raise AssertionError(msg or f"Expected values to be different, both are {actual!r}")


def assert_true(value: Any, msg: str = '') -> None:
    """Assert that value is truthy."""
    if not value:
        raise AssertionError(msg or f"Expected truthy value, got {value!r}")


def assert_false(value: Any, msg: str = '') -> None:
    """Assert that value is falsy."""
    if value:
        raise AssertionError(msg or f"Expected falsy value, got {value!r}")


def assert_raises(exception_type: type, func: Callable, *args: Any, **kwargs: Any) -> None:
    """Assert that func raises the given exception type."""
    try:
        func(*args, **kwargs)
    except exception_type:
        return
    except Exception as e:
        raise AssertionError(f"Expected {exception_type.__name__}, got {type(e).__name__}: {e}")
    raise AssertionError(f"Expected {exception_type.__name__} to be raised, but nothing was raised")


def assert_in(item: Any, container: Any, msg: str = '') -> None:
    """Assert that item is in container."""
    if item not in container:
        raise AssertionError(msg or f"Expected {item!r} to be in {container!r}")


def assert_not_in(item: Any, container: Any, msg: str = '') -> None:
    """Assert that item is not in container."""
    if item in container:
        raise AssertionError(msg or f"Expected {item!r} not to be in {container!r}")


def assert_is_none(value: Any, msg: str = '') -> None:
    """Assert that value is None."""
    if value is not None:
        raise AssertionError(msg or f"Expected None, got {value!r}")


def assert_is_not_none(value: Any, msg: str = '') -> None:
    """Assert that value is not None."""
    if value is None:
        raise AssertionError(msg or f"Expected non-None value, got None")


def assert_greater(a: Any, b: Any, msg: str = '') -> None:
    """Assert that a > b."""
    if not (a > b):
        raise AssertionError(msg or f"Expected {a!r} > {b!r}")


def assert_greater_equal(a: Any, b: Any, msg: str = '') -> None:
    """Assert that a >= b."""
    if not (a >= b):
        raise AssertionError(msg or f"Expected {a!r} >= {b!r}")


def assert_less(a: Any, b: Any, msg: str = '') -> None:
    """Assert that a < b."""
    if not (a < b):
        raise AssertionError(msg or f"Expected {a!r} < {b!r}")


def assert_less_equal(a: Any, b: Any, msg: str = '') -> None:
    """Assert that a <= b."""
    if not (a <= b):
        raise AssertionError(msg or f"Expected {a!r} <= {b!r}")


def assert_contains(haystack: Any, needle: Any, msg: str = '') -> None:
    """Assert that needle is contained in haystack."""
    if needle not in haystack:
        raise AssertionError(msg or f"Expected {needle!r} to be contained in {haystack!r}")


def assert_type(value: Any, expected_type: type, msg: str = '') -> None:
    """Assert that value is an instance of expected_type."""
    if not isinstance(value, expected_type):
        raise AssertionError(msg or f"Expected type {expected_type.__name__}, got {type(value).__name__}")


def assert_length(collection: Any, expected: int, msg: str = '') -> None:
    """Assert that the collection has the expected length."""
    actual = len(collection)
    if actual != expected:
        raise AssertionError(msg or f"Expected length {expected}, got {actual}")


def assert_approx_equal(actual: float, expected: float, places: int = 7, msg: str = '') -> None:
    """Assert that two floats are approximately equal within decimal places."""
    if round(abs(actual - expected), places) != 0:
        raise AssertionError(msg or f"Expected {actual} ≈ {expected} (within {places} decimal places)")


def assert_regex(string: str, pattern: str, msg: str = '') -> None:
    """Assert that the string matches the regex pattern."""
    import re
    if not re.search(pattern, string):
        raise AssertionError(msg or f"Expected {string!r} to match pattern {pattern!r}")


def test(name: str) -> Callable:
    """Decorator to mark a function as a named test."""
    def decorator(func: Callable) -> Callable:
        func._test_name = name
        return func
    return decorator


def describe(name: str) -> Callable:
    """Decorator to mark a function as a test group/describe block."""
    def decorator(func: Callable) -> Callable:
        func._describe_name = name
        return func
    return decorator
