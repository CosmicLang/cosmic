"""AST node types for the Cosmic language."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


# ─── Base ────────────────────────────────────────────────────────────────
@dataclass
class ASTNode:
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        method = getattr(visitor, f'visit_{type(self).__name__}', None)
        if method:
            return method(self)
        return visitor.generic_visit(self)


# ─── Expressions ─────────────────────────────────────────────────────────
@dataclass
class IntLiteral(ASTNode):
    value: int = 0

@dataclass
class FloatLiteral(ASTNode):
    value: float = 0.0

@dataclass
class StringLiteral(ASTNode):
    value: str = ""

@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

@dataclass
class NoneLiteral(ASTNode):
    pass

@dataclass
class CharLiteral(ASTNode):
    value: str = ""

@dataclass
class Identifier(ASTNode):
    name: str = ""

@dataclass
class SelfExpr(ASTNode):
    pass

@dataclass
class SuperExpr(ASTNode):
    method: str = ""

@dataclass
class BinaryExpr(ASTNode):
    op: str = ""
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class UnaryExpr(ASTNode):
    op: str = ""
    operand: ASTNode = None
    prefix: bool = True

@dataclass
class CallExpr(ASTNode):
    callee: ASTNode = None
    args: list[ASTNode] = field(default_factory=list)
    kwargs: dict[str, ASTNode] = field(default_factory=dict)

@dataclass
class MethodCallExpr(ASTNode):
    object: ASTNode = None
    method: str = ""
    args: list[ASTNode] = field(default_factory=list)
    kwargs: dict[str, ASTNode] = field(default_factory=dict)

@dataclass
class PropertyAccessExpr(ASTNode):
    object: ASTNode = None
    property: str = ""

@dataclass
class IndexExpr(ASTNode):
    object: ASTNode = None
    index: ASTNode = None

@dataclass
class SliceExpr(ASTNode):
    object: ASTNode = None
    start: Optional[ASTNode] = None
    end: Optional[ASTNode] = None
    step: Optional[ASTNode] = None

@dataclass
class LambdaExpr(ASTNode):
    params: list[Param] = field(default_factory=list)
    body: ASTNode = None

@dataclass
class ListExpr(ASTNode):
    elements: list[ASTNode] = field(default_factory=list)

@dataclass
class DictExpr(ASTNode):
    keys: list[ASTNode] = field(default_factory=list)
    values: list[ASTNode] = field(default_factory=list)

@dataclass
class SetExpr(ASTNode):
    elements: list[ASTNode] = field(default_factory=list)

@dataclass
class TupleExpr(ASTNode):
    elements: list[ASTNode] = field(default_factory=list)

@dataclass
class IfExpr(ASTNode):
    condition: ASTNode = None
    then_body: ASTNode = None
    elif_branches: list[tuple[ASTNode, ASTNode]] = field(default_factory=list)
    else_body: Optional[ASTNode] = None

@dataclass
class MatchExpr(ASTNode):
    value: ASTNode = None
    cases: list[MatchCase] = field(default_factory=list)

@dataclass
class MatchCase(ASTNode):
    pattern: ASTNode = None
    guard: Optional[ASTNode] = None
    body: ASTNode = None

@dataclass
class IsExpr(ASTNode):
    value: ASTNode = None
    type_ref: TypeRef = None

@dataclass
class AsExpr(ASTNode):
    value: ASTNode = None
    type_ref: TypeRef = None

@dataclass
class PipeExpr(ASTNode):
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class NullishCoalesceExpr(ASTNode):
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class SpreadExpr(ASTNode):
    value: ASTNode = None

@dataclass
class GeneratorExpr(ASTNode):
    var: str = ""
    element: ASTNode = None
    iter_expr: ASTNode = None
    condition: Optional[ASTNode] = None

@dataclass
class AwaitExpr(ASTNode):
    value: ASTNode = None

@dataclass
class YieldExpr(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class TypeOfExpr(ASTNode):
    value: ASTNode = None


# ─── Statements ──────────────────────────────────────────────────────────
@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode = None

@dataclass
class AssignStmt(ASTNode):
    target: ASTNode = None
    value: ASTNode = None
    op: str = "="

@dataclass
class AugAssignStmt(ASTNode):
    target: ASTNode = None
    value: ASTNode = None
    op: str = "+="

@dataclass
class LetStmt(ASTNode):
    name: str = ""
    type_ref: Optional[TypeRef] = None
    value: Optional[ASTNode] = None
    mutable: bool = False

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class BreakStmt(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class ContinueStmt(ASTNode):
    pass

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode = None
    then_body: ASTNode = None
    elif_branches: list[tuple[ASTNode, ASTNode]] = field(default_factory=list)
    else_body: Optional[ASTNode] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode = None
    body: ASTNode = None

@dataclass
class ForStmt(ASTNode):
    var: str = ""
    iter_expr: ASTNode = None
    body: ASTNode = None

@dataclass
class LoopStmt(ASTNode):
    body: ASTNode = None

@dataclass
class RaiseStmt(ASTNode):
    value: ASTNode = None

@dataclass
class TryStmt(ASTNode):
    body: ASTNode = None
    catch_clauses: list[CatchClause] = field(default_factory=list)
    finally_body: Optional[ASTNode] = None

@dataclass
class CatchClause(ASTNode):
    type_ref: Optional[TypeRef] = None
    var_name: Optional[str] = None
    body: ASTNode = None

@dataclass
class AssertStmt(ASTNode):
    condition: ASTNode = None
    message: Optional[ASTNode] = None

@dataclass
class Block(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)


# ─── Declarations ────────────────────────────────────────────────────────
@dataclass
class Param(ASTNode):
    name: str = ""
    type_ref: Optional[TypeRef] = None
    default: Optional[ASTNode] = None

@dataclass
class FnDecl(ASTNode):
    name: str = ""
    params: list[Param] = field(default_factory=list)
    return_type: Optional[TypeRef] = None
    body: Optional[ASTNode] = None
    is_async: bool = False
    is_pub: bool = False
    is_static: bool = False
    decorators: list[ASTNode] = field(default_factory=list)

@dataclass
class ClassDecl(ASTNode):
    name: str = ""
    bases: list[TypeRef] = field(default_factory=list)
    body: ASTNode = None
    is_pub: bool = False
    is_abstract: bool = False
    type_params: list[str] = field(default_factory=list)

@dataclass
class RecordDecl(ASTNode):
    name: str = ""
    fields: list[Param] = field(default_factory=list)
    methods: list[FnDecl] = field(default_factory=list)
    is_pub: bool = False
    type_params: list[str] = field(default_factory=list)

@dataclass
class EnumDecl(ASTNode):
    name: str = ""
    variants: list[EnumVariant] = field(default_factory=list)
    is_pub: bool = False

@dataclass
class EnumVariant(ASTNode):
    name: str = ""
    fields: list[TypeRef] = field(default_factory=list)
    value: Optional[ASTNode] = None

@dataclass
class InterfaceDecl(ASTNode):
    name: str = ""
    methods: list[FnDecl] = field(default_factory=list)
    is_pub: bool = False

@dataclass
class TypeAlias(ASTNode):
    name: str = ""
    type_ref: TypeRef = None
    is_pub: bool = False

@dataclass
class ModuleDecl(ASTNode):
    name: str = ""
    body: list[ASTNode] = field(default_factory=list)

@dataclass
class ImportDecl(ASTNode):
    module: str = ""
    names: list[str] = field(default_factory=list)
    alias: Optional[str] = None

@dataclass
class FromImportDecl(ASTNode):
    module: str = ""
    names: list[tuple[str, Optional[str]]] = field(default_factory=list)

@dataclass
class TestDecl(ASTNode):
    name: str = ""
    body: ASTNode = None


# ─── Types ───────────────────────────────────────────────────────────────
@dataclass
class TypeRef(ASTNode):
    name: str = ""
    type_args: list[TypeRef] = field(default_factory=list)
    nullable: bool = False
    is_list: bool = False
    is_dict: bool = False
    dict_key: Optional[TypeRef] = None

@dataclass
class FuncType(ASTNode):
    params: list[TypeRef] = field(default_factory=list)
    return_type: TypeRef = None

@dataclass
class UnionType(ASTNode):
    types: list[TypeRef] = field(default_factory=list)

@dataclass
class TupleType(ASTNode):
    types: list[TypeRef] = field(default_factory=list)


# ─── Program ─────────────────────────────────────────────────────────────
@dataclass
class Program(ASTNode):
    statements: list[ASTNode] = field(default_factory=list)
    filename: str = ""
