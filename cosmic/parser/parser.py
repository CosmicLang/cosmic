"""Parser for the Cosmic language. Recursive descent + Pratt for expressions."""
from __future__ import annotations
from ..lexer.tokens import Token, TokenType
from ..ast.nodes import (
    ASTNode, AsExpr, AssertStmt, AssignStmt, AugAssignStmt, AwaitExpr,
    BinaryExpr, Block, BoolLiteral, BreakStmt, CallExpr, CatchClause,
    CharLiteral, ClassDecl, ContinueStmt, DictExpr, EnumDecl, EnumVariant,
    ExprStmt, FloatLiteral, FnDecl, ForStmt, FromImportDecl, Identifier,
    IfExpr, IfStmt, ImportDecl, IndexExpr, IntLiteral, InterfaceDecl,
    IsExpr, LambdaExpr, LetStmt, ListExpr, LoopStmt, MatchCase, MatchExpr,
    ModuleDecl, NoneLiteral, NullishCoalesceExpr, Param, PipeExpr, Program,
    PropertyAccessExpr, RaiseStmt, RecordDecl, ReturnStmt, SelfExpr,
    SliceExpr, SpreadExpr, StringLiteral, SuperExpr, TestDecl, TryStmt,
    TupleExpr, TypeAlias, TypeOfExpr, TypeRef, UnaryExpr, WhileStmt,
    YieldExpr,
)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"Line {token.line}, Column {token.column}: {message}")


PRECEDENCE = {
    TokenType.OR: 1,
    TokenType.OR_OR: 1,
    TokenType.AND: 2,
    TokenType.AND_AND: 2,
    TokenType.PIPE: 3,
    TokenType.NULLISH: 4,
    TokenType.EQ: 5, TokenType.NEQ: 5,
    TokenType.LT: 6, TokenType.GT: 6,
    TokenType.LTE: 6, TokenType.GTE: 6,
    TokenType.IS: 6, TokenType.AS: 6,
    TokenType.BIT_OR: 7,
    TokenType.BIT_XOR: 8,
    TokenType.BIT_AND: 9,
    TokenType.LSHIFT: 10, TokenType.RSHIFT: 10,
    TokenType.PLUS: 11, TokenType.MINUS: 11,
    TokenType.STAR: 12, TokenType.SLASH: 12,
    TokenType.PERCENT: 12, TokenType.FLOOR_DIV: 12,
    TokenType.POWER: 13,
}


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<stdin>"):
        self.tokens = tokens
        self.pos = 0
        self.filename = filename

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, type: TokenType, msg: str = "") -> Token:
        tok = self.peek()
        if tok.type != type:
            raise ParseError(msg or f"Expected {type.name}, got {tok.type.name}", tok)
        return self.advance()

    def match(self, *types: TokenType) -> bool:
        return self.peek().type in types

    def at(self, *types: TokenType) -> bool:
        return self.peek().type in types

    def consume(self, *types: TokenType) -> Token | None:
        if self.peek().type in types:
            return self.advance()
        return None

    def error(self, msg: str) -> ParseError:
        return ParseError(msg, self.peek())

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            self.advance()

    def parse(self) -> Program:
        stmts = []
        while not self.at(TokenType.EOF):
            self.skip_newlines()
            if self.at(TokenType.EOF):
                break
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
        return Program(statements=stmts, filename=self.filename)

    def parse_statement(self) -> ASTNode:
        self.skip_newlines()
        tok = self.peek()

        if tok.type == TokenType.FN or tok.type == TokenType.ASYNC or tok.type == TokenType.STATIC:
            return self.parse_fn_decl()
        if tok.type == TokenType.PUB:
            next_type = self.peek(1).type
            if next_type == TokenType.FN or next_type == TokenType.ASYNC or next_type == TokenType.STATIC:
                return self.parse_fn_decl()
            if next_type == TokenType.CLASS:
                return self.parse_class_decl()
            if next_type == TokenType.RECORD:
                return self.parse_record_decl()
            if next_type == TokenType.ENUM:
                return self.parse_enum_decl()
            if next_type == TokenType.INTERFACE:
                return self.parse_interface_decl()
            if next_type == TokenType.TYPE:
                return self.parse_type_alias()
            return self.parse_fn_decl()
        if tok.type == TokenType.CLASS:
            return self.parse_class_decl()
        if tok.type == TokenType.RECORD:
            return self.parse_record_decl()
        if tok.type == TokenType.ENUM:
            return self.parse_enum_decl()
        if tok.type == TokenType.INTERFACE:
            return self.parse_interface_decl()
        if tok.type == TokenType.TYPE:
            return self.parse_type_alias()
        if tok.type == TokenType.IMPORT:
            return self.parse_import()
        if tok.type == TokenType.FROM:
            return self.parse_from_import()
        if tok.type == TokenType.MODULE:
            return self.parse_module_decl()
        if tok.type == TokenType.TEST:
            return self.parse_test_decl()
        if tok.type == TokenType.CONST:
            return self.parse_const_decl()
        if tok.type == TokenType.LET or tok.type == TokenType.VAR:
            return self.parse_let_stmt()
        if tok.type == TokenType.IF:
            return self.parse_if_stmt()
        if tok.type == TokenType.WHILE:
            return self.parse_while_stmt()
        if tok.type == TokenType.FOR:
            return self.parse_for_stmt()
        if tok.type == TokenType.LOOP:
            return self.parse_loop_stmt()
        if tok.type == TokenType.RETURN:
            return self.parse_return_stmt()
        if tok.type == TokenType.BREAK:
            return self.parse_break_stmt()
        if tok.type == TokenType.CONTINUE:
            return self.parse_continue_stmt()
        if tok.type == TokenType.RAISE:
            return self.parse_raise_stmt()
        if tok.type == TokenType.TRY:
            return self.parse_try_stmt()
        if tok.type == TokenType.MATCH:
            return self.parse_match_expr()
        if tok.type == TokenType.ASSERT:
            return self.parse_assert_stmt()
        if tok.type == TokenType.LBRACE:
            return self.parse_block()
        if tok.type == TokenType.NEWLINE:
            self.advance()
            return None
        return self.parse_expr_stmt()

    def parse_fn_decl(self) -> FnDecl:
        is_pub = False
        is_async = False
        is_static = False
        for _ in range(3):
            if self.match(TokenType.PUB):
                is_pub = True
                self.advance()
            elif self.match(TokenType.ASYNC):
                is_async = True
                self.advance()
            elif self.match(TokenType.STATIC):
                is_static = True
                self.advance()
            else:
                break
        tok = self.expect(TokenType.FN)

        name_tok = self.expect(TokenType.IDENT, "Expected function name")
        params = self.parse_params()

        return_type = None
        if self.match(TokenType.COLON):
            self.advance()
            return_type = self.parse_type_ref()
        elif self.match(TokenType.ARROW):
            self.advance()
            return_type = self.parse_type_ref()

        body = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            body = self.parse_expression()
        elif self.at(TokenType.LBRACE):
            body = self.parse_block()

        return FnDecl(
            name=name_tok.value,
            params=params,
            return_type=return_type,
            body=body,
            is_async=is_async,
            is_pub=is_pub,
            is_static=is_static,
            line=tok.line,
            column=tok.column,
        )

    def parse_params(self) -> list[Param]:
        params = []
        self.expect(TokenType.LPAREN, "Expected '('")
        if self.match(TokenType.RPAREN):
            self.advance()
            return params
        while not self.at(TokenType.RPAREN):
            params.append(self.parse_param())
            if self.match(TokenType.COMMA):
                self.advance()
        self.expect(TokenType.RPAREN, "Expected ')'")
        return params

    def parse_param(self) -> Param:
        tok = self.expect(TokenType.IDENT, "Expected parameter name")
        name = tok.value
        type_ref = None
        default = None
        if self.match(TokenType.COLON):
            self.advance()
            type_ref = self.parse_type_ref()
        if self.match(TokenType.ASSIGN):
            self.advance()
            default = self.parse_expression()
        return Param(name=name, type_ref=type_ref, default=default, line=tok.line, column=tok.column)

    def parse_class_decl(self) -> ClassDecl:
        is_pub = False
        if self.match(TokenType.PUB):
            is_pub = True
            self.advance()
        tok = self.expect(TokenType.CLASS)
        name_tok = self.expect(TokenType.IDENT, "Expected class name")
        bases = []
        if self.match(TokenType.EXTENDS):
            self.advance()
            bases.append(self.parse_type_ref())
            while self.match(TokenType.COMMA):
                self.advance()
                bases.append(self.parse_type_ref())
        body = self.parse_block()
        return ClassDecl(
            name=name_tok.value,
            bases=bases,
            body=body,
            is_pub=is_pub,
            line=tok.line,
            column=tok.column,
        )

    def parse_record_decl(self) -> RecordDecl:
        is_pub = False
        if self.match(TokenType.PUB):
            is_pub = True
            self.advance()
        tok = self.expect(TokenType.RECORD)
        name_tok = self.expect(TokenType.IDENT, "Expected record name")
        fields = self.parse_params()
        methods = []
        if self.at(TokenType.LBRACE):
            body = self.parse_block()
            if isinstance(body, Block):
                for stmt in body.statements:
                    if isinstance(stmt, FnDecl):
                        methods.append(stmt)
        return RecordDecl(
            name=name_tok.value,
            fields=fields,
            methods=methods,
            is_pub=is_pub,
            line=tok.line,
            column=tok.column,
        )

    def parse_enum_decl(self) -> EnumDecl:
        is_pub = False
        if self.match(TokenType.PUB):
            is_pub = True
            self.advance()
        tok = self.expect(TokenType.ENUM)
        name_tok = self.expect(TokenType.IDENT, "Expected enum name")
        self.expect(TokenType.LBRACE, "Expected '{'")
        variants = []
        while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
            vtok = self.expect(TokenType.IDENT, "Expected variant name")
            fields = []
            value = None
            if self.match(TokenType.LPAREN):
                fields = self.parse_type_list_in_parens()
            elif self.match(TokenType.ASSIGN):
                self.advance()
                value = self.parse_expression()
            variants.append(EnumVariant(name=vtok.value, fields=fields, value=value, line=vtok.line, column=vtok.column))
            if self.match(TokenType.COMMA):
                self.advance()
        self.expect(TokenType.RBRACE, "Expected '}'")
        return EnumDecl(name=name_tok.value, variants=variants, is_pub=is_pub, line=tok.line, column=tok.column)

    def parse_type_list_in_parens(self) -> list[TypeRef]:
        self.expect(TokenType.LPAREN)
        types = []
        if not self.at(TokenType.RPAREN):
            types.append(self.parse_type_ref())
            while self.match(TokenType.COMMA):
                self.advance()
                types.append(self.parse_type_ref())
        self.expect(TokenType.RPAREN)
        return types

    def parse_interface_decl(self) -> InterfaceDecl:
        is_pub = False
        if self.match(TokenType.PUB):
            is_pub = True
            self.advance()
        tok = self.expect(TokenType.INTERFACE)
        name_tok = self.expect(TokenType.IDENT, "Expected interface name")
        self.expect(TokenType.LBRACE, "Expected '{'")
        methods = []
        while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
            if self.at(TokenType.FN):
                methods.append(self.parse_fn_decl())
            else:
                self.advance()
        self.expect(TokenType.RBRACE, "Expected '}'")
        return InterfaceDecl(name=name_tok.value, methods=methods, is_pub=is_pub, line=tok.line, column=tok.column)

    def parse_type_alias(self) -> TypeAlias:
        is_pub = False
        if self.match(TokenType.PUB):
            is_pub = True
            self.advance()
        tok = self.expect(TokenType.TYPE)
        name_tok = self.expect(TokenType.IDENT, "Expected type name")
        self.expect(TokenType.ASSIGN, "Expected '='")
        type_ref = self.parse_type_ref()
        return TypeAlias(name=name_tok.value, type_ref=type_ref, is_pub=is_pub, line=tok.line, column=tok.column)

    def parse_import(self) -> ImportDecl:
        tok = self.expect(TokenType.IMPORT)
        module_parts = [self.expect(TokenType.IDENT, "Expected module name").value]
        while self.match(TokenType.DOT):
            self.advance()
            module_parts.append(self.expect(TokenType.IDENT, "Expected module name").value)
        module = '.'.join(module_parts)
        alias = None
        if self.match(TokenType.AS):
            self.advance()
            alias = self.expect(TokenType.IDENT, "Expected alias").value
        return ImportDecl(module=module, names=[module.split('.')[0]], alias=alias, line=tok.line, column=tok.column)

    def parse_from_import(self) -> FromImportDecl:
        tok = self.expect(TokenType.FROM)
        module_parts = [self.expect(TokenType.IDENT, "Expected module name").value]
        while self.match(TokenType.DOT):
            self.advance()
            module_parts.append(self.expect(TokenType.IDENT, "Expected module name").value)
        module = '.'.join(module_parts)
        self.expect(TokenType.IMPORT, "Expected 'import'")
        names = []
        name_tok = self.expect(TokenType.IDENT, "Expected imported name")
        alias = None
        if self.match(TokenType.AS):
            self.advance()
            alias = self.expect(TokenType.IDENT, "Expected alias").value
        names.append((name_tok.value, alias))
        while self.match(TokenType.COMMA):
            self.advance()
            name_tok = self.expect(TokenType.IDENT, "Expected imported name")
            alias = None
            if self.match(TokenType.AS):
                self.advance()
                alias = self.expect(TokenType.IDENT, "Expected alias").value
            names.append((name_tok.value, alias))
        return FromImportDecl(module=module, names=names, line=tok.line, column=tok.column)

    def parse_module_decl(self) -> ModuleDecl:
        tok = self.expect(TokenType.MODULE)
        name_tok = self.expect(TokenType.IDENT, "Expected module name")
        self.expect(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
            self.skip_newlines()
            if self.at(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
        self.expect(TokenType.RBRACE, "Expected '}'")
        return ModuleDecl(name=name_tok.value, body=stmts, line=tok.line, column=tok.column)

    def parse_test_decl(self) -> TestDecl:
        tok = self.expect(TokenType.TEST)
        name_tok = self.expect(TokenType.STRING_LIT, "Expected test name")
        body = self.parse_block()
        return TestDecl(name=name_tok.value, body=body, line=tok.line, column=tok.column)

    def parse_const_decl(self) -> LetStmt:
        tok = self.expect(TokenType.CONST)
        name_tok = self.expect(TokenType.IDENT, "Expected constant name")
        type_ref = None
        if self.match(TokenType.COLON):
            self.advance()
            type_ref = self.parse_type_ref()
        self.expect(TokenType.ASSIGN, "Expected '='")
        value = self.parse_expression()
        return LetStmt(name=name_tok.value, type_ref=type_ref, value=value, mutable=False, line=tok.line, column=tok.column)

    def parse_let_stmt(self) -> LetStmt:
        tok = self.advance()
        mutable = tok.type == TokenType.VAR
        name_tok = self.expect(TokenType.IDENT, "Expected variable name")
        type_ref = None
        if self.match(TokenType.COLON):
            self.advance()
            type_ref = self.parse_type_ref()
        value = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            value = self.parse_expression()
        return LetStmt(name=name_tok.value, type_ref=type_ref, value=value, mutable=mutable, line=tok.line, column=tok.column)

    def parse_if_stmt(self) -> IfStmt:
        tok = self.expect(TokenType.IF)
        condition = self.parse_expression()
        then_body = self.parse_block()
        elif_branches = []
        else_body = None
        while self.match(TokenType.ELIF):
            self.advance()
            elif_cond = self.parse_expression()
            elif_body = self.parse_block()
            elif_branches.append((elif_cond, elif_body))
        if self.match(TokenType.ELSE):
            self.advance()
            else_body = self.parse_block()
        return IfStmt(
            condition=condition,
            then_body=then_body,
            elif_branches=elif_branches,
            else_body=else_body,
            line=tok.line,
            column=tok.column,
        )

    def parse_while_stmt(self) -> WhileStmt:
        tok = self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileStmt(condition=condition, body=body, line=tok.line, column=tok.column)

    def parse_for_stmt(self) -> ForStmt:
        tok = self.expect(TokenType.FOR)
        var_tok = self.expect(TokenType.IDENT, "Expected variable name")
        self.expect(TokenType.IN, "Expected 'in'")
        iter_expr = self.parse_expression()
        body = self.parse_block()
        return ForStmt(var=var_tok.value, iter_expr=iter_expr, body=body, line=tok.line, column=tok.column)

    def parse_loop_stmt(self) -> LoopStmt:
        tok = self.expect(TokenType.LOOP)
        body = self.parse_block()
        return LoopStmt(body=body, line=tok.line, column=tok.column)

    def parse_return_stmt(self) -> ReturnStmt:
        tok = self.expect(TokenType.RETURN)
        value = None
        if not self.at(TokenType.NEWLINE) and not self.at(TokenType.EOF) and not self.at(TokenType.RBRACE):
            value = self.parse_expression()
        return ReturnStmt(value=value, line=tok.line, column=tok.column)

    def parse_break_stmt(self) -> BreakStmt:
        tok = self.expect(TokenType.BREAK)
        value = None
        if not self.at(TokenType.NEWLINE) and not self.at(TokenType.EOF) and not self.at(TokenType.RBRACE):
            value = self.parse_expression()
        return BreakStmt(value=value, line=tok.line, column=tok.column)

    def parse_continue_stmt(self) -> ContinueStmt:
        tok = self.expect(TokenType.CONTINUE)
        return ContinueStmt(line=tok.line, column=tok.column)

    def parse_raise_stmt(self) -> RaiseStmt:
        tok = self.expect(TokenType.RAISE)
        value = None
        if not self.at(TokenType.NEWLINE) and not self.at(TokenType.EOF) and not self.at(TokenType.RBRACE):
            value = self.parse_expression()
        return RaiseStmt(value=value, line=tok.line, column=tok.column)

    def parse_try_stmt(self) -> TryStmt:
        tok = self.expect(TokenType.TRY)
        body = self.parse_block()
        catch_clauses = []
        finally_body = None
        while self.match(TokenType.CATCH):
            clause_tok = self.advance()
            type_ref = None
            var_name = None
            if not self.at(TokenType.LBRACE):
                type_ref = self.parse_type_ref()
                if self.match(TokenType.IDENT):
                    var_name = self.advance().value
            clause_body = self.parse_block()
            catch_clauses.append(CatchClause(type_ref=type_ref, var_name=var_name, body=clause_body, line=clause_tok.line, column=clause_tok.column))
        if self.match(TokenType.FINALLY):
            self.advance()
            finally_body = self.parse_block()
        return TryStmt(body=body, catch_clauses=catch_clauses, finally_body=finally_body, line=tok.line, column=tok.column)

    def parse_assert_stmt(self) -> AssertStmt:
        tok = self.expect(TokenType.ASSERT)
        condition = self.parse_expression()
        message = None
        if self.match(TokenType.COMMA):
            self.advance()
            message = self.parse_expression()
        return AssertStmt(condition=condition, message=message, line=tok.line, column=tok.column)

    def parse_match_expr(self) -> MatchExpr:
        tok = self.expect(TokenType.MATCH)
        value = self.parse_expression()
        self.expect(TokenType.LBRACE, "Expected '{' after match value")
        cases = []
        while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
            pattern = self.parse_expression()
            guard = None
            if self.match(TokenType.IF):
                self.advance()
                guard = self.parse_expression()
            self.expect(TokenType.DOUBLE_ARROW, "Expected '=>'")
            body = self.parse_expression()
            cases.append(MatchCase(pattern=pattern, guard=guard, body=body,
                                   line=pattern.line, column=pattern.column))
            if self.match(TokenType.COMMA):
                self.advance()
        self.expect(TokenType.RBRACE, "Expected '}'")
        return MatchExpr(value=value, cases=cases, line=tok.line, column=tok.column)

    def parse_block(self) -> Block:
        open_tok = self.expect(TokenType.LBRACE, "Expected '{'")
        self.skip_newlines()
        stmts = []
        while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        close_tok = self.expect(TokenType.RBRACE, "Expected '}'")
        return Block(statements=stmts, line=open_tok.line, column=open_tok.column)

    def parse_expr_stmt(self) -> ASTNode:
        expr = self.parse_expression()
        tok = self.peek()
        augmented_ops = {
            TokenType.PLUS_ASSIGN: '+=', TokenType.MINUS_ASSIGN: '-=',
            TokenType.STAR_ASSIGN: '*=', TokenType.SLASH_ASSIGN: '/=',
            TokenType.PERCENT_ASSIGN: '%=', TokenType.POWER_ASSIGN: '**=',
        }
        if tok.type in augmented_ops:
            op = self.advance().value
            value = self.parse_expression()
            return AugAssignStmt(target=expr, value=value, op=op,
                                 line=expr.line, column=expr.column)
        if tok.type == TokenType.ASSIGN:
            self.advance()
            value = self.parse_expression()
            return AssignStmt(target=expr, value=value,
                              line=expr.line, column=expr.column)
        return ExprStmt(expr=expr, line=expr.line if expr else 0, column=expr.column if expr else 0)

    # ─── Expression Parsing (Pratt) ──────────────────────────────────────
    def parse_expression(self, min_prec: int = 0) -> ASTNode:
        left = self.parse_unary()
        while True:
            tok = self.peek()
            if tok.type not in PRECEDENCE:
                break
            prec = PRECEDENCE[tok.type]
            if prec < min_prec:
                break
            op_tok = self.advance()
            if tok.type == TokenType.PIPE:
                right = self.parse_expression(prec)
                left = PipeExpr(left=left, right=right, line=op_tok.line, column=op_tok.column)
            elif tok.type == TokenType.NULLISH:
                right = self.parse_expression(prec + 1)
                left = NullishCoalesceExpr(left=left, right=right, line=op_tok.line, column=op_tok.column)
            elif tok.type == TokenType.IS:
                right_type = self.parse_type_ref()
                left = IsExpr(value=left, type_ref=right_type, line=op_tok.line, column=op_tok.column)
            elif tok.type == TokenType.AS:
                right_type = self.parse_type_ref()
                left = AsExpr(value=left, type_ref=right_type, line=op_tok.line, column=op_tok.column)
            elif tok.type in (TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT,
                              TokenType.LTE, TokenType.GTE, TokenType.PLUS, TokenType.MINUS,
                              TokenType.STAR, TokenType.SLASH, TokenType.PERCENT, TokenType.FLOOR_DIV,
                              TokenType.POWER, TokenType.LSHIFT, TokenType.RSHIFT,
                              TokenType.BIT_AND, TokenType.BIT_OR, TokenType.BIT_XOR):
                right = self.parse_expression(prec + 1)
                left = BinaryExpr(op=tok.value, left=left, right=right, line=op_tok.line, column=op_tok.column)
            elif tok.type == TokenType.AND or tok.type == TokenType.AND_AND:
                right = self.parse_expression(prec + 1)
                left = BinaryExpr(op="and", left=left, right=right, line=op_tok.line, column=op_tok.column)
            elif tok.type == TokenType.OR or tok.type == TokenType.OR_OR:
                right = self.parse_expression(prec + 1)
                left = BinaryExpr(op="or", left=left, right=right, line=op_tok.line, column=op_tok.column)
            else:
                break
        return left

    def parse_unary(self) -> ASTNode:
        tok = self.peek()
        if tok.type == TokenType.MINUS:
            self.advance()
            operand = self.parse_unary()
            return UnaryExpr(op="-", operand=operand, prefix=True, line=tok.line, column=tok.column)
        if tok.type == TokenType.NOT:
            self.advance()
            operand = self.parse_unary()
            return UnaryExpr(op="not", operand=operand, prefix=True, line=tok.line, column=tok.column)
        if tok.type == TokenType.NOT_NOT:
            self.advance()
            operand = self.parse_unary()
            return UnaryExpr(op="not not", operand=operand, prefix=True, line=tok.line, column=tok.column)
        if tok.type == TokenType.BIT_NOT:
            self.advance()
            operand = self.parse_unary()
            return UnaryExpr(op="~", operand=operand, prefix=True, line=tok.line, column=tok.column)
        if tok.type == TokenType.AWAIT:
            self.advance()
            operand = self.parse_unary()
            return AwaitExpr(value=operand, line=tok.line, column=tok.column)
        if tok.type == TokenType.YIELD:
            self.advance()
            value = self.parse_expression() if not self.at(TokenType.NEWLINE) else None
            return YieldExpr(value=value, line=tok.line, column=tok.column)
        if tok.type == TokenType.SPREAD:
            self.advance()
            operand = self.parse_unary()
            return SpreadExpr(value=operand, line=tok.line, column=tok.column)
        if tok.type == TokenType.TYPEOF:
            self.advance()
            operand = self.parse_unary()
            return TypeOfExpr(value=operand, line=tok.line, column=tok.column)
        return self.parse_postfix()

    def parse_postfix(self) -> ASTNode:
        expr = self.parse_primary()
        while True:
            if self.match(TokenType.DOT):
                self.advance()
                prop = self.expect(TokenType.IDENT, "Expected property name")
                expr = PropertyAccessExpr(object=expr, property=prop.value, line=prop.line, column=prop.column)
            elif self.match(TokenType.LPAREN):
                args, kwargs = self.parse_call_args()
                expr = CallExpr(callee=expr, args=args, kwargs=kwargs, line=expr.line, column=expr.column)
            elif self.match(TokenType.LBRACKET):
                self.advance()
                if self.match(TokenType.COLON):
                    self.advance()
                    end = self.parse_expression() if not self.at(TokenType.RBRACKET) else None
                    step = None
                    if self.match(TokenType.COLON):
                        self.advance()
                        step = self.parse_expression() if not self.at(TokenType.RBRACKET) else None
                    self.expect(TokenType.RBRACKET)
                    expr = SliceExpr(object=expr, start=None, end=end, step=step, line=expr.line, column=expr.column)
                else:
                    index = self.parse_expression()
                    if self.match(TokenType.COLON):
                        self.advance()
                        end = self.parse_expression() if not self.at(TokenType.RBRACKET) else None
                        step = None
                        if self.match(TokenType.COLON):
                            self.advance()
                            step = self.parse_expression() if not self.at(TokenType.RBRACKET) else None
                        self.expect(TokenType.RBRACKET)
                        expr = SliceExpr(object=expr, start=index, end=end, step=step, line=expr.line, column=expr.column)
                    else:
                        self.expect(TokenType.RBRACKET)
                        expr = IndexExpr(object=expr, index=index, line=expr.line, column=expr.column)
            elif self.match(TokenType.DOUBLE_COLON):
                self.advance()
                name = self.expect(TokenType.IDENT, "Expected name")
                if self.match(TokenType.LPAREN):
                    args, kwargs = self.parse_call_args()
                    expr = CallExpr(
                        callee=PropertyAccessExpr(object=expr, property=name.value, line=name.line, column=name.column),
                        args=args, kwargs=kwargs,
                        line=expr.line, column=expr.column,
                    )
                else:
                    expr = PropertyAccessExpr(object=expr, property=name.value, line=name.line, column=name.column)
            else:
                break
        return expr

    def parse_call_args(self) -> tuple[list[ASTNode], dict[str, ASTNode]]:
        self.expect(TokenType.LPAREN)
        args = []
        kwargs = {}
        if self.match(TokenType.RPAREN):
            self.advance()
            return args, kwargs
        while not self.at(TokenType.RPAREN):
            if self.match(TokenType.DOUBLE_COLON):
                break
            if self.peek().type == TokenType.IDENT and (self.peek(1).type == TokenType.ASSIGN):
                name_tok = self.advance()
                self.advance()
                val = self.parse_expression()
                kwargs[name_tok.value] = val
            elif self.match(TokenType.SPREAD):
                self.advance()
                args.append(SpreadExpr(value=self.parse_expression(), line=self.peek().line, column=self.peek().column))
            else:
                args.append(self.parse_expression())
            if self.match(TokenType.COMMA):
                self.advance()
        self.expect(TokenType.RPAREN)
        return args, kwargs

    def parse_primary(self) -> ASTNode:
        tok = self.peek()

        if tok.type == TokenType.INT_LIT:
            self.advance()
            return IntLiteral(value=tok.value, line=tok.line, column=tok.column)
        if tok.type == TokenType.FLOAT_LIT:
            self.advance()
            return FloatLiteral(value=tok.value, line=tok.line, column=tok.column)
        if tok.type == TokenType.STRING_LIT:
            self.advance()
            return StringLiteral(value=tok.value, line=tok.line, column=tok.column)
        if tok.type == TokenType.BOOL_LIT:
            self.advance()
            return BoolLiteral(value=tok.value, line=tok.line, column=tok.column)
        if tok.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(value=True, line=tok.line, column=tok.column)
        if tok.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(value=False, line=tok.line, column=tok.column)
        if tok.type == TokenType.NONE_LIT:
            self.advance()
            return NoneLiteral(line=tok.line, column=tok.column)
        if tok.type == TokenType.NONE:
            self.advance()
            return NoneLiteral(line=tok.line, column=tok.column)
        if tok.type == TokenType.CHAR_LIT:
            self.advance()
            return CharLiteral(value=tok.value, line=tok.line, column=tok.column)
        if tok.type == TokenType.SELF:
            self.advance()
            return SelfExpr(line=tok.line, column=tok.column)
        if tok.type == TokenType.SUPER:
            self.advance()
            method = ""
            if self.match(TokenType.DOT):
                self.advance()
                method = self.expect(TokenType.IDENT, "Expected method name").value
            return SuperExpr(method=method, line=tok.line, column=tok.column)
        if tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(name=tok.value, line=tok.line, column=tok.column)
        if tok.type == TokenType.LPAREN:
            self.advance()
            if self.match(TokenType.RPAREN):
                self.advance()
                return TupleExpr(elements=[], line=tok.line, column=tok.column)
            expr = self.parse_expression()
            if self.match(TokenType.COMMA):
                elements = [expr]
                self.advance()
                while not self.at(TokenType.RPAREN):
                    elements.append(self.parse_expression())
                    if self.match(TokenType.COMMA):
                        self.advance()
                self.expect(TokenType.RPAREN)
                return TupleExpr(elements=elements, line=tok.line, column=tok.column)
            self.expect(TokenType.RPAREN)
            return expr
        if tok.type == TokenType.LBRACKET:
            self.advance()
            elements = []
            if not self.at(TokenType.RBRACKET):
                elements.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    self.advance()
                    if self.at(TokenType.RBRACKET):
                        break
                    elements.append(self.parse_expression())
            self.expect(TokenType.RBRACKET)
            return ListExpr(elements=elements, line=tok.line, column=tok.column)
        if tok.type == TokenType.LBRACE:
            self.advance()
            keys = []
            values = []
            if not self.at(TokenType.RBRACE):
                k = self.parse_expression()
                self.expect(TokenType.COLON, "Expected ':' in dict")
                v = self.parse_expression()
                keys.append(k)
                values.append(v)
                while self.match(TokenType.COMMA):
                    self.advance()
                    if self.at(TokenType.RBRACE):
                        break
                    k = self.parse_expression()
                    self.expect(TokenType.COLON)
                    v = self.parse_expression()
                    keys.append(k)
                    values.append(v)
            self.expect(TokenType.RBRACE)
            return DictExpr(keys=keys, values=values, line=tok.line, column=tok.column)
        if tok.type == TokenType.LAMBDA:
            self.advance()
            params = []
            if self.match(TokenType.IDENT):
                params.append(Param(name=self.advance().value))
                while self.match(TokenType.COMMA):
                    self.advance()
                    params.append(Param(name=self.expect(TokenType.IDENT, "Expected param name").value))
            if self.match(TokenType.DOUBLE_ARROW):
                self.advance()
            body = self.parse_expression()
            return LambdaExpr(params=params, body=body, line=tok.line, column=tok.column)
        if tok.type == TokenType.IF:
            return self.parse_if_expr()
        if tok.type == TokenType.MATCH:
            return self.parse_match_expr()

        raise self.error(f"Unexpected token: {tok.type.name} ({tok.value!r})")

    def parse_if_expr(self) -> IfExpr:
        tok = self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.expect(TokenType.LBRACE, "Expected '{' for if expression")
        then_stmts = []
        while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
            then_stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        then_body = Block(statements=then_stmts, line=then_stmts[0].line if then_stmts else tok.line,
                          column=then_stmts[0].column if then_stmts else tok.column) if then_stmts else Block()
        elif_branches = []
        else_body = None
        while self.match(TokenType.ELIF):
            self.advance()
            elif_cond = self.parse_expression()
            self.expect(TokenType.LBRACE)
            elif_stmts = []
            while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
                elif_stmts.append(self.parse_statement())
            self.expect(TokenType.RBRACE)
            elif_body = Block(statements=elif_stmts) if elif_stmts else Block()
            elif_branches.append((elif_cond, elif_body))
        if self.match(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.LBRACE)
            else_stmts = []
            while not self.at(TokenType.RBRACE) and not self.at(TokenType.EOF):
                else_stmts.append(self.parse_statement())
            self.expect(TokenType.RBRACE)
            else_body = Block(statements=else_stmts) if else_stmts else Block()
        return IfExpr(
            condition=condition,
            then_body=then_body,
            elif_branches=elif_branches,
            else_body=else_body,
            line=tok.line,
            column=tok.column,
        )

    def parse_type_ref(self) -> TypeRef:
        tok = self.peek()
        if tok.type == TokenType.LBRACKET:
            self.advance()
            inner = self.parse_type_ref()
            self.expect(TokenType.RBRACKET)
            return TypeRef(name="List", type_args=[inner], is_list=True, line=tok.line, column=tok.column)
        if tok.type == TokenType.LBRACE:
            self.advance()
            key_type = self.parse_type_ref()
            self.expect(TokenType.COLON)
            val_type = self.parse_type_ref()
            self.expect(TokenType.RBRACE)
            return TypeRef(name="Dict", type_args=[key_type, val_type], is_dict=True,
                          dict_key=key_type, line=tok.line, column=tok.column)

        name_tok = self.expect(TokenType.IDENT, "Expected type name")
        type_args = []
        if self.match(TokenType.LT):
            self.advance()
            type_args.append(self.parse_type_ref())
            while self.match(TokenType.COMMA):
                self.advance()
                type_args.append(self.parse_type_ref())
            self.expect(TokenType.GT, "Expected '>'")

        nullable = False
        if self.match(TokenType.QUESTION):
            self.advance()
            nullable = True

        return TypeRef(
            name=name_tok.value,
            type_args=type_args,
            nullable=nullable,
            line=tok.line,
            column=tok.column,
        )


def parse(source: str, filename: str = "<stdin>") -> Program:
    from ..lexer.lexer import tokenize
    tokens = tokenize(source, filename)
    return Parser(tokens, filename).parse()
