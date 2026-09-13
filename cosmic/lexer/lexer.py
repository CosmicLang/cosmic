"""Lexer/Tokenizer for the Cosmic language."""
from __future__ import annotations
from .tokens import Token, TokenType, KEYWORDS, SINGLE_CHAR_TOKENS, KEYWORD_LIST
from dataclasses import dataclass
from typing import Iterator


class LexError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


@dataclass
class Lexer:
    source: str
    filename: str = "<stdin>"
    pos: int = 0
    line: int = 1
    column: int = 1
    indent_stack: list[int] = None
    paren_depth: int = 0
    bracket_depth: int = 0
    brace_depth: int = 0
    pending_dedents: int = 0
    at_line_start: bool = True

    def __post_init__(self):
        if self.indent_stack is None:
            self.indent_stack = [0]

    def error(self, msg: str) -> LexError:
        return LexError(msg, self.line, self.column)

    def peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return '\0'

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.source[self.pos:self.pos + len(expected)] == expected:
            for _ in expected:
                self.advance()
            return True
        return False

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.advance()

    def skip_comment(self) -> bool:
        if self.match('//'):
            while self.pos < len(self.source) and self.source[self.pos] != '\n':
                self.advance()
            return True
        if self.match('/*'):
            depth = 1
            while depth > 0 and self.pos < len(self.source):
                if self.match('/*'):
                    depth += 1
                elif self.match('*/'):
                    depth -= 1
                else:
                    self.advance()
            return True
        return False

    def read_string(self, quote: str) -> Token:
        start_line, start_col = self.line, self.column
        self.advance()
        parts: list[str] = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == quote:
                self.advance()
                value = ''.join(parts)
                return Token(TokenType.STRING_LIT, value, start_line, start_col, len(value) + 2)
            if ch == '\\':
                self.advance()
                escape = self.advance()
                escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '0': '\0', "'": "'", '"': '"'}
                parts.append(escape_map.get(escape, escape))
            elif ch == '{' and self.peek(1) == '{':
                parts.append('{{')
                self.advance()
                self.advance()
            elif ch == '}' and self.peek(1) == '}':
                parts.append('}}')
                self.advance()
                self.advance()
            else:
                parts.append(ch)
                self.advance()
        raise self.error("Unterminated string literal")

    def read_char(self) -> Token:
        start_line, start_col = self.line, self.column
        self.advance()
        if self.peek() == '\\':
            self.advance()
            escape = self.advance()
            escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '0': '\0', "'": "'"}
            ch = escape_map.get(escape, escape)
        else:
            ch = self.advance()
        if self.peek() != "'":
            raise self.error("Unterminated character literal")
        self.advance()
        return Token(TokenType.CHAR_LIT, ch, start_line, start_col, 3)

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.column
        has_dot = False
        is_hex = False
        is_bin = False
        is_oct = False

        if self.peek() == '0' and self.peek(1) in 'xX':
            is_hex = True
            self.advance()
            self.advance()
        elif self.peek() == '0' and self.peek(1) in 'bB':
            is_bin = True
            self.advance()
            self.advance()
        elif self.peek() == '0' and self.peek(1) in 'oO':
            is_oct = True
            self.advance()
            self.advance()

        digits = []
        if is_hex:
            while self.pos < len(self.source) and self.source[self.pos] in '0123456789abcdefABCDEF_':
                if self.source[self.pos] != '_':
                    digits.append(self.source[self.pos])
                self.advance()
        elif is_bin:
            while self.pos < len(self.source) and self.source[self.pos] in '01_':
                if self.source[self.pos] != '_':
                    digits.append(self.source[self.pos])
                self.advance()
        elif is_oct:
            while self.pos < len(self.source) and self.source[self.pos] in '01234567_':
                if self.source[self.pos] != '_':
                    digits.append(self.source[self.pos])
                self.advance()
        else:
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                digits.append(self.source[self.pos])
                self.advance()
            if self.peek() == '.' and self.peek(1) != '.':
                has_dot = True
                digits.append('.')
                self.advance()
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    digits.append(self.source[self.pos])
                    self.advance()

        num_str = ''.join(digits)

        if self.peek() in 'eE' and not is_hex and not is_bin and not is_oct:
            has_dot = True
            num_str += self.advance()
            if self.peek() in '+-':
                num_str += self.advance()
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                num_str += self.source[self.pos]
                self.advance()

        suffix = ''
        if self.peek() in 'fF':
            suffix = self.advance()
        elif self.peek() in 'lL':
            suffix = self.advance()

        raw = num_str + suffix
        col_length = self.column - start_col

        if has_dot or suffix in ('f', 'F'):
            value = float(num_str)
            return Token(TokenType.FLOAT_LIT, value, start_line, start_col, col_length)
        else:
            base = 16 if is_hex else (2 if is_bin else (8 if is_oct else 10))
            value = int(num_str, base)
            return Token(TokenType.INT_LIT, value, start_line, start_col, col_length)

    def read_ident_or_keyword(self) -> Token:
        start_line, start_col = self.line, self.column
        chars = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            chars.append(self.source[self.pos])
            self.advance()
        word = ''.join(chars)
        length = self.column - start_col

        if word in KEYWORDS:
            return Token(KEYWORDS[word], word, start_line, start_col, length)
        if word == 'true':
            return Token(TokenType.BOOL_LIT, True, start_line, start_col, length)
        if word == 'false':
            return Token(TokenType.BOOL_LIT, False, start_line, start_col, length)
        if word == 'none':
            return Token(TokenType.NONE_LIT, None, start_line, start_col, length)
        if word == 'self':
            return Token(TokenType.SELF, 'self', start_line, start_col, length)
        if word == 'super':
            return Token(TokenType.SUPER, 'super', start_line, start_col, length)
        if word == 'and':
            return Token(TokenType.AND, 'and', start_line, start_col, length)
        if word == 'or':
            return Token(TokenType.OR, 'or', start_line, start_col, length)
        if word == 'not':
            return Token(TokenType.NOT, 'not', start_line, start_col, length)
        if word == 'is':
            return Token(TokenType.IS, 'is', start_line, start_col, length)
        if word == 'in':
            return Token(TokenType.IN, 'in', start_line, start_col, length)
        if word == 'as':
            return Token(TokenType.AS, 'as', start_line, start_col, length)
        if word == 'self':
            return Token(TokenType.SELF, 'self', start_line, start_col, length)
        if word == 'super':
            return Token(TokenType.SUPER, 'super', start_line, start_col, length)
        if word == 'self':
            return Token(TokenType.SELF, 'self', start_line, start_col, length)
        if word == 'super':
            return Token(TokenType.SUPER, 'super', start_line, start_col, length)

        return Token(TokenType.IDENT, word, start_line, start_col, length)

    def handle_newline(self) -> Iterator[Token]:
        start_line = self.line
        self.advance()
        self.at_line_start = True

        if self.paren_depth > 0 or self.bracket_depth > 0 or self.brace_depth > 0:
            return

        current_indent = 0
        while self.pos < len(self.source) and self.source[self.pos] in ' \t':
            if self.source[self.pos] == ' ':
                current_indent += 1
            else:
                current_indent += 4
            self.advance()

        while self.pos < len(self.source) and self.source[self.pos] == '#':
            while self.pos < len(self.source) and self.source[self.pos] != '\n':
                self.advance()
            if self.pos < len(self.source):
                self.advance()
            current_indent = 0
            while self.pos < len(self.source) and self.source[self.pos] in ' \t':
                if self.source[self.pos] == ' ':
                    current_indent += 1
                else:
                    current_indent += 4
                self.advance()

        if current_indent == self.indent_stack[-1]:
            return

        if current_indent > self.indent_stack[-1]:
            self.indent_stack.append(current_indent)
            yield Token(TokenType.LBRACE, '{', start_line, 1, 1)
        else:
            while current_indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.pending_dedents += 1
                yield Token(TokenType.RBRACE, '}', start_line, 1, 1)

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            if self.source[self.pos] == '\n':
                if self.paren_depth == 0 and self.bracket_depth == 0:
                    for tok in self.handle_newline():
                        tokens.append(tok)
                    self.at_line_start = True
                    continue
                else:
                    self.advance()
                    continue

            if self.source[self.pos] == '#':
                if self.peek(1) == '!':
                    while self.pos < len(self.source) and self.source[self.pos] != '\n':
                        self.advance()
                    continue
                if not self.skip_comment():
                    self.advance()
                    while self.pos < len(self.source) and self.source[self.pos] != '\n':
                        self.advance()
                continue

            start_line, start_col = self.line, self.column

            if self.source[self.pos] == '"':
                if self.peek(1) == '"' and self.peek(2) == '"':
                    self.advance(); self.advance(); self.advance()
                    parts = []
                    while self.pos < len(self.source):
                        if self.source[self.pos:self.pos + 3] == '"""':
                            self.advance(); self.advance(); self.advance()
                            break
                        parts.append(self.advance())
                    tokens.append(Token(TokenType.STRING_LIT, ''.join(parts), start_line, start_col, 0))
                    continue
                tokens.append(self.read_string('"'))
                continue
            if self.source[self.pos] == "'":
                if self.peek(1) == "'" and self.peek(2) == "'":
                    self.advance(); self.advance(); self.advance()
                    parts = []
                    while self.pos < len(self.source):
                        if self.source[self.pos:self.pos + 3] == "'''":
                            self.advance(); self.advance(); self.advance()
                            break
                        parts.append(self.advance())
                    tokens.append(Token(TokenType.STRING_LIT, ''.join(parts), start_line, start_col, 0))
                    continue
                if self.peek(1) == "'":
                    raise self.error("Empty character literal")
                tokens.append(self.read_string("'"))
                continue

            if self.source[self.pos].isdigit() or (self.source[self.pos] == '.' and self.peek(1).isdigit()):
                tokens.append(self.read_number())
                continue

            if self.source[self.pos].isalpha() or self.source[self.pos] == '_':
                tokens.append(self.read_ident_or_keyword())
                continue

            ch = self.source[self.pos]

            two = self.source[self.pos:self.pos + 2]
            three = self.source[self.pos:self.pos + 3]
            op_map = {
                '==': TokenType.EQ, '!=': TokenType.NEQ,
                '<=': TokenType.LTE, '>=': TokenType.GTE,
                '->': TokenType.ARROW, '=>': TokenType.DOUBLE_ARROW,
                '::': TokenType.DOUBLE_COLON, '||': TokenType.OR_OR,
                '??': TokenType.NULLISH, '&&': TokenType.AND_AND,
                '**': TokenType.POWER, '//': TokenType.FLOOR_DIV,
                '+=': TokenType.PLUS_ASSIGN, '-=': TokenType.MINUS_ASSIGN,
                '*=': TokenType.STAR_ASSIGN, '/=': TokenType.SLASH_ASSIGN,
                '%=': TokenType.PERCENT_ASSIGN, '**=': TokenType.POWER_ASSIGN,
                '<<': TokenType.LSHIFT,                 '>>': TokenType.RSHIFT,
                '|>': TokenType.PIPE,
                '...': TokenType.ELLIPSIS, '..<': TokenType.ELLIPSIS,
            }
            if len(three) == 3 and three in op_map:
                self.advance(); self.advance(); self.advance()
                tokens.append(Token(op_map[three], three, start_line, start_col, 3))
                continue
            if two in op_map:
                self.advance(); self.advance()
                tokens.append(Token(op_map[two], two, start_line, start_col, 2))
                continue

            if ch in SINGLE_CHAR_TOKENS:
                tok_type = SINGLE_CHAR_TOKENS[ch]
                if ch == '(':
                    self.paren_depth += 1
                elif ch == ')':
                    self.paren_depth = max(0, self.paren_depth - 1)
                elif ch == '[':
                    self.bracket_depth += 1
                elif ch == ']':
                    self.bracket_depth = max(0, self.bracket_depth - 1)
                elif ch == '{':
                    self.brace_depth += 1
                elif ch == '}':
                    self.brace_depth = max(0, self.brace_depth - 1)
                self.advance()
                tokens.append(Token(tok_type, ch, start_line, start_col, 1))
                continue

            single_ops = {
                '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
                '/': TokenType.SLASH, '%': TokenType.PERCENT,
                '=': TokenType.ASSIGN, '<': TokenType.LT, '>': TokenType.GT,
                '&': TokenType.BIT_AND, '|': TokenType.BIT_OR,
                '^': TokenType.BIT_XOR, '~': TokenType.BIT_NOT,
                '!': TokenType.NOT_NOT, '?': TokenType.QUESTION,
                ':': TokenType.COLON, ';': TokenType.SEMICOLON,
                ',': TokenType.COMMA, '.': TokenType.DOT,
                '@': TokenType.AT, '#': TokenType.HASH,
                '$': TokenType.DOLLAR,
            }
            if ch in single_ops:
                self.advance()
                tokens.append(Token(single_ops[ch], ch, start_line, start_col, 1))
                continue

            raise self.error(f"Unexpected character: {ch!r}")

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.RBRACE, '}', self.line, self.column, 1))

        tokens.append(Token(TokenType.EOF, None, self.line, self.column, 0))
        return tokens


def tokenize(source: str, filename: str = "<stdin>") -> list[Token]:
    return Lexer(source, filename).tokenize()
