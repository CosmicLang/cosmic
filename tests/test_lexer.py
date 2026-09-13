"""Tests for the Cosmic lexer."""
import pytest
from cosmic.lexer.lexer import tokenize, LexError
from cosmic.lexer.tokens import TokenType


class TestLiterals:
    def test_int_literal(self):
        toks = tokenize("42")
        assert toks[0].type == TokenType.INT_LIT
        assert toks[0].value == 42

    def test_float_literal(self):
        toks = tokenize("3.14")
        assert toks[0].type == TokenType.FLOAT_LIT
        assert toks[0].value == 3.14

    def test_hex_literal(self):
        toks = tokenize("0xFF")
        assert toks[0].type == TokenType.INT_LIT
        assert toks[0].value == 255

    def test_binary_literal(self):
        toks = tokenize("0b1010")
        assert toks[0].type == TokenType.INT_LIT
        assert toks[0].value == 10

    def test_octal_literal(self):
        toks = tokenize("0o17")
        assert toks[0].type == TokenType.INT_LIT
        assert toks[0].value == 15

    def test_string_literal(self):
        toks = tokenize('"hello world"')
        assert toks[0].type == TokenType.STRING_LIT
        assert toks[0].value == "hello world"

    def test_string_escape(self):
        toks = tokenize(r'"line\n\t\\\"end"')
        assert toks[0].value == 'line\n\t\\"end'

    def test_multiline_string(self):
        src = '"""line1\nline2\nline3"""'
        toks = tokenize(src)
        assert toks[0].type == TokenType.STRING_LIT
        assert "line1\nline2\nline3" in toks[0].value

    def test_char_literal(self):
        toks = tokenize('"a"')
        assert toks[0].type == TokenType.STRING_LIT
        assert toks[0].value == "a"

    def test_bool_true(self):
        toks = tokenize("true")
        assert toks[0].type == TokenType.TRUE

    def test_bool_false(self):
        toks = tokenize("false")
        assert toks[0].type == TokenType.FALSE

    def test_none_literal(self):
        toks = tokenize("none")
        assert toks[0].type == TokenType.NONE


class TestKeywords:
    @pytest.mark.parametrize("kw,expected", [
        ("fn", TokenType.FN), ("return", TokenType.RETURN), ("let", TokenType.LET),
        ("var", TokenType.VAR), ("if", TokenType.IF), ("elif", TokenType.ELIF),
        ("else", TokenType.ELSE), ("while", TokenType.WHILE), ("for", TokenType.FOR),
        ("in", TokenType.IN), ("loop", TokenType.LOOP), ("break", TokenType.BREAK),
        ("continue", TokenType.CONTINUE), ("match", TokenType.MATCH),
        ("class", TokenType.CLASS), ("record", TokenType.RECORD),
        ("enum", TokenType.ENUM), ("interface", TokenType.INTERFACE),
        ("import", TokenType.IMPORT), ("from", TokenType.FROM),
        ("as", TokenType.AS), ("pub", TokenType.PUB), ("self", TokenType.SELF),
        ("super", TokenType.SUPER), ("and", TokenType.AND), ("or", TokenType.OR),
        ("not", TokenType.NOT), ("is", TokenType.IS), ("async", TokenType.ASYNC),
        ("await", TokenType.AWAIT), ("lambda", TokenType.LAMBDA),
        ("try", TokenType.TRY), ("catch", TokenType.CATCH),
        ("raise", TokenType.RAISE), ("type", TokenType.TYPE),
        ("const", TokenType.CONST), ("struct", TokenType.STRUCT),
    ])
    def test_keyword(self, kw, expected):
        toks = tokenize(kw)
        assert toks[0].type == expected


class TestOperators:
    @pytest.mark.parametrize("op,expected", [
        ("+", TokenType.PLUS), ("-", TokenType.MINUS), ("*", TokenType.STAR),
        ("/", TokenType.SLASH), ("%", TokenType.PERCENT), ("**", TokenType.POWER),
        ("//", TokenType.FLOOR_DIV), ("==", TokenType.EQ), ("!=", TokenType.NEQ),
        ("<", TokenType.LT), (">", TokenType.GT), ("<=", TokenType.LTE),
        (">=", TokenType.GTE), ("=", TokenType.ASSIGN), ("+=", TokenType.PLUS_ASSIGN),
        ("-=", TokenType.MINUS_ASSIGN), ("*=", TokenType.STAR_ASSIGN),
        ("/=", TokenType.SLASH_ASSIGN), ("&&", TokenType.AND_AND),
        ("||", TokenType.OR_OR), ("!", TokenType.NOT_NOT), ("~", TokenType.BIT_NOT),
        ("<<", TokenType.LSHIFT), (">>", TokenType.RSHIFT), ("->", TokenType.ARROW),
        ("=>", TokenType.DOUBLE_ARROW), ("::", TokenType.DOUBLE_COLON),
        ("??", TokenType.NULLISH), ("...", TokenType.ELLIPSIS),
        ("@", TokenType.AT),
    ])
    def test_operator(self, op, expected):
        toks = tokenize(op)
        assert toks[0].type == expected


class TestDelimiters:
    @pytest.mark.parametrize("ch,expected", [
        ("(", TokenType.LPAREN), (")", TokenType.RPAREN),
        ("{", TokenType.LBRACE), ("}", TokenType.RBRACE),
        ("[", TokenType.LBRACKET), ("]", TokenType.RBRACKET),
        (",", TokenType.COMMA), (";", TokenType.SEMICOLON),
        (":", TokenType.COLON), (".", TokenType.DOT),
        ("?", TokenType.QUESTION),
    ])
    def test_delimiter(self, ch, expected):
        toks = tokenize(ch)
        assert toks[0].type == expected


class TestComments:
    def test_hash_comment(self):
        toks = tokenize("# this is a comment\n42")
        ints = [t for t in toks if t.type == TokenType.INT_LIT]
        assert len(ints) == 1
        assert ints[0].value == 42

    def test_block_comment(self):
        toks = tokenize("42 /* block\ncomment */ 10")
        ints = [t for t in toks if t.type == TokenType.INT_LIT]
        assert len(ints) == 2

    def test_hashbang(self):
        toks = tokenize("#!/usr/bin/env cosmic\n42")
        ints = [t for t in toks if t.type == TokenType.INT_LIT]
        assert len(ints) == 1


class TestIdentifiers:
    def test_simple_ident(self):
        toks = tokenize("myVar")
        assert toks[0].type == TokenType.IDENT
        assert toks[0].value == "myVar"

    def test_underscore(self):
        toks = tokenize("_private")
        assert toks[0].type == TokenType.IDENT
        assert toks[0].value == "_private"

    def test_underscore_digits(self):
        toks = tokenize("var_123")
        assert toks[0].type == TokenType.IDENT
        assert toks[0].value == "var_123"


class TestSourceLocation:
    def test_line_tracking(self):
        toks = tokenize("a\nb\nc")
        assert toks[0].line == 1
        assert toks[1].line == 2
        assert toks[2].line == 3

    def test_column_tracking(self):
        toks = tokenize("   x")
        assert toks[0].column == 4

    def test_eof_token(self):
        toks = tokenize("42")
        assert toks[-1].type == TokenType.EOF


class TestComplex:
    def test_function_def(self):
        src = "fn add(a: int, b: int) -> int { return a + b }"
        toks = tokenize(src)
        types = [t.type for t in toks if t.type != TokenType.EOF]
        assert TokenType.FN in types
        assert TokenType.RETURN in types
        assert TokenType.ARROW in types

    def test_string_interpolation_braces(self):
        toks = tokenize('"{{escaped}}"')
        assert toks[0].value == "{{escaped}}"
