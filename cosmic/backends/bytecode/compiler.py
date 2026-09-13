"""Bytecode compiler and VM for the Cosmic language."""
from __future__ import annotations
from enum import IntEnum, auto
from dataclasses import dataclass, field
from typing import Any, Optional
from ...ast.nodes import *


# ─── Opcodes ─────────────────────────────────────────────────────────────

class Op(IntEnum):
    LOAD_CONST = auto()
    LOAD_NULL = auto()
    LOAD_TRUE = auto()
    LOAD_FALSE = auto()
    LOAD_LOCAL = auto()
    STORE_LOCAL = auto()
    LOAD_GLOBAL = auto()
    STORE_GLOBAL = auto()
    LOAD_ATTR = auto()
    STORE_ATTR = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()
    JUMP_IF_NOT_NULL = auto()
    CALL = auto()
    CALL_METHOD = auto()
    RETURN = auto()
    MAKE_FUNCTION = auto()
    MAKE_CLOSURE = auto()
    MAKE_LIST = auto()
    MAKE_DICT = auto()
    MAKE_SET = auto()
    MAKE_TUPLE = auto()
    INDEX = auto()
    SLICE = auto()
    ITER_NEXT = auto()
    ITER_HAS_NEXT = auto()
    POP_TOP = auto()
    DUP_TOP = auto()
    RAISE = auto()
    TRY_START = auto()
    TRY_END = auto()
    CATCH_START = auto()
    IMPORT_NAME = auto()
    IMPORT_FROM = auto()
    YIELD = auto()
    AWAIT = auto()
    MAKE_CLASS = auto()
    MAKE_RECORD = auto()
    MAKE_ENUM = auto()
    HALT = auto()


class BinaryOp(IntEnum):
    ADD = 0
    SUB = 1
    MUL = 2
    DIV = 3
    MOD = 4
    POW = 5
    FLOOR_DIV = 6
    EQ = 7
    NEQ = 8
    LT = 9
    GT = 10
    LTE = 11
    GTE = 12
    AND = 13
    OR = 14
    BIT_AND = 15
    BIT_OR = 16
    BIT_XOR = 17
    LSHIFT = 18
    RSHIFT = 19


class UnaryOp(IntEnum):
    NEG = 0
    NOT = 1
    BIT_NOT = 2


BINOP_MAP = {
    "+": BinaryOp.ADD, "-": BinaryOp.SUB, "*": BinaryOp.MUL,
    "/": BinaryOp.DIV, "%": BinaryOp.MOD, "**": BinaryOp.POW,
    "//": BinaryOp.FLOOR_DIV, "==": BinaryOp.EQ, "!=": BinaryOp.NEQ,
    "<": BinaryOp.LT, ">": BinaryOp.GT, "<=": BinaryOp.LTE,
    ">=": BinaryOp.GTE, "and": BinaryOp.AND, "or": BinaryOp.OR,
    "&": BinaryOp.BIT_AND, "|": BinaryOp.BIT_OR, "^": BinaryOp.BIT_XOR,
    "<<": BinaryOp.LSHIFT, ">>": BinaryOp.RSHIFT,
}

UNOP_MAP = {"-": UnaryOp.NEG, "not": UnaryOp.NOT, "~": UnaryOp.BIT_NOT}

AUG_BINOP_MAP = {
    "+=": BinaryOp.ADD, "-=": BinaryOp.SUB, "*=": BinaryOp.MUL,
    "/=": BinaryOp.DIV, "%=": BinaryOp.MOD, "**=": BinaryOp.POW,
    "//=": BinaryOp.FLOOR_DIV, "&=": BinaryOp.BIT_AND,
    "|=": BinaryOp.BIT_OR, "^=": BinaryOp.BIT_XOR,
    "<<=": BinaryOp.LSHIFT, ">>=": BinaryOp.RSHIFT,
}


# ─── Instruction ─────────────────────────────────────────────────────────

@dataclass
class Instruction:
    op: Op
    arg: Any = None
    line: int = 0

    def __repr__(self):
        return f"Instruction({self.op.name}, {self.arg!r})"


# ─── BytecodeFunction ───────────────────────────────────────────────────

@dataclass
class BytecodeFunction:
    name: str
    arity: int
    instructions: list[Instruction] = field(default_factory=list)
    constants: list[Any] = field(default_factory=list)
    local_names: list[str] = field(default_factory=list)
    is_closure: bool = False
    free_vars: list[str] = field(default_factory=list)
    upvalue_count: int = 0


# ─── Compiler ────────────────────────────────────────────────────────────

class CompilerState:
    def __init__(self, parent=None, kind="function"):
        self.parent = parent
        self.kind = kind
        self.instructions: list[Instruction] = []
        self.constants: list[Any] = []
        self.local_names: list[str] = []
        self.local_count = 0
        self.scope_depth = 0
        self.breaks: list[int] = []
        self.continues: list[int] = []
        self.try_depth = 0

    def add_local(self, name: str):
        self.local_names.append(name)
        self.local_count += 1
        return self.local_count - 1

    def resolve_local(self, name: str) -> Optional[int]:
        for i in range(len(self.local_names) - 1, -1, -1):
            if self.local_names[i] == name:
                return i
        return None


class BytecodeCompiler:
    def __init__(self):
        self.state = CompilerState(kind="module")
        self.interned_strings: dict[str, int] = {}
        self.globals: dict[str, str] = {}
        self.global_count = 0
        self.functions: list[BytecodeFunction] = []
        self.errors: list[str] = []

    def _emit(self, op: Op, arg=None, line=0):
        self.state.instructions.append(Instruction(op, arg, line))

    def _add_constant(self, value: Any) -> int:
        for i, c in enumerate(self.state.constants):
            if c == value and type(c) is type(value):
                return i
        self.state.constants.append(value)
        return len(self.state.constants) - 1

    def _resolve_free(self, name: str) -> Optional[int]:
        state = self.state.parent
        while state:
            idx = state.resolve_local(name)
            if idx is not None:
                return idx
            state = state.parent
        return None

    def _enter_scope(self):
        self.state.scope_depth += 1

    def _exit_scope(self) -> list[Instruction]:
        pops = []
        while self.state.instructions:
            last = self.state.instructions[-1]
            if last.op in (Op.LOAD_LOCAL, Op.STORE_LOCAL):
                break
            self.state.instructions.pop()
        depth = self.state.scope_depth
        count = 0
        for i in range(len(self.state.local_names) - 1, -1, -1):
            if i < self.state.local_count - count:
                break
            count += 1
        for _ in range(count):
            self.state.instructions.append(Instruction(Op.POP_TOP, None, 0))
        self.state.local_names = self.state.local_names[:-count] if count else self.state.local_names
        self.state.local_count -= count
        self.state.scope_depth -= 1
        return pops

    def compile(self, ast: Program) -> tuple[list[Instruction], list[Any]]:
        for stmt in ast.statements:
            self._compile_node(stmt)
        self._emit(Op.HALT)
        return self.state.instructions, self.state.constants

    def _compile_node(self, node: ASTNode):
        method = getattr(self, f'_compile_{type(node).__name__}', None)
        if method:
            method(node)
        else:
            self._emit(Op.LOAD_CONST, self._add_constant(None), node.line)

    # ── Literals ──────────────────────────────────────────────────────

    def _compile_IntLiteral(self, node: IntLiteral):
        idx = self._add_constant(node.value)
        self._emit(Op.LOAD_CONST, idx, node.line)

    def _compile_FloatLiteral(self, node: FloatLiteral):
        idx = self._add_constant(node.value)
        self._emit(Op.LOAD_CONST, idx, node.line)

    def _compile_StringLiteral(self, node: StringLiteral):
        idx = self._add_constant(node.value)
        self._emit(Op.LOAD_CONST, idx, node.line)

    def _compile_BoolLiteral(self, node: BoolLiteral):
        self._emit(Op.LOAD_TRUE if node.value else Op.LOAD_FALSE, line=node.line)

    def _compile_NoneLiteral(self, node: NoneLiteral):
        self._emit(Op.LOAD_NULL, line=node.line)

    def _compile_CharLiteral(self, node: CharLiteral):
        idx = self._add_constant(node.value)
        self._emit(Op.LOAD_CONST, idx, node.line)

    def _compile_Identifier(self, node: Identifier):
        local = self.state.resolve_local(node.name)
        if local is not None:
            self._emit(Op.LOAD_LOCAL, local, node.line)
        else:
            self._emit(Op.LOAD_GLOBAL, node.name, node.line)

    def _compile_SelfExpr(self, node: SelfExpr):
        local = self.state.resolve_local("self")
        if local is not None:
            self._emit(Op.LOAD_LOCAL, local, node.line)
        else:
            self._emit(Op.LOAD_GLOBAL, "self", node.line)

    def _compile_SuperExpr(self, node: SuperExpr):
        self._emit(Op.LOAD_GLOBAL, "super", node.line)

    # ── Expressions ───────────────────────────────────────────────────

    def _compile_BinaryExpr(self, node: BinaryExpr):
        if node.op == "and":
            self._compile_node(node.left)
            self._emit(Op.DUP_TOP, line=node.line)
            end = len(self.state.instructions)
            self._emit(Op.JUMP_IF_FALSE, end + 3, node.line)
            self._emit(Op.POP_TOP, line=node.line)
            self._compile_node(node.right)
            self.state.instructions[end].arg = len(self.state.instructions)
            return
        if node.op == "or":
            self._compile_node(node.left)
            self._emit(Op.DUP_TOP, line=node.line)
            end = len(self.state.instructions)
            self._emit(Op.JUMP_IF_TRUE, end + 3, node.line)
            self._emit(Op.POP_TOP, line=node.line)
            self._compile_node(node.right)
            self.state.instructions[end].arg = len(self.state.instructions)
            return
        if node.op == "??":
            self._compile_node(node.left)
            self._emit(Op.DUP_TOP, line=node.line)
            end = len(self.state.instructions)
            self._emit(Op.JUMP_IF_NOT_NULL, end + 3, node.line)
            self._emit(Op.POP_TOP, line=node.line)
            self._compile_node(node.right)
            self.state.instructions[end].arg = len(self.state.instructions)
            return
        self._compile_node(node.left)
        self._compile_node(node.right)
        bop = BINOP_MAP.get(node.op)
        if bop is None:
            self._emit(Op.BINARY_OP, int(BinaryOp.ADD), node.line)
        else:
            self._emit(Op.BINARY_OP, int(bop), node.line)

    def _compile_UnaryExpr(self, node: UnaryExpr):
        self._compile_node(node.operand)
        uop = UNOP_MAP.get(node.op, UnaryOp.NEG)
        self._emit(Op.UNARY_OP, int(uop), node.line)

    def _compile_CallExpr(self, node: CallExpr):
        self._compile_node(node.callee)
        for arg in node.args:
            self._compile_node(arg)
        self._emit(Op.CALL, len(node.args), node.line)

    def _compile_MethodCallExpr(self, node: MethodCallExpr):
        self._compile_node(node.object)
        for arg in node.args:
            self._compile_node(arg)
        name_idx = self._add_constant(node.method)
        self._emit(Op.CALL_METHOD, (node.method, len(node.args)), node.line)

    def _compile_PropertyAccessExpr(self, node: PropertyAccessExpr):
        self._compile_node(node.object)
        self._emit(Op.LOAD_ATTR, node.property, node.line)

    def _compile_IndexExpr(self, node: IndexExpr):
        self._compile_node(node.object)
        self._compile_node(node.index)
        self._emit(Op.INDEX, line=node.line)

    def _compile_SliceExpr(self, node: SliceExpr):
        self._compile_node(node.object)
        if node.start:
            self._compile_node(node.start)
        else:
            self._emit(Op.LOAD_NULL, line=node.line)
        if node.end:
            self._compile_node(node.end)
        else:
            self._emit(Op.LOAD_NULL, line=node.line)
        if node.step:
            self._compile_node(node.step)
        else:
            self._emit(Op.LOAD_NULL, line=node.line)
        self._emit(Op.SLICE, line=node.line)

    def _compile_LambdaExpr(self, node: LambdaExpr):
        func = self._compile_function(f"<lambda_{len(self.functions)}>", node.params, node.body)
        idx = self._add_constant(func)
        self._emit(Op.MAKE_CLOSURE if func.free_vars else Op.MAKE_FUNCTION, idx, node.line)

    def _compile_ListExpr(self, node: ListExpr):
        for elem in node.elements:
            self._compile_node(elem)
        self._emit(Op.MAKE_LIST, len(node.elements), node.line)

    def _compile_DictExpr(self, node: DictExpr):
        for key, val in zip(node.keys, node.values):
            self._compile_node(key)
            self._compile_node(val)
        self._emit(Op.MAKE_DICT, len(node.keys), node.line)

    def _compile_SetExpr(self, node: SetExpr):
        for elem in node.elements:
            self._compile_node(elem)
        self._emit(Op.MAKE_SET, len(node.elements), node.line)

    def _compile_TupleExpr(self, node: TupleExpr):
        for elem in node.elements:
            self._compile_node(elem)
        self._emit(Op.MAKE_TUPLE, len(node.elements), node.line)

    def _compile_PipeExpr(self, node: PipeExpr):
        self._compile_node(node.left)
        self._compile_node(node.right)

    def _compile_NullishCoalesceExpr(self, node: NullishCoalesceExpr):
        self._compile_node(node.left)
        self._emit(Op.DUP_TOP, line=node.line)
        end = len(self.state.instructions)
        self._emit(Op.JUMP_IF_NOT_NULL, end + 3, node.line)
        self._emit(Op.POP_TOP, line=node.line)
        self._compile_node(node.right)
        self.state.instructions[end].arg = len(self.state.instructions)

    def _compile_GeneratorExpr(self, node: GeneratorExpr):
        self._compile_node(node.iter_expr)
        self._emit(Op.MAKE_LIST, 0, node.line)

    def _compile_AwaitExpr(self, node: AwaitExpr):
        self._compile_node(node.value)
        self._emit(Op.AWAIT, line=node.line)

    def _compile_YieldExpr(self, node: YieldExpr):
        if node.value:
            self._compile_node(node.value)
        else:
            self._emit(Op.LOAD_NULL, line=node.line)
        self._emit(Op.YIELD, line=node.line)

    def _compile_IsExpr(self, node: IsExpr):
        self._compile_node(node.value)
        self._compile_node(node.type_ref) if node.type_ref else None

    def _compile_AsExpr(self, node: AsExpr):
        self._compile_node(node.value)

    def _compile_SpreadExpr(self, node: SpreadExpr):
        self._compile_node(node.value)

    def _compile_TypeOfExpr(self, node: TypeOfExpr):
        self._compile_node(node.value)

    def _compile_MatchExpr(self, node: MatchExpr):
        self._compile_node(node.value)
        self._emit(Op.POP_TOP, line=node.line)

    def _compile_MatchCase(self, node: MatchCase):
        self._compile_node(node.body)

    # ── Statements ────────────────────────────────────────────────────

    def _compile_ExprStmt(self, node: ExprStmt):
        self._compile_node(node.expr)
        self._emit(Op.POP_TOP, line=node.line)

    def _compile_AssignStmt(self, node: AssignStmt):
        if isinstance(node.target, Identifier):
            local = self.state.resolve_local(node.target.name)
            if local is not None:
                self._compile_node(node.value)
                self._emit(Op.STORE_LOCAL, local, node.line)
            else:
                self._compile_node(node.value)
                self._emit(Op.STORE_GLOBAL, node.target.name, node.line)
        elif isinstance(node.target, PropertyAccessExpr):
            self._compile_node(node.target.object)
            self._compile_node(node.value)
            self._emit(Op.STORE_ATTR, node.target.property, node.line)
        elif isinstance(node.target, IndexExpr):
            self._compile_node(node.target.object)
            self._compile_node(node.target.index)
            self._compile_node(node.value)
        else:
            self._compile_node(node.value)

    def _compile_AugAssignStmt(self, node: AugAssignStmt):
        if isinstance(node.target, Identifier):
            local = self.state.resolve_local(node.target.name)
            if local is not None:
                self._emit(Op.LOAD_LOCAL, local, node.line)
            else:
                self._emit(Op.LOAD_GLOBAL, node.target.name, node.line)
            self._compile_node(node.value)
            bop = AUG_BINOP_MAP.get(node.op)
            if bop is not None:
                self._emit(Op.BINARY_OP, int(bop), node.line)
            if local is not None:
                self._emit(Op.STORE_LOCAL, local, node.line)
            else:
                self._emit(Op.STORE_GLOBAL, node.target.name, node.line)

    def _compile_LetStmt(self, node: LetStmt):
        local_idx = self.state.add_local(node.name)
        if node.value:
            self._compile_node(node.value)
        else:
            self._emit(Op.LOAD_NULL, line=node.line)
        self._emit(Op.STORE_LOCAL, local_idx, node.line)

    def _compile_ReturnStmt(self, node: ReturnStmt):
        if node.value:
            self._compile_node(node.value)
        else:
            self._emit(Op.LOAD_NULL, line=node.line)
        self._emit(Op.RETURN, line=node.line)

    def _compile_BreakStmt(self, node: BreakStmt):
        self._emit(Op.JUMP, len(self.state.instructions), node.line)
        self.state.breaks.append(len(self.state.instructions) - 1)

    def _compile_ContinueStmt(self, node: ContinueStmt):
        self._emit(Op.JUMP, len(self.state.instructions), node.line)
        self.state.continues.append(len(self.state.instructions) - 1)

    def _compile_IfStmt(self, node: IfStmt):
        self._compile_node(node.condition)
        if_false = len(self.state.instructions)
        self._emit(Op.JUMP_IF_FALSE, 0, node.line)
        self._compile_node(node.then_body)
        end_jumps = [len(self.state.instructions)]
        self._emit(Op.JUMP, 0, node.line)
        self.state.instructions[if_false].arg = len(self.state.instructions)
        for elif_cond, elif_body in node.elif_branches:
            self._compile_node(elif_cond)
            elif_false = len(self.state.instructions)
            self._emit(Op.JUMP_IF_FALSE, 0, node.line)
            self._compile_node(elif_body)
            end_jumps.append(len(self.state.instructions))
            self._emit(Op.JUMP, 0, node.line)
            self.state.instructions[elif_false].arg = len(self.state.instructions)
        if node.else_body:
            self._compile_node(node.else_body)
        for jmp in end_jumps:
            self.state.instructions[jmp].arg = len(self.state.instructions)

    def _compile_IfExpr(self, node: IfExpr):
        self._compile_node(node.condition)
        if_false = len(self.state.instructions)
        self._emit(Op.JUMP_IF_FALSE, 0, node.line)
        self._compile_node(node.then_body)
        end_jumps = [len(self.state.instructions)]
        self._emit(Op.JUMP, 0, node.line)
        self.state.instructions[if_false].arg = len(self.state.instructions)
        for elif_cond, elif_body in node.elif_branches:
            self._compile_node(elif_cond)
            elif_false = len(self.state.instructions)
            self._emit(Op.JUMP_IF_FALSE, 0, node.line)
            self._compile_node(elif_body)
            end_jumps.append(len(self.state.instructions))
            self._emit(Op.JUMP, 0, node.line)
            self.state.instructions[elif_false].arg = len(self.state.instructions)
        if node.else_body:
            self._compile_node(node.else_body)
        for jmp in end_jumps:
            self.state.instructions[jmp].arg = len(self.state.instructions)

    def _compile_WhileStmt(self, node: WhileStmt):
        loop_start = len(self.state.instructions)
        self._compile_node(node.condition)
        if_false = len(self.state.instructions)
        self._emit(Op.JUMP_IF_FALSE, 0, node.line)
        self._compile_node(node.body)
        self._emit(Op.JUMP, loop_start, node.line)
        self.state.instructions[if_false].arg = len(self.state.instructions)
        breaks = self.state.breaks
        continues = self.state.continues
        self.state.breaks = []
        self.state.continues = []
        for b in breaks:
            self.state.instructions[b].arg = len(self.state.instructions)
        for c in continues:
            self.state.instructions[c].arg = loop_start

    def _compile_ForStmt(self, node: ForStmt):
        self._compile_node(node.iter_expr)
        iter_var = self.state.add_local("$iter")
        self._emit(Op.STORE_LOCAL, iter_var, node.line)
        loop_start = len(self.state.instructions)
        self._emit(Op.ITER_HAS_NEXT, iter_var, node.line)
        if_false = len(self.state.instructions)
        self._emit(Op.JUMP_IF_FALSE, 0, node.line)
        self._emit(Op.ITER_NEXT, iter_var, node.line)
        loop_var = self.state.add_local(node.var)
        self._emit(Op.STORE_LOCAL, loop_var, node.line)
        self._compile_node(node.body)
        self._emit(Op.JUMP, loop_start, node.line)
        self.state.instructions[if_false].arg = len(self.state.instructions)
        for b in self.state.breaks:
            self.state.instructions[b].arg = len(self.state.instructions)
        for c in self.state.continues:
            self.state.instructions[c].arg = loop_start
        self.state.breaks = []
        self.state.continues = []

    def _compile_LoopStmt(self, node: LoopStmt):
        loop_start = len(self.state.instructions)
        self._compile_node(node.body)
        self._emit(Op.JUMP, loop_start, node.line)
        for b in self.state.breaks:
            self.state.instructions[b].arg = len(self.state.instructions)
        for c in self.state.continues:
            self.state.instructions[c].arg = loop_start
        self.state.breaks = []
        self.state.continues = []

    def _compile_RaiseStmt(self, node: RaiseStmt):
        self._compile_node(node.value)
        self._emit(Op.RAISE, line=node.line)

    def _compile_TryStmt(self, node: TryStmt):
        try_start_idx = len(self.state.instructions)
        self._emit(Op.TRY_START, 0, node.line)
        self._compile_node(node.body)
        end_jump_idx = len(self.state.instructions)
        self._emit(Op.JUMP, 0, node.line)
        self.state.instructions[try_start_idx].arg = len(self.state.instructions)
        for clause in node.catch_clauses:
            self._emit(Op.CATCH_START, clause.var_name, clause.line)
            if clause.var_name:
                local_idx = self.state.add_local(clause.var_name)
                self._emit(Op.STORE_LOCAL, local_idx, clause.line)
            self._compile_node(clause.body)
        self._emit(Op.TRY_END, line=node.line)
        self.state.instructions[end_jump_idx].arg = len(self.state.instructions)

    def _compile_AssertStmt(self, node: AssertStmt):
        self._compile_node(node.condition)
        end = len(self.state.instructions)
        self._emit(Op.JUMP_IF_TRUE, 0, node.line)
        if node.message:
            self._compile_node(node.message)
        else:
            self._emit(Op.LOAD_CONST, self._add_constant("Assertion failed"), node.line)
        self._emit(Op.RAISE, line=node.line)
        self.state.instructions[end].arg = len(self.state.instructions)

    def _compile_Block(self, node: Block):
        for stmt in node.statements:
            self._compile_node(stmt)

    # ── Declarations ──────────────────────────────────────────────────

    def _compile_FnDecl(self, node: FnDecl):
        func = self._compile_function(node.name, node.params, node.body)
        idx = self._add_constant(func)
        self._emit(Op.MAKE_FUNCTION, idx, node.line)
        self.globals[node.name] = node.name
        self._emit(Op.STORE_GLOBAL, node.name, node.line)

    def _compile_ClassDecl(self, node: ClassDecl):
        self._emit(Op.LOAD_CONST, self._add_constant(node.name), node.line)
        self._compile_node(node.body)
        self._emit(Op.MAKE_CLASS, node.name, node.line)
        local = self.state.add_local(node.name)
        self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_RecordDecl(self, node: RecordDecl):
        self._emit(Op.LOAD_CONST, self._add_constant(node.name), node.line)
        for field in node.fields:
            self._emit(Op.LOAD_CONST, self._add_constant(field.name), field.line)
        self._emit(Op.MAKE_RECORD, (node.name, [f.name for f in node.fields]), node.line)
        local = self.state.add_local(node.name)
        self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_EnumDecl(self, node: EnumDecl):
        self._emit(Op.LOAD_CONST, self._add_constant(node.name), node.line)
        for variant in node.variants:
            self._emit(Op.LOAD_CONST, self._add_constant(variant.name), variant.line)
            if variant.fields:
                self._emit(Op.LOAD_CONST, self._add_constant(len(variant.fields)), variant.line)
            else:
                self._emit(Op.LOAD_CONST, self._add_constant(0), variant.line)
            if variant.value:
                self._compile_node(variant.value)
        self._emit(Op.MAKE_ENUM, (node.name, [(v.name, len(v.fields)) for v in node.variants]), node.line)
        local = self.state.add_local(node.name)
        self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_InterfaceDecl(self, node: InterfaceDecl):
        self._emit(Op.LOAD_CONST, self._add_constant(node.name), node.line)
        local = self.state.add_local(node.name)
        self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_TypeAlias(self, node: TypeAlias):
        self._emit(Op.LOAD_CONST, self._add_constant(node.name), node.line)
        local = self.state.add_local(node.name)
        self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_ModuleDecl(self, node: ModuleDecl):
        for stmt in node.body:
            self._compile_node(stmt)

    def _compile_ImportDecl(self, node: ImportDecl):
        self._emit(Op.IMPORT_NAME, node.module, node.line)
        alias = node.alias or node.module
        local = self.state.add_local(alias)
        self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_FromImportDecl(self, node: FromImportDecl):
        self._emit(Op.IMPORT_NAME, node.module, node.line)
        for name, alias in node.names:
            self._emit(Op.IMPORT_FROM, name, node.line)
            local = self.state.add_local(alias or name)
            self._emit(Op.STORE_LOCAL, local, node.line)

    def _compile_TestDecl(self, node: TestDecl):
        func = self._compile_function(f"test_{node.name}", [], node.body)
        idx = self._add_constant(func)
        self._emit(Op.MAKE_FUNCTION, idx, node.line)
        local = self.state.add_local(f"test_{node.name}")
        self._emit(Op.STORE_LOCAL, local, node.line)

    # ── Helpers ───────────────────────────────────────────────────────

    def _compile_function(self, name: str, params: list[Param], body: ASTNode) -> BytecodeFunction:
        prev = self.state
        self.state = CompilerState(parent=prev, kind="function")
        self.state.scope_depth = prev.scope_depth + 1
        for param in params:
            self.state.add_local(param.name)
        self._compile_node(body)
        has_return = self.state.instructions and self.state.instructions[-1].op == Op.RETURN
        if not has_return:
            if isinstance(body, Block):
                self._emit(Op.LOAD_NULL, line=body.line if body else 0)
            self._emit(Op.RETURN, line=body.line if body else 0)
        func = BytecodeFunction(
            name=name,
            arity=len(params),
            instructions=self.state.instructions,
            constants=self.state.constants,
            local_names=self.state.local_names,
        )
        self.functions.append(func)
        self.state = prev
        return func


# ─── VM ──────────────────────────────────────────────────────────────────

class VMError(Exception):
    pass


class _ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class CosmicRuntimeError(VMError):
    def __init__(self, message: str, traceback_info=None):
        super().__init__(message)
        self.traceback_info = traceback_info or []


@dataclass
class Frame:
    func: BytecodeFunction
    ip: int = 0
    locals: list[Any] = field(default_factory=list)
    stack: list[Any] = field(default_factory=list)


class CallFrame:
    def __init__(self, func: BytecodeFunction, locals_list=None):
        self.func = func
        self.ip = 0
        self.locals = locals_list if locals_list is not None else []
        self.stack: list[Any] = []


class _IteratorWrapper:
    def __init__(self, iterable):
        self._iter = iter(iterable)
        self._exhausted = False
        try:
            self._next_val = next(self._iter)
        except StopIteration:
            self._exhausted = True
            self._next_val = None

    def has_next(self):
        return not self._exhausted

    def next(self):
        if self._exhausted:
            return None
        val = self._next_val
        try:
            self._next_val = next(self._iter)
        except StopIteration:
            self._exhausted = True
        return val


class CosmicVM:
    def __init__(self):
        self.frames: list[CallFrame] = []
        self.globals: dict[str, Any] = {}
        self.stack: list[Any] = []
        self.output_buffer: list[str] = []
        self._exception_handlers: list[int] = []
        self._setup_builtins()

    def _setup_builtins(self):
        self.globals["print"] = "builtin_print"
        self.globals["println"] = "builtin_print"
        self.globals["puts"] = "builtin_print"
        self.globals["input"] = "builtin_input"
        self.globals["len"] = "builtin_len"
        self.globals["int"] = "builtin_int"
        self.globals["float"] = "builtin_float"
        self.globals["str"] = "builtin_str"
        self.globals["bool"] = "builtin_bool"
        self.globals["list"] = "builtin_list"
        self.globals["type"] = "builtin_type"
        self.globals["isinstance"] = "builtin_isinstance"
        self.globals["range"] = "builtin_range"
        self.globals["enumerate"] = "builtin_enumerate"
        self.globals["zip"] = "builtin_zip"
        self.globals["map"] = "builtin_map"
        self.globals["filter"] = "builtin_filter"
        self.globals["sum"] = "builtin_sum"
        self.globals["min"] = "builtin_min"
        self.globals["max"] = "builtin_max"
        self.globals["abs"] = "builtin_abs"
        self.globals["sorted"] = "builtin_sorted"
        self.globals["reversed"] = "builtin_reversed"
        self.globals["any"] = "builtin_any"
        self.globals["all"] = "builtin_all"
        self.globals["True"] = True
        self.globals["False"] = False
        self.globals["None"] = None

    def _builtin_print(self, *args):
        sep = " "
        end = "\n"
        result = sep.join(str(a) for a in args)
        print(result)
        self.output_buffer.append(result + end)
        return None

    def _builtin_input(self, prompt=""):
        if prompt:
            print(prompt, end="")
        return input()

    def _builtin_len(self, obj):
        return len(obj)

    def _builtin_int(self, obj):
        return int(obj)

    def _builtin_float(self, obj):
        return float(obj)

    def _builtin_str(self, obj):
        return str(obj)

    def _builtin_bool(self, obj):
        return bool(obj)

    def _builtin_list(self, obj=None):
        if obj is None:
            return []
        return list(obj)

    def _builtin_type(self, obj):
        return type(obj).__name__

    def _builtin_isinstance(self, obj, type_name):
        if isinstance(type_name, str):
            return type(obj).__name__ == type_name
        return isinstance(obj, type_name)

    def _builtin_range(self, *args):
        return list(range(*args))

    def _builtin_enumerate(self, iterable, start=0):
        return list(enumerate(iterable, start))

    def _builtin_zip(self, *iterables):
        return list(zip(*iterables))

    def _builtin_map(self, func, iterable):
        return list(map(func, iterable))

    def _builtin_filter(self, func, iterable):
        return list(filter(func, iterable))

    def _builtin_sum(self, iterable, start=0):
        return sum(iterable, start)

    def _builtin_min(self, *args):
        return min(*args)

    def _builtin_max(self, *args):
        return max(*args)

    def _builtin_abs(self, obj):
        return abs(obj)

    def _builtin_sorted(self, iterable, key=None, reverse=False):
        return sorted(iterable, key=key, reverse=reverse)

    def _builtin_reversed(self, iterable):
        return list(reversed(iterable))

    def _builtin_any(self, iterable):
        return any(iterable)

    def _builtin_all(self, iterable):
        return all(iterable)

    def _call_builtin(self, name: str, args: list[Any]):
        builtins = {
            "builtin_print": self._builtin_print,
            "builtin_input": self._builtin_input,
            "builtin_len": self._builtin_len,
            "builtin_int": self._builtin_int,
            "builtin_float": self._builtin_float,
            "builtin_str": self._builtin_str,
            "builtin_bool": self._builtin_bool,
            "builtin_list": self._builtin_list,
            "builtin_type": self._builtin_type,
            "builtin_isinstance": self._builtin_isinstance,
            "builtin_range": self._builtin_range,
            "builtin_enumerate": self._builtin_enumerate,
            "builtin_zip": self._builtin_zip,
            "builtin_map": self._builtin_map,
            "builtin_filter": self._builtin_filter,
            "builtin_sum": self._builtin_sum,
            "builtin_min": self._builtin_min,
            "builtin_max": self._builtin_max,
            "builtin_abs": self._builtin_abs,
            "builtin_sorted": self._builtin_sorted,
            "builtin_reversed": self._builtin_reversed,
            "builtin_any": self._builtin_any,
            "builtin_all": self._builtin_all,
        }
        func = builtins.get(name)
        if func is None:
            raise VMError(f"Unknown builtin: {name}")
        return func(*args)

    def _pop(self) -> Any:
        if self.stack:
            return self.stack.pop()
        if self.frames:
            frame = self.frames[-1]
            if frame.stack:
                return frame.stack.pop()
        raise VMError("Stack underflow")

    def _push(self, value: Any):
        self.stack.append(value)

    def _peek(self) -> Any:
        if self.stack:
            return self.stack[-1]
        if self.frames:
            frame = self.frames[-1]
            if frame.stack:
                return frame.stack[-1]
        raise VMError("Stack underflow")

    def run(self, instructions: list[Instruction], constants: list[Any] = None) -> Any:
        if constants is not None:
            self.constants = constants
        else:
            self.constants = []
        self.ip = 0
        self.frames = []
        self.stack = []
        self.result = None
        top_frame = CallFrame(BytecodeFunction(name="<module>", arity=0, instructions=instructions, constants=self.constants if constants is not None else []))
        self.frames.append(top_frame)
        self._execute(instructions)
        if self.stack:
            self.result = self.stack[-1]
        return self.result

    def _execute(self, instructions: list[Instruction]):
        try:
            while self.ip < len(instructions):
                instr = instructions[self.ip]
                self.ip += 1
                self._execute_instruction(instr, instructions)
        except _ReturnSignal:
            raise
        except CosmicRuntimeError as exc:
            if self._exception_handlers:
                handler_ip = self._exception_handlers[-1]
                self._exception_handlers.pop()
                self._push(str(exc))
                self.ip = handler_ip
                self._execute(instructions)
            else:
                raise

    def _execute_instruction(self, instr: Instruction, instructions: list[Instruction]):
        op = instr.op
        arg = instr.arg

        if op == Op.HALT:
            if self.stack:
                self.result = self.stack[-1]
            return

        elif op == Op.LOAD_CONST:
            self._push(self.constants[arg])

        elif op == Op.LOAD_NULL:
            self._push(None)

        elif op == Op.LOAD_TRUE:
            self._push(True)

        elif op == Op.LOAD_FALSE:
            self._push(False)

        elif op == Op.LOAD_LOCAL:
            if self.frames:
                frame = self.frames[-1]
                if arg < len(frame.locals):
                    self._push(frame.locals[arg])
                else:
                    raise VMError(f"Local variable index {arg} out of range")
            else:
                raise VMError("No active frame for LOAD_LOCAL")

        elif op == Op.STORE_LOCAL:
            value = self._pop()
            if self.frames:
                frame = self.frames[-1]
                while len(frame.locals) <= arg:
                    frame.locals.append(None)
                frame.locals[arg] = value
            else:
                raise VMError("No active frame for STORE_LOCAL")

        elif op == Op.LOAD_GLOBAL:
            if isinstance(arg, str) and arg in self.globals:
                self._push(self.globals[arg])
            else:
                raise VMError(f"Undefined global: {arg}")

        elif op == Op.STORE_GLOBAL:
            value = self._pop()
            if isinstance(arg, str):
                self.globals[arg] = value

        elif op == Op.LOAD_ATTR:
            obj = self._pop()
            if isinstance(obj, dict) and isinstance(arg, str):
                if arg in obj:
                    self._push(obj[arg])
                else:
                    self._push(None)
            elif hasattr(obj, arg):
                self._push(getattr(obj, arg))
            elif isinstance(obj, str) and hasattr(str, arg):
                self._push(getattr(str, arg))
            else:
                raise VMError(f"Attribute '{arg}' not found on {type(obj).__name__}")

        elif op == Op.STORE_ATTR:
            value = self._pop()
            obj = self._pop()
            if isinstance(obj, dict) and isinstance(arg, str):
                obj[arg] = value
            elif hasattr(obj, '__dict__'):
                setattr(obj, arg, value)
            else:
                raise VMError(f"Cannot set attribute '{arg}' on {type(obj).__name__}")

        elif op == Op.BINARY_OP:
            right = self._pop()
            left = self._pop()
            result = self._apply_binary_op(arg, left, right)
            self._push(result)

        elif op == Op.UNARY_OP:
            operand = self._pop()
            result = self._apply_unary_op(arg, operand)
            self._push(result)

        elif op == Op.JUMP:
            self.ip = arg

        elif op == Op.JUMP_IF_FALSE:
            value = self._pop()
            if not value:
                self.ip = arg

        elif op == Op.JUMP_IF_TRUE:
            value = self._pop()
            if value:
                self.ip = arg

        elif op == Op.JUMP_IF_NOT_NULL:
            value = self._peek()
            if value is not None:
                self.ip = arg
            else:
                self._pop()

        elif op == Op.CALL:
            n_args = arg
            args = []
            for _ in range(n_args):
                args.insert(0, self._pop())
            callee = self._pop()
            if isinstance(callee, str) and callee.startswith("builtin_"):
                result = self._call_builtin(callee, args)
                self._push(result)
            elif isinstance(callee, BytecodeFunction):
                self._call_function(callee, args)
            elif callable(callee):
                result = callee(*args)
                self._push(result)
            else:
                raise VMError(f"Cannot call {type(callee).__name__}")

        elif op == Op.CALL_METHOD:
            method_name, n_args = arg
            args = []
            for _ in range(n_args):
                args.insert(0, self._pop())
            receiver = self._pop()
            if isinstance(receiver, dict):
                method = receiver.get(method_name)
                if callable(method):
                    result = method(receiver, *args)
                    self._push(result)
                else:
                    self._push(method)
            elif hasattr(receiver, method_name):
                method = getattr(receiver, method_name)
                if callable(method):
                    result = method(*args)
                    self._push(result)
                else:
                    self._push(method)
            else:
                raise VMError(f"Method '{method_name}' not found on {type(receiver).__name__}")

        elif op == Op.RETURN:
            result = self._pop()
            self._push(result)
            raise _ReturnSignal(result)

        elif op == Op.MAKE_FUNCTION:
            func = self.constants[arg]
            self._push(func)

        elif op == Op.MAKE_CLOSURE:
            func = self.constants[arg]
            self._push(func)

        elif op == Op.MAKE_LIST:
            elements = []
            for _ in range(arg):
                elements.insert(0, self._pop())
            self._push(elements)

        elif op == Op.MAKE_DICT:
            pairs = {}
            for _ in range(arg):
                value = self._pop()
                key = self._pop()
                pairs[key] = value
            self._push(pairs)

        elif op == Op.MAKE_SET:
            elements = set()
            for _ in range(arg):
                elements.add(self._pop())
            self._push(elements)

        elif op == Op.MAKE_TUPLE:
            elements = []
            for _ in range(arg):
                elements.insert(0, self._pop())
            self._push(tuple(elements))

        elif op == Op.INDEX:
            index = self._pop()
            obj = self._pop()
            if isinstance(obj, list) and isinstance(index, int):
                if 0 <= index < len(obj):
                    self._push(obj[index])
                else:
                    raise VMError(f"Index {index} out of range for list of length {len(obj)}")
            elif isinstance(obj, dict):
                if index in obj:
                    self._push(obj[index])
                else:
                    raise VMError(f"Key {index!r} not found in dict")
            elif isinstance(obj, str) and isinstance(index, int):
                if 0 <= index < len(obj):
                    self._push(obj[index])
                else:
                    raise VMError(f"Index {index} out of range for string of length {len(obj)}")
            else:
                raise VMError(f"Cannot index {type(obj).__name__}")

        elif op == Op.SLICE:
            step = self._pop()
            end = self._pop()
            start = self._pop()
            obj = self._pop()
            if isinstance(obj, (list, str, tuple)):
                s = slice(start, end, step)
                self._push(obj[s])
            else:
                raise VMError(f"Cannot slice {type(obj).__name__}")

        elif op == Op.ITER_NEXT:
            iter_var = arg
            if self.frames:
                frame = self.frames[-1]
                if iter_var < len(frame.locals):
                    iterator = frame.locals[iter_var]
                    if isinstance(iterator, _IteratorWrapper):
                        value = iterator.next()
                        self._push(value)
                    elif hasattr(iterator, '__iter__'):
                        try:
                            value = next(iterator)
                            self._push(value)
                        except StopIteration:
                            self._push(None)
                    else:
                        self._push(None)

        elif op == Op.ITER_HAS_NEXT:
            iter_var = arg
            if self.frames:
                frame = self.frames[-1]
                if iter_var < len(frame.locals):
                    iterator = frame.locals[iter_var]
                    if isinstance(iterator, _IteratorWrapper):
                        self._push(iterator.has_next())
                    elif hasattr(iterator, '__iter__'):
                        wrapped = _IteratorWrapper(iterator)
                        frame.locals[iter_var] = wrapped
                        self._push(wrapped.has_next())
                    else:
                        self._push(False)

        elif op == Op.POP_TOP:
            self._pop()

        elif op == Op.DUP_TOP:
            val = self._peek()
            self._push(val)

        elif op == Op.RAISE:
            exc = self._pop()
            raise CosmicRuntimeError(str(exc))

        elif op == Op.TRY_START:
            self._exception_handlers.append(arg)

        elif op == Op.TRY_END:
            if self._exception_handlers:
                self._exception_handlers.pop()

        elif op == Op.CATCH_START:
            exc_value = self._pop()
            self._exception_handlers.pop() if self._exception_handlers else None
            self._push(exc_value)

        elif op == Op.IMPORT_NAME:
            self._push(None)

        elif op == Op.IMPORT_FROM:
            pass

        elif op == Op.YIELD:
            value = self._pop()
            self._push(value)

        elif op == Op.AWAIT:
            value = self._pop()
            self._push(value)

        elif op == Op.MAKE_CLASS:
            class_name = arg
            body_val = self._pop()
            bases_val = self._pop() if self.stack else None
            class_dict = {}
            if isinstance(body_val, dict):
                class_dict = body_val
            new_class = type(class_name, (object,), class_dict)
            self._push(new_class)

        elif op == Op.MAKE_RECORD:
            record_name, field_names = arg
            values = {}
            for fn in reversed(field_names):
                values[fn] = self._pop()
            self._push(values)

        elif op == Op.MAKE_ENUM:
            enum_name, variants_info = arg
            enum_class = {}
            for vname, vfields in variants_info:
                enum_class[vname] = vname
            self._push(enum_class)

        else:
            raise VMError(f"Unknown opcode: {op}")

    def _apply_binary_op(self, op: int, left: Any, right: Any) -> Any:
        ops = {
            BinaryOp.ADD: lambda l, r: l + r,
            BinaryOp.SUB: lambda l, r: l - r,
            BinaryOp.MUL: lambda l, r: l * r,
            BinaryOp.DIV: lambda l, r: l / r,
            BinaryOp.MOD: lambda l, r: l % r,
            BinaryOp.POW: lambda l, r: l ** r,
            BinaryOp.FLOOR_DIV: lambda l, r: l // r,
            BinaryOp.EQ: lambda l, r: l == r,
            BinaryOp.NEQ: lambda l, r: l != r,
            BinaryOp.LT: lambda l, r: l < r,
            BinaryOp.GT: lambda l, r: l > r,
            BinaryOp.LTE: lambda l, r: l <= r,
            BinaryOp.GTE: lambda l, r: l >= r,
            BinaryOp.AND: lambda l, r: l and r,
            BinaryOp.OR: lambda l, r: l or r,
            BinaryOp.BIT_AND: lambda l, r: l & r,
            BinaryOp.BIT_OR: lambda l, r: l | r,
            BinaryOp.BIT_XOR: lambda l, r: l ^ r,
            BinaryOp.LSHIFT: lambda l, r: l << r,
            BinaryOp.RSHIFT: lambda l, r: l >> r,
        }
        func = ops.get(op)
        if func:
            try:
                return func(left, right)
            except Exception as e:
                raise VMError(f"Binary operation error: {e}")
        raise VMError(f"Unknown binary op: {op}")

    def _apply_unary_op(self, op: int, operand: Any) -> Any:
        ops = {
            UnaryOp.NEG: lambda x: -x,
            UnaryOp.NOT: lambda x: not x,
            UnaryOp.BIT_NOT: lambda x: ~x,
        }
        func = ops.get(op)
        if func:
            try:
                return func(operand)
            except Exception as e:
                raise VMError(f"Unary operation error: {e}")
        raise VMError(f"Unknown unary op: {op}")

    def _call_function(self, func: BytecodeFunction, args: list[Any]):
        if len(args) != func.arity:
            raise VMError(f"{func.name}() takes {func.arity} arguments but {len(args)} were given")
        new_frame = CallFrame(func)
        new_frame.locals = list(args)
        while len(new_frame.locals) < len(func.local_names):
            new_frame.locals.append(None)
        self.frames.append(new_frame)
        old_stack = self.stack
        self.stack = new_frame.stack
        old_ip = self.ip
        old_constants = self.constants
        self.constants = func.constants
        self.ip = 0
        try:
            self._execute(func.instructions)
        except _ReturnSignal as ret:
            self.frames.pop()
            self.stack = old_stack
            self.ip = old_ip
            self.constants = old_constants
            self._push(ret.value)
        else:
            result = self.stack[-1] if self.stack else None
            self.frames.pop()
            self.stack = old_stack
            self.ip = old_ip
            self.constants = old_constants
            self._push(result)


# ─── Public API ──────────────────────────────────────────────────────────

def compile(ast: Program) -> tuple[list[Instruction], list[Any]]:
    compiler = BytecodeCompiler()
    instructions, constants = compiler.compile(ast)
    return instructions, constants


def run(bytecode: tuple[list[Instruction], list[Any]] = None, instructions=None, constants=None) -> Any:
    if bytecode is not None:
        instructions, constants = bytecode
    vm = CosmicVM()
    return vm.run(instructions, constants)
