"""Python transpiler for the Cosmic language."""
from __future__ import annotations
from ...ast.nodes import *


class PythonTranspiler:
    """Transpiles a Cosmic AST into Python source code."""

    def __init__(self) -> None:
        self._indent = 0
        self._indent_str = "    "
        self._output: list[str] = []
        self._pending_imports: list[str] = []

    # ── helpers ────────────────────────────────────────────────────────

    def _line(self, text: str = "") -> None:
        if text:
            self._output.append(f"{self._indent * self._indent_str}{text}")
        else:
            self._output.append("")

    def _indent_block(self) -> None:
        self._indent += 1

    def _dedent_block(self) -> None:
        self._indent -= 1

    def _emit_block(self, node: ASTNode) -> None:
        if isinstance(node, Block):
            if not node.statements:
                self._line("pass")
            else:
                for stmt in node.statements:
                    result = self.visit(stmt)
                    if isinstance(result, str) and result and not self._emits_own_line(stmt):
                        self._line(result)
        else:
            result = self.visit(node)
            if isinstance(result, str) and result and not self._emits_own_line(node):
                self._line(result)

    def _emits_own_line(self, node: ASTNode) -> bool:
        """Return True if the node already calls _line() internally."""
        return isinstance(node, (
            ExprStmt, AssignStmt, AugAssignStmt, LetStmt,
            ReturnStmt, BreakStmt, ContinueStmt,
            IfStmt, WhileStmt, ForStmt, LoopStmt,
            RaiseStmt, TryStmt, AssertStmt,
            FnDecl, ClassDecl, RecordDecl, EnumDecl,
            InterfaceDecl, TypeAlias, ModuleDecl,
            ImportDecl, FromImportDecl, TestDecl,
            Block,
        ))

    def _emit_expr(self, node: ASTNode) -> str:
        return self.visit(node)

    def _type_ref(self, ref) -> str:
        if ref is None:
            return ""

        if isinstance(ref, UnionType):
            parts = [self._type_ref(t) for t in ref.types]
            return " | ".join(parts)

        if isinstance(ref, TupleType):
            parts = [self._type_ref(t) for t in ref.types]
            return f"tuple[{', '.join(parts)}]"

        if isinstance(ref, FuncType):
            params = [self._type_ref(p) for p in ref.params]
            ret = self._type_ref(ref.return_type) if ref.return_type else "None"
            return f"Callable[[{', '.join(params)}], {ret}]"

        if ref.is_list:
            inner = self._type_ref(ref.type_args[0]) if ref.type_args else "Any"
            result = f"list[{inner}]"
        elif ref.is_dict:
            key = self._type_ref(ref.dict_key) if ref.dict_key else "Any"
            val = self._type_ref(ref.type_args[0]) if ref.type_args else "Any"
            result = f"dict[{key}, {val}]"
        else:
            name = ref.name
            mapping = {
                "int": "int",
                "float": "float",
                "str": "str",
                "bool": "bool",
                "none": "None",
                "any": "Any",
            }
            name = mapping.get(name, name)
            if ref.type_args:
                args = ", ".join(self._type_ref(a) for a in ref.type_args)
                result = f"{name}[{args}]"
            else:
                result = name

        if ref.nullable:
            result = f"{result} | None"

        return result

    def _params(self, params: list[Param]) -> str:
        parts: list[str] = []
        for p in params:
            s = p.name
            if p.type_ref:
                s += f": {self._type_ref(p.type_ref)}"
            if p.default is not None:
                s += f" = {self._emit_expr(p.default)}"
            parts.append(s)
        return ", ".join(parts)

    def _add_pending_import(self, imp: str) -> None:
        if imp not in self._pending_imports:
            self._pending_imports.append(imp)

    # ── public API ─────────────────────────────────────────────────────

    def transpile(self, program: Program) -> str:
        self._indent = 0
        self._output = []
        self._pending_imports = []

        for stmt in program.statements:
            self.visit(stmt)

        lines: list[str] = []
        if self._pending_imports:
            for imp in self._pending_imports:
                lines.append(imp)
            lines.append("")
        lines.extend(self._output)
        return "\n".join(lines) + "\n"

    # ── visit dispatch ─────────────────────────────────────────────────

    def visit(self, node: ASTNode) -> str | None:
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method:
            return method(node)
        return self.generic_visit(node)

    def generic_visit(self, node: ASTNode) -> str:
        raise NotImplementedError(
            f"PythonTranspiler has no visit method for {type(node).__name__}"
        )

    # ── expressions ────────────────────────────────────────────────────

    def visit_IntLiteral(self, node: IntLiteral) -> str:
        return str(node.value)

    def visit_FloatLiteral(self, node: FloatLiteral) -> str:
        return repr(node.value)

    def visit_StringLiteral(self, node: StringLiteral) -> str:
        return repr(node.value)

    def visit_BoolLiteral(self, node: BoolLiteral) -> str:
        return "True" if node.value else "False"

    def visit_NoneLiteral(self, node: NoneLiteral) -> str:
        return "None"

    def visit_CharLiteral(self, node: CharLiteral) -> str:
        return repr(node.value)

    def visit_Identifier(self, node: Identifier) -> str:
        return node.name

    def visit_SelfExpr(self, node: SelfExpr) -> str:
        return "self"

    def visit_SuperExpr(self, node: SuperExpr) -> str:
        method_map = {
            "init": "__init__", "str": "__str__", "repr": "__repr__",
            "eq": "__eq__", "lt": "__lt__", "le": "__le__",
            "gt": "__gt__", "ge": "__ge__", "hash": "__hash__",
            "len": "__len__", "getitem": "__getitem__", "setitem": "__setitem__",
            "iter": "__iter__", "next": "__next__", "call": "__call__",
        }
        method = method_map.get(node.method, node.method)
        return f"super().{method}"

    def visit_BinaryExpr(self, node: BinaryExpr) -> str:
        op = node.op
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right)

        parenthesize = (BinaryExpr, IfExpr, LambdaExpr, UnaryExpr,
                        PipeExpr, NullishCoalesceExpr, AwaitExpr, YieldExpr)
        if isinstance(node.left, parenthesize):
            left = f"({left})"
        if isinstance(node.right, parenthesize):
            right = f"({right})"

        return f"{left} {op} {right}"

    def visit_UnaryExpr(self, node: UnaryExpr) -> str:
        operand = self._emit_expr(node.operand)
        if node.prefix:
            if node.op == "not":
                return f"not {operand}"
            if node.op == "not not":
                return f"not not {operand}"
            return f"{node.op}{operand}"
        return f"{operand}{node.op}"

    def visit_CallExpr(self, node: CallExpr) -> str:
        callee = self._emit_expr(node.callee)
        args = [self._emit_expr(a) for a in node.args]
        kwargs = [f"{k}={self._emit_expr(v)}" for k, v in node.kwargs.items()]
        all_args = args + kwargs
        return f"{callee}({', '.join(all_args)})"

    def visit_MethodCallExpr(self, node: MethodCallExpr) -> str:
        obj = self._emit_expr(node.object)
        args = [self._emit_expr(a) for a in node.args]
        kwargs = [f"{k}={self._emit_expr(v)}" for k, v in node.kwargs.items()]
        all_args = args + kwargs
        return f"{obj}.{node.method}({', '.join(all_args)})"

    def visit_PropertyAccessExpr(self, node: PropertyAccessExpr) -> str:
        obj = self._emit_expr(node.object)
        return f"{obj}.{node.property}"

    def visit_IndexExpr(self, node: IndexExpr) -> str:
        obj = self._emit_expr(node.object)
        idx = self._emit_expr(node.index)
        return f"{obj}[{idx}]"

    def visit_SliceExpr(self, node: SliceExpr) -> str:
        obj = self._emit_expr(node.object)
        start = self._emit_expr(node.start) if node.start is not None else ""
        end = self._emit_expr(node.end) if node.end is not None else ""
        step = self._emit_expr(node.step) if node.step is not None else ""

        parts = [start, end]
        if step:
            parts.append(step)
        return f"{obj}[{':'.join(parts)}]"

    def visit_LambdaExpr(self, node: LambdaExpr) -> str:
        params = ", ".join(p.name for p in node.params)
        body = self._emit_expr(node.body)
        return f"lambda {params}: {body}"

    def visit_ListExpr(self, node: ListExpr) -> str:
        elements = [self._emit_expr(e) for e in node.elements]
        return f"[{', '.join(elements)}]"

    def visit_DictExpr(self, node: DictExpr) -> str:
        pairs = []
        for k, v in zip(node.keys, node.values):
            pairs.append(f"{self._emit_expr(k)}: {self._emit_expr(v)}")
        return "{" + ", ".join(pairs) + "}"

    def visit_SetExpr(self, node: SetExpr) -> str:
        elements = [self._emit_expr(e) for e in node.elements]
        return "{" + ", ".join(elements) + "}"

    def visit_TupleExpr(self, node: TupleExpr) -> str:
        elements = [self._emit_expr(e) for e in node.elements]
        if len(elements) == 1:
            return f"({elements[0]},)"
        return f"({', '.join(elements)})"

    def visit_IfExpr(self, node: IfExpr) -> str:
        cond = self._emit_expr(node.condition)
        then = self._emit_expr(node.then_body)
        result = f"{then} if {cond} else "
        if node.elif_branches:
            elif_parts = []
            for elif_cond, elif_body in node.elif_branches:
                c = self._emit_expr(elif_cond)
                b = self._emit_expr(elif_body)
                elif_parts.append((c, b))
            else_body = self._emit_expr(node.else_body) if node.else_body else "None"
            inner = else_body
            for c, b in reversed(elif_parts):
                inner = f"{b} if {c} else {inner}"
            result += inner
        elif node.else_body:
            result += self._emit_expr(node.else_body)
        else:
            result += "None"
        return result

    def visit_MatchExpr(self, node: MatchExpr) -> str:
        val = self._emit_expr(node.value)
        lines: list[str] = [f"match {val}:"]
        self._indent_block()
        for case in node.cases:
            pat = self._emit_expr(case.pattern)
            if case.guard:
                guard = self._emit_expr(case.guard)
                lines.append(f"{self._indent * self._indent_str}case {pat} if {guard}:")
            else:
                lines.append(f"{self._indent * self._indent_str}case {pat}:")
            self._indent_block()
            if isinstance(case.body, Block):
                if case.body.statements:
                    for stmt in case.body.statements:
                        result = self.visit(stmt)
                        if isinstance(result, str) and result and not self._emits_own_line(stmt):
                            lines.append(f"{self._indent * self._indent_str}{result}")
                        elif not result:
                            pass
                else:
                    lines.append(f"{self._indent * self._indent_str}pass")
            else:
                lines.append(f"{self._indent * self._indent_str}{self._emit_expr(case.body)}")
            self._dedent_block()
        self._dedent_block()
        return "\n".join(lines)

    def visit_IsExpr(self, node: IsExpr) -> str:
        val = self._emit_expr(node.value)
        typ = self._type_ref(node.type_ref)
        return f"isinstance({val}, {typ})"

    def visit_AsExpr(self, node: AsExpr) -> str:
        val = self._emit_expr(node.value)
        typ = self._type_ref(node.type_ref)
        return f"{typ}({val})"

    def visit_PipeExpr(self, node: PipeExpr) -> str:
        left = self._emit_expr(node.left)
        right = node.right
        if isinstance(right, Identifier):
            return f"{right.name}({left})"
        elif isinstance(right, CallExpr):
            callee = self._emit_expr(right.callee)
            args = [left] + [self._emit_expr(a) for a in right.args]
            kwargs = [f"{k}={self._emit_expr(v)}" for k, v in right.kwargs.items()]
            all_args = args + kwargs
            return f"{callee}({', '.join(all_args)})"
        else:
            right_str = self._emit_expr(right)
            return f"({right_str})({left})"

    def visit_NullishCoalesceExpr(self, node: NullishCoalesceExpr) -> str:
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right)
        return f"(lambda _l: _l if _l is not None else ({right}))({left})"

    def visit_SpreadExpr(self, node: SpreadExpr) -> str:
        val = self._emit_expr(node.value)
        return f"*{val}"

    def visit_GeneratorExpr(self, node: GeneratorExpr) -> str:
        elem = self._emit_expr(node.element)
        iter_expr = self._emit_expr(node.iter_expr)
        var = node.var or "_"
        if node.condition:
            cond = self._emit_expr(node.condition)
            return f"({elem} for {var} in {iter_expr} if {cond})"
        return f"({elem} for {var} in {iter_expr})"

    def visit_AwaitExpr(self, node: AwaitExpr) -> str:
        val = self._emit_expr(node.value)
        return f"await {val}"

    def visit_YieldExpr(self, node: YieldExpr) -> str:
        if node.value is not None:
            val = self._emit_expr(node.value)
            return f"yield {val}"
        return "yield"

    def visit_TypeOfExpr(self, node: TypeOfExpr) -> str:
        val = self._emit_expr(node.value)
        return f"type({val})"

    def visit_FuncType(self, node: FuncType) -> str:
        return self._type_ref(node)

    def visit_UnionType(self, node: UnionType) -> str:
        return self._type_ref(node)

    def visit_TupleType(self, node: TupleType) -> str:
        return self._type_ref(node)

    # ── statements ─────────────────────────────────────────────────────

    def visit_ExprStmt(self, node: ExprStmt) -> str:
        expr = self._emit_expr(node.expr)
        if expr:
            self._line(expr)
        return ""

    def visit_AssignStmt(self, node: AssignStmt) -> str:
        target = self._emit_expr(node.target)
        value = self._emit_expr(node.value)
        self._line(f"{target} {node.op} {value}")
        return ""

    def visit_AugAssignStmt(self, node: AugAssignStmt) -> str:
        target = self._emit_expr(node.target)
        value = self._emit_expr(node.value)
        self._line(f"{target} {node.op} {value}")
        return ""

    def visit_LetStmt(self, node: LetStmt) -> str:
        value = self._emit_expr(node.value) if node.value is not None else "None"
        self._line(f"{node.name} = {value}")
        return ""

    def visit_ReturnStmt(self, node: ReturnStmt) -> str:
        if node.value is not None:
            val = self._emit_expr(node.value)
            self._line(f"return {val}")
        else:
            self._line("return")
        return ""

    def visit_BreakStmt(self, node: BreakStmt) -> str:
        self._line("break")
        return ""

    def visit_ContinueStmt(self, node: ContinueStmt) -> str:
        self._line("continue")
        return ""

    def visit_IfStmt(self, node: IfStmt) -> str:
        cond = self._emit_expr(node.condition)
        self._line(f"if {cond}:")
        self._indent_block()
        self._emit_block(node.then_body)
        self._dedent_block()

        for elif_cond, elif_body in node.elif_branches:
            cond = self._emit_expr(elif_cond)
            self._line(f"elif {cond}:")
            self._indent_block()
            self._emit_block(elif_body)
            self._dedent_block()

        if node.else_body:
            self._line("else:")
            self._indent_block()
            self._emit_block(node.else_body)
            self._dedent_block()

        return ""

    def visit_WhileStmt(self, node: WhileStmt) -> str:
        cond = self._emit_expr(node.condition)
        self._line(f"while {cond}:")
        self._indent_block()
        self._emit_block(node.body)
        self._dedent_block()
        return ""

    def visit_ForStmt(self, node: ForStmt) -> str:
        iter_expr = self._emit_expr(node.iter_expr)
        self._line(f"for {node.var} in {iter_expr}:")
        self._indent_block()
        self._emit_block(node.body)
        self._dedent_block()
        return ""

    def visit_LoopStmt(self, node: LoopStmt) -> str:
        self._line("while True:")
        self._indent_block()
        self._emit_block(node.body)
        self._dedent_block()
        return ""

    def visit_RaiseStmt(self, node: RaiseStmt) -> str:
        if node.value is not None:
            val = self._emit_expr(node.value)
            self._line(f"raise {val}")
        else:
            self._line("raise")
        return ""

    def visit_TryStmt(self, node: TryStmt) -> str:
        self._line("try:")
        self._indent_block()
        self._emit_block(node.body)
        self._dedent_block()

        for clause in node.catch_clauses:
            parts: list[str] = []
            if clause.type_ref:
                parts.append(self._type_ref(clause.type_ref))
            if clause.var_name:
                parts.append(clause.var_name)
            catch_arg = " as ".join(parts)
            if catch_arg:
                self._line(f"except {catch_arg}:")
            else:
                self._line("except:")
            self._indent_block()
            self._emit_block(clause.body)
            self._dedent_block()

        if node.finally_body:
            self._line("finally:")
            self._indent_block()
            self._emit_block(node.finally_body)
            self._dedent_block()

        return ""

    def visit_AssertStmt(self, node: AssertStmt) -> str:
        cond = self._emit_expr(node.condition)
        if node.message:
            msg = self._emit_expr(node.message)
            self._line(f"assert {cond}, {msg}")
        else:
            self._line(f"assert {cond}")
        return ""

    def visit_Block(self, node: Block) -> str:
        self._emit_block(node)
        return ""

    # ── declarations ───────────────────────────────────────────────────

    def visit_FnDecl(self, node: FnDecl) -> str:
        prefix = "async " if node.is_async else ""
        params = self._params(node.params)
        ret = f" -> {self._type_ref(node.return_type)}" if node.return_type else ""

        for decorator in node.decorators:
            dec = self._emit_expr(decorator)
            self._line(f"@{dec}")

        self._line(f"{prefix}def {node.name}({params}){ret}:")

        self._indent_block()
        if node.body:
            self._emit_block(node.body)
        else:
            self._line("pass")
        self._dedent_block()

        return ""

    def visit_ClassDecl(self, node: ClassDecl) -> str:
        bases = ", ".join(self._type_ref(b) for b in node.bases)
        header = f"class {node.name}"
        if bases:
            header += f"({bases})"
        header += ":"
        self._line(header)
        self._indent_block()

        if node.body and isinstance(node.body, Block):
            if not node.body.statements:
                self._line("pass")
            else:
                self._emit_block(node.body)
        else:
            self._line("pass")

        self._dedent_block()
        return ""

    def visit_RecordDecl(self, node: RecordDecl) -> str:
        self._add_pending_import("from dataclasses import dataclass")

        self._line(f"@dataclass")
        self._line(f"class {node.name}:")

        self._indent_block()

        if node.fields:
            for f in node.fields:
                s = f.name
                if f.type_ref:
                    s += f": {self._type_ref(f.type_ref)}"
                else:
                    s += ": Any"
                if f.default is not None:
                    s += f" = {self._emit_expr(f.default)}"
                self._line(s)
        else:
            self._line("pass")

        for method in node.methods:
            self.visit(method)

        self._dedent_block()
        return ""

    def visit_EnumDecl(self, node: EnumDecl) -> str:
        self._add_pending_import("from enum import Enum")
        self._add_pending_import("from enum import auto")

        self._line(f"class {node.name}(Enum):")

        self._indent_block()

        if not node.variants:
            self._line("pass")
        else:
            for variant in node.variants:
                if variant.value is not None:
                    val = self._emit_expr(variant.value)
                    self._line(f"{variant.name} = {val}")
                elif variant.fields:
                    self._line(f"{variant.name} = auto()")
                else:
                    self._line(f"{variant.name} = auto()")

        self._dedent_block()
        return ""

    def visit_InterfaceDecl(self, node: InterfaceDecl) -> str:
        self._add_pending_import("from typing import Protocol")

        self._line(f"class {node.name}(Protocol):")
        self._indent_block()

        if not node.methods:
            self._line("pass")
        else:
            for method in node.methods:
                self.visit(method)

        self._dedent_block()
        return ""

    def visit_TypeAlias(self, node: TypeAlias) -> str:
        typ = self._type_ref(node.type_ref)
        self._line(f"{node.name} = {typ}")
        return ""

    def visit_ModuleDecl(self, node: ModuleDecl) -> str:
        self._line(f"# Module: {node.name}")
        for stmt in node.body:
            self.visit(stmt)
        return ""

    def visit_ImportDecl(self, node: ImportDecl) -> str:
        if node.names:
            names = ", ".join(node.names)
            line = f"from {node.module} import {names}"
        else:
            line = f"import {node.module}"
        if node.alias:
            line += f" as {node.alias}"
        self._line(line)
        return ""

    def visit_FromImportDecl(self, node: FromImportDecl) -> str:
        parts: list[str] = []
        for name, alias in node.names:
            if alias:
                parts.append(f"{name} as {alias}")
            else:
                parts.append(name)
        names = ", ".join(parts)
        line = f"from {node.module} import {names}"
        self._line(line)
        return ""

    def visit_TestDecl(self, node: TestDecl) -> str:
        test_name = f"test_{node.name.replace(' ', '_').replace('-', '_')}"
        self._line(f"def {test_name}():")
        self._indent_block()
        if node.body:
            self._emit_block(node.body)
        else:
            self._line("pass")
        self._dedent_block()
        return ""


def transpile(program: Program) -> str:
    """Transpile a Cosmic Program AST into Python source code."""
    transpiler = PythonTranspiler()
    return transpiler.transpile(program)
