"""Token types for the Cosmic language."""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Literals
    INT_LIT = auto()
    FLOAT_LIT = auto()
    STRING_LIT = auto()
    BOOL_LIT = auto()
    NONE_LIT = auto()
    CHAR_LIT = auto()
    BYTE_LIT = auto()

    # Identifiers
    IDENT = auto()

    # Keywords
    FN = auto()
    RETURN = auto()
    LET = auto()
    MUT = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    LOOP = auto()
    BREAK = auto()
    CONTINUE = auto()
    MATCH = auto()
    CLASS = auto()
    RECORD = auto()
    ENUM = auto()
    EXTENDS = auto()
    IMPLS = auto()
    INTERFACE = auto()
    TRAIT = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    MODULE = auto()
    PUB = auto()
    PRIV = auto()
    STATIC = auto()
    FINAL = auto()
    ASSERT = auto()
    TEST = auto()
    SELF = auto()
    SUPER = auto()
    TRUE = auto()
    FALSE = auto()
    NONE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IS = auto()
    ASYNC = auto()
    AWAIT = auto()
    LAMBDA = auto()
    TRY = auto()
    CATCH = auto()
    RAISE = auto()
    YIELD = auto()
    FINALLY = auto()
    TYPEOF = auto()
    STRUCT = auto()
    UNION = auto()
    TYPE = auto()
    CONST = auto()
    WHERE = auto()
    VAR = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    POWER = auto()
    FLOOR_DIV = auto()
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()
    PERCENT_ASSIGN = auto()
    POWER_ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()
    BIT_NOT = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    ARROW = auto()
    DOUBLE_ARROW = auto()
    PIPE = auto()
    NULLISH = auto()
    AND_AND = auto()
    OR_OR = auto()
    NOT_NOT = auto()
    SPREAD = auto()
    AT = auto()
    DOLLAR = auto()
    HASH = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    DOUBLE_COLON = auto()
    DOT = auto()
    QUESTION = auto()
    ELLIPSIS = auto()
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    'fn': TokenType.FN,
    'return': TokenType.RETURN,
    'let': TokenType.LET,
    'mut': TokenType.MUT,
    'if': TokenType.IF,
    'elif': TokenType.ELIF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'for': TokenType.FOR,
    'in': TokenType.IN,
    'loop': TokenType.LOOP,
    'break': TokenType.BREAK,
    'continue': TokenType.CONTINUE,
    'match': TokenType.MATCH,
    'class': TokenType.CLASS,
    'record': TokenType.RECORD,
    'enum': TokenType.ENUM,
    'extends': TokenType.EXTENDS,
    'impls': TokenType.IMPLS,
    'interface': TokenType.INTERFACE,
    'trait': TokenType.TRAIT,
    'import': TokenType.IMPORT,
    'from': TokenType.FROM,
    'as': TokenType.AS,
    'module': TokenType.MODULE,
    'pub': TokenType.PUB,
    'priv': TokenType.PRIV,
    'static': TokenType.STATIC,
    'final': TokenType.FINAL,
    'assert': TokenType.ASSERT,
    'test': TokenType.TEST,
    'self': TokenType.SELF,
    'super': TokenType.SUPER,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'none': TokenType.NONE,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
    'is': TokenType.IS,
    'async': TokenType.ASYNC,
    'await': TokenType.AWAIT,
    'lambda': TokenType.LAMBDA,
    'try': TokenType.TRY,
    'catch': TokenType.CATCH,
    'raise': TokenType.RAISE,
    'yield': TokenType.YIELD,
    'finally': TokenType.FINALLY,
    'typeof': TokenType.TYPEOF,
    'struct': TokenType.STRUCT,
    'union': TokenType.UNION,
    'type': TokenType.TYPE,
    'const': TokenType.CONST,
    'where': TokenType.WHERE,
    'var': TokenType.VAR,
}

SINGLE_CHAR_TOKENS = {
    '(': TokenType.LPAREN,
    ')': TokenType.RPAREN,
    '{': TokenType.LBRACE,
    '}': TokenType.RBRACE,
    '[': TokenType.LBRACKET,
    ']': TokenType.RBRACKET,
    ',': TokenType.COMMA,
    ';': TokenType.SEMICOLON,
    ':': TokenType.COLON,
    '.': TokenType.DOT,
    '?': TokenType.QUESTION,
    '@': TokenType.AT,
    '#': TokenType.HASH,
    '$': TokenType.DOLLAR,
}

KEYWORD_LIST = sorted(KEYWORDS.keys(), key=len, reverse=True)


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    line: int
    column: int
    length: int = 1

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.column})"
