"""Tests for the type checker."""
import pytest
from cosmic.parser.parser import parse
from cosmic.types.checker import type_check


def tc(source: str):
    """Type check source and return (type_map, errors)."""
    return type_check(parse(source))


class TestBasicTypes:
    def test_int_literal(self):
        tm, errs = tc("let x = 42")
        assert len(errs) == 0

    def test_float_literal(self):
        tm, errs = tc("let x = 3.14")
        assert len(errs) == 0

    def test_string_literal(self):
        tm, errs = tc('let x = "hello"')
        assert len(errs) == 0

    def test_bool_literal(self):
        tm, errs = tc("let x = true")
        assert len(errs) == 0

    def test_none_literal(self):
        tm, errs = tc("let x = none")
        assert len(errs) == 0


class TestExpressions:
    def test_binary_int(self):
        tm, errs = tc("let x = 1 + 2")
        assert len(errs) == 0

    def test_comparison(self):
        tm, errs = tc("let x = 1 < 2")
        assert len(errs) == 0

    def test_and_or(self):
        tm, errs = tc("let x = true and false or true")
        assert len(errs) == 0

    def test_not(self):
        tm, errs = tc("let x = not true")
        assert len(errs) == 0


class TestFunctions:
    def test_function_declaration(self):
        tm, errs = tc("fn noop() { }")
        assert len(errs) == 0

    def test_function_call(self):
        tm, errs = tc("fn noop() { }\nnoop()")
        assert len(errs) == 0


class TestControlFlow:
    def test_if_statement(self):
        tm, errs = tc("if true { let x = 1 }")
        assert len(errs) == 0

    def test_while_loop(self):
        tm, errs = tc("let i = 0\nwhile i < 10 { i += 1 }")
        assert len(errs) == 0

    def test_for_loop(self):
        tm, errs = tc("for i in range(10) { }")
        assert len(errs) == 0


class TestDataStructures:
    def test_list(self):
        tm, errs = tc("let x = [1, 2, 3]")
        assert len(errs) == 0

    def test_dict(self):
        tm, errs = tc('let x = {"a": 1}')
        assert len(errs) == 0

    def test_tuple(self):
        tm, errs = tc("let x = (1, 2, 3)")
        assert len(errs) == 0


class TestImports:
    def test_import(self):
        tm, errs = tc("import os")
        assert len(errs) == 0

    def test_from_import(self):
        tm, errs = tc("from os import path")
        assert len(errs) == 0


class TestLambda:
    def test_lambda(self):
        tm, errs = tc("let f = lambda x => x + 1")
        assert len(errs) == 0
