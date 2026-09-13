"""Tests for the Cosmic parser."""
import pytest
from cosmic.parser.parser import parse, ParseError
from cosmic.ast.nodes import *


class TestFunctionDeclaration:
    def test_simple_fn(self):
        ast = parse("fn main() { }")
        assert len(ast.statements) == 1
        fn = ast.statements[0]
        assert isinstance(fn, FnDecl)
        assert fn.name == "main"
        assert len(fn.params) == 0

    def test_fn_with_params(self):
        ast = parse("fn add(a: int, b: int) { }")
        fn = ast.statements[0]
        assert len(fn.params) == 2
        assert fn.params[0].name == "a"
        assert fn.params[1].name == "b"

    def test_fn_with_return_type(self):
        ast = parse("fn add(a: int, b: int) -> int { }")
        fn = ast.statements[0]
        assert fn.return_type is not None
        assert fn.return_type.name == "int"

    def test_fn_expression_body(self):
        ast = parse("fn double(x) = x * 2")
        fn = ast.statements[0]
        assert fn.body is not None
        assert isinstance(fn.body, BinaryExpr)

    def test_fn_with_default_param(self):
        ast = parse("fn greet(name: str = 'world') { }")
        fn = ast.statements[0]
        assert fn.params[0].default is not None

    def test_pub_fn(self):
        ast = parse("pub fn helper() { }")
        fn = ast.statements[0]
        assert fn.is_pub is True


class TestClassDeclaration:
    def test_simple_class(self):
        ast = parse("class Animal { }")
        cls = ast.statements[0]
        assert isinstance(cls, ClassDecl)
        assert cls.name == "Animal"

    def test_class_with_bases(self):
        ast = parse("class Dog extends Animal { }")
        cls = ast.statements[0]
        assert len(cls.bases) == 1
        assert cls.bases[0].name == "Animal"


class TestRecordDeclaration:
    def test_record(self):
        ast = parse("record Point(x: int, y: int)")
        rec = ast.statements[0]
        assert isinstance(rec, RecordDecl)
        assert rec.name == "Point"
        assert len(rec.fields) == 2


class TestEnumDeclaration:
    def test_simple_enum(self):
        ast = parse("enum Color { RED, GREEN, BLUE }")
        en = ast.statements[0]
        assert isinstance(en, EnumDecl)
        assert len(en.variants) == 3
        assert en.variants[0].name == "RED"


class TestLetStatement:
    def test_let_with_type(self):
        ast = parse("let x: int = 10")
        stmt = ast.statements[0]
        assert isinstance(stmt, LetStmt)
        assert stmt.name == "x"
        assert stmt.value is not None

    def test_let_without_type(self):
        ast = parse("let y = 20")
        stmt = ast.statements[0]
        assert isinstance(stmt, LetStmt)
        assert stmt.type_ref is None

    def test_var_mutable(self):
        ast = parse("var z = 30")
        stmt = ast.statements[0]
        assert isinstance(stmt, LetStmt)
        assert stmt.mutable is True


class TestExpressions:
    def test_binary_expr(self):
        ast = parse("1 + 2")
        expr = ast.statements[0].expr
        assert isinstance(expr, BinaryExpr)
        assert expr.op == "+"

    def test_precedence_mul_before_add(self):
        ast = parse("1 + 2 * 3")
        expr = ast.statements[0].expr
        assert isinstance(expr, BinaryExpr)
        assert expr.op == "+"
        assert isinstance(expr.right, BinaryExpr)
        assert expr.right.op == "*"

    def test_paren_precedence(self):
        ast = parse("(1 + 2) * 3")
        expr = ast.statements[0].expr
        assert isinstance(expr, BinaryExpr)
        assert expr.op == "*"
        assert isinstance(expr.left, BinaryExpr)

    def test_unary_minus(self):
        ast = parse("-x")
        expr = ast.statements[0].expr
        assert isinstance(expr, UnaryExpr)
        assert expr.op == "-"

    def test_not_operator(self):
        ast = parse("not x")
        expr = ast.statements[0].expr
        assert isinstance(expr, UnaryExpr)
        assert expr.op == "not"

    def test_comparison(self):
        ast = parse("a < b")
        expr = ast.statements[0].expr
        assert isinstance(expr, BinaryExpr)
        assert expr.op == "<"

    def test_string_literal(self):
        ast = parse('"hello"')
        expr = ast.statements[0].expr
        assert isinstance(expr, StringLiteral)
        assert expr.value == "hello"

    def test_none_literal(self):
        ast = parse("none")
        expr = ast.statements[0].expr
        assert isinstance(expr, NoneLiteral)

    def test_function_call(self):
        ast = parse("add(1, 2)")
        expr = ast.statements[0].expr
        assert isinstance(expr, CallExpr)
        assert len(expr.args) == 2

    def test_method_call(self):
        ast = parse("obj.method()")
        expr = ast.statements[0].expr
        assert isinstance(expr, CallExpr)
        assert isinstance(expr.callee, PropertyAccessExpr)
        assert expr.callee.property == "method"

    def test_property_access(self):
        ast = parse("obj.prop")
        expr = ast.statements[0].expr
        assert isinstance(expr, PropertyAccessExpr)
        assert expr.property == "prop"

    def test_index_expr(self):
        ast = parse("arr[0]")
        expr = ast.statements[0].expr
        assert isinstance(expr, IndexExpr)

    def test_list_literal(self):
        ast = parse("[1, 2, 3]")
        expr = ast.statements[0].expr
        assert isinstance(expr, ListExpr)
        assert len(expr.elements) == 3

    def test_dict_literal(self):
        ast = parse('let d = {"a": 1, "b": 2}')
        stmt = ast.statements[0]
        assert isinstance(stmt, LetStmt)
        assert isinstance(stmt.value, DictExpr)
        assert len(stmt.value.keys) == 2

    def test_lambda(self):
        ast = parse("lambda x => x + 1")
        expr = ast.statements[0].expr
        assert isinstance(expr, LambdaExpr)
        assert len(expr.params) == 1

    def test_pipe(self):
        ast = parse("x |> f")
        expr = ast.statements[0].expr
        assert isinstance(expr, PipeExpr)

    def test_nullish_coalesce(self):
        ast = parse("a ?? b")
        expr = ast.statements[0].expr
        assert isinstance(expr, NullishCoalesceExpr)

    def test_and_or(self):
        ast = parse("a and b or c")
        expr = ast.statements[0].expr
        assert isinstance(expr, BinaryExpr)
        assert expr.op == "or"


class TestControlFlow:
    def test_if_stmt(self):
        ast = parse("if true { let x = 1 }")
        stmt = ast.statements[0]
        assert isinstance(stmt, IfStmt)

    def test_if_else(self):
        ast = parse("if true { } else { }")
        stmt = ast.statements[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.else_body is not None

    def test_if_elif_else(self):
        ast = parse("if true { } elif false { } else { }")
        stmt = ast.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.elif_branches) == 1

    def test_while_loop(self):
        ast = parse("while true { }")
        stmt = ast.statements[0]
        assert isinstance(stmt, WhileStmt)

    def test_for_loop(self):
        ast = parse("for i in range(10) { }")
        stmt = ast.statements[0]
        assert isinstance(stmt, ForStmt)
        assert stmt.var == "i"

    def test_loop(self):
        ast = parse("loop { break }")
        stmt = ast.statements[0]
        assert isinstance(stmt, LoopStmt)

    def test_break(self):
        ast = parse("loop { break }")
        loop = ast.statements[0]
        assert isinstance(loop.body.statements[0], BreakStmt)

    def test_continue(self):
        ast = parse("loop { continue }")
        loop = ast.statements[0]
        assert isinstance(loop.body.statements[0], ContinueStmt)

    def test_return_stmt(self):
        ast = parse("fn f() { return 42 }")
        fn = ast.statements[0]
        ret = fn.body.statements[0]
        assert isinstance(ret, ReturnStmt)

    def test_try_catch(self):
        ast = parse("try { x } catch e { y }")
        stmt = ast.statements[0]
        assert isinstance(stmt, TryStmt)
        assert len(stmt.catch_clauses) == 1


class TestImport:
    def test_import(self):
        ast = parse("import os")
        stmt = ast.statements[0]
        assert isinstance(stmt, ImportDecl)
        assert stmt.module == "os"

    def test_from_import(self):
        ast = parse("from os import path")
        stmt = ast.statements[0]
        assert isinstance(stmt, FromImportDecl)
        assert stmt.module == "os"

    def test_import_alias(self):
        ast = parse("import os as operating_system")
        stmt = ast.statements[0]
        assert isinstance(stmt, ImportDecl)
        assert stmt.alias == "operating_system"


class TestBlock:
    def test_nested_blocks(self):
        ast = parse("fn f() { if true { let x = 1 } }")
        fn = ast.statements[0]
        assert isinstance(fn.body, Block)
        if_stmt = fn.body.statements[0]
        assert isinstance(if_stmt, IfStmt)
