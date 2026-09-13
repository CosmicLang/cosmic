"""Type checker for the Cosmic language."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List, Set, Tuple, Union, Callable


from ..ast.nodes import *


class TypeCheckError(Exception):
    """Raised when a type error is encountered."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


@dataclass
class TypeInfo:
    """Represents type information for an AST node."""
    name: str
    type_args: List['TypeInfo'] = field(default_factory=list)
    nullable: bool = False
    is_function: bool = False
    param_types: List['TypeInfo'] = field(default_factory=list)
    return_type: Optional['TypeInfo'] = None
    is_generic: bool = False
    generic_params: List[str] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypeInfo):
            return False
        return (self.name == other.name and
                self.type_args == other.type_args and
                self.nullable == other.nullable)

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.type_args), self.nullable))

    def __repr__(self) -> str:
        if self.is_function:
            params = ", ".join(str(p) for p in self.param_types)
            return f"({params}) -> {self.return_type}"
        if self.type_args:
            args = ", ".join(str(a) for a in self.type_args)
            return f"{self.name}[{args}]"
        if self.nullable:
            return f"{self.name}?"
        return self.name


class SymbolTable:
    """Symbol table for storing variable and function type information."""

    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, TypeInfo] = {}
        self.constants: Set[str] = set()
        self.functions: Dict[str, 'FunctionSignature'] = {}
        self.classes: Dict[str, 'ClassInfo'] = {}
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
        self.in_loop: bool = False

    def define(self, name: str, type_info: TypeInfo, is_const: bool = False) -> None:
        self.symbols[name] = type_info
        if is_const:
            self.constants.add(name)

    def lookup(self, name: str) -> Optional[TypeInfo]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def is_defined(self, name: str) -> bool:
        if name in self.symbols:
            return True
        if self.parent:
            return self.parent.is_defined(name)
        return False

    def is_mutable(self, name: str) -> bool:
        if name in self.constants:
            return False
        if name in self.symbols:
            return True
        if self.parent:
            return self.parent.is_mutable(name)
        return True

    def define_function(self, name: str, sig: 'FunctionSignature') -> None:
        self.functions[name] = sig

    def lookup_function(self, name: str) -> Optional['FunctionSignature']:
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.lookup_function(name)
        return None

    def define_class(self, name: str, info: 'ClassInfo') -> None:
        self.classes[name] = info

    def lookup_class(self, name: str) -> Optional['ClassInfo']:
        if name in self.classes:
            return self.classes[name]
        if self.parent:
            return self.parent.lookup_class(name)
        return None

    def child_scope(self) -> 'SymbolTable':
        child = SymbolTable(parent=self)
        child.current_class = self.current_class
        child.current_function = self.current_function
        child.in_loop = self.in_loop
        return child


@dataclass
class FunctionSignature:
    """Represents a function's type signature."""
    name: str
    param_types: List[TypeInfo]
    param_names: List[str]
    param_defaults: List[Optional[Any]]
    return_type: TypeInfo
    is_async: bool = False
    is_method: bool = False
    self_type: Optional[TypeInfo] = None


@dataclass
class ClassInfo:
    """Represents class type information."""
    name: str
    bases: List[TypeInfo]
    fields: Dict[str, TypeInfo]
    methods: Dict[str, FunctionSignature]
    is_abstract: bool = False
    type_params: List[str] = field(default_factory=list)


class TypeSystem:
    """Built-in type system with common types."""

    def __init__(self):
        self.types: Dict[str, TypeInfo] = {}
        self._setup_builtin_types()

    def _setup_builtin_types(self) -> None:
        self.types['int'] = TypeInfo(name='int')
        self.types['float'] = TypeInfo(name='float')
        self.types['string'] = TypeInfo(name='string')
        self.types['bool'] = TypeInfo(name='bool')
        self.types['none'] = TypeInfo(name='none')
        self.types['any'] = TypeInfo(name='any')
        self.types['object'] = TypeInfo(name='object')
        self.types['list'] = TypeInfo(name='list')
        self.types['dict'] = TypeInfo(name='dict')
        self.types['set'] = TypeInfo(name='set')
        self.types['tuple'] = TypeInfo(name='tuple')
        self.types['char'] = TypeInfo(name='char')

    def get_type(self, name: str) -> TypeInfo:
        if name in self.types:
            return self.types[name]
        return TypeInfo(name=name)

    def register_type(self, name: str, type_info: TypeInfo) -> None:
        self.types[name] = type_info

    def is_numeric(self, type_info: TypeInfo) -> bool:
        return type_info.name in ('int', 'float')

    def is_integer(self, type_info: TypeInfo) -> bool:
        return type_info.name == 'int'

    def is_string(self, type_info: TypeInfo) -> bool:
        return type_info.name == 'string'

    def is_bool(self, type_info: TypeInfo) -> bool:
        return type_info.name == 'bool'

    def is_none(self, type_info: TypeInfo) -> bool:
        return type_info.name == 'none'

    def is_comparable(self, type_info: TypeInfo) -> bool:
        return type_info.name in ('int', 'float', 'string', 'bool', 'none')

    def is_callable(self, type_info: TypeInfo) -> bool:
        return type_info.is_function or type_info.name in ('function',)

    def can_unify(self, t1: TypeInfo, t2: TypeInfo) -> bool:
        if t1 == t2:
            return True
        if t1.name == 'any' or t2.name == 'any':
            return True
        if t1.nullable and t2.name == 'none':
            return True
        if t2.nullable and t1.name == 'none':
            return True
        if self.is_numeric(t1) and self.is_numeric(t2):
            return True
        return False

    def unify(self, t1: TypeInfo, t2: TypeInfo) -> TypeInfo:
        if t1 == t2:
            return t1
        if t1.name == 'any':
            return t2
        if t2.name == 'any':
            return t1
        if t1.nullable and t2.name == 'none':
            return t1
        if t2.nullable and t1.name == 'none':
            return t2
        if self.is_numeric(t1) and self.is_numeric(t2):
            if t1.name == 'float' or t2.name == 'float':
                return self.types['float']
            return self.types['int']
        return self.types['any']

    def get_element_type(self, collection: TypeInfo) -> Optional[TypeInfo]:
        if collection.type_args:
            return collection.type_args[0]
        if collection.name == 'list':
            return self.types['any']
        if collection.name == 'set':
            return self.types['any']
        if collection.name == 'tuple' and collection.type_args:
            return collection.type_args[0]
        return None

    def get_dict_types(self, collection: TypeInfo) -> Tuple[Optional[TypeInfo], Optional[TypeInfo]]:
        if collection.type_args and len(collection.type_args) >= 2:
            return collection.type_args[0], collection.type_args[1]
        if collection.name == 'dict':
            return self.types['any'], self.types['any']
        return None, None


class TypeChecker:
    """Type checker for the Cosmic language."""

    def __init__(self):
        self.type_system = TypeSystem()
        self.symbol_table = SymbolTable()
        self.type_map: Dict[int, TypeInfo] = {}
        self.errors: List[TypeCheckError] = []
        self._setup_builtin_functions()
        self._current_return_type: Optional[TypeInfo] = None
        self._async_context: bool = False

    def _setup_builtin_functions(self) -> None:
        self.symbol_table.define_function('print', FunctionSignature(
            name='print',
            param_types=[self.type_system.types['any']],
            param_names=['value'],
            param_defaults=[None],
            return_type=self.type_system.types['none']
        ))
        self.symbol_table.define_function('len', FunctionSignature(
            name='len',
            param_types=[self.type_system.types['any']],
            param_names=['collection'],
            param_defaults=[None],
            return_type=self.type_system.types['int']
        ))
        self.symbol_table.define_function('range', FunctionSignature(
            name='range',
            param_types=[self.type_system.types['int'], self.type_system.types['int'], self.type_system.types['int']],
            param_names=['start', 'stop', 'step'],
            param_defaults=[None, None, None],
            return_type=TypeInfo(name='list', type_args=[self.type_system.types['int']])
        ))
        self.symbol_table.define_function('int', FunctionSignature(
            name='int',
            param_types=[self.type_system.types['any']],
            param_names=['value'],
            param_defaults=[None],
            return_type=self.type_system.types['int']
        ))
        self.symbol_table.define_function('float', FunctionSignature(
            name='float',
            param_types=[self.type_system.types['any']],
            param_names=['value'],
            param_defaults=[None],
            return_type=self.type_system.types['float']
        ))
        self.symbol_table.define_function('string', FunctionSignature(
            name='string',
            param_types=[self.type_system.types['any']],
            param_names=['value'],
            param_defaults=[None],
            return_type=self.type_system.types['string']
        ))
        self.symbol_table.define_function('bool', FunctionSignature(
            name='bool',
            param_types=[self.type_system.types['any']],
            param_names=['value'],
            param_defaults=[None],
            return_type=self.type_system.types['bool']
        ))
        self.symbol_table.define_function('input', FunctionSignature(
            name='input',
            param_types=[self.type_system.types['string']],
            param_names=['prompt'],
            param_defaults=[None],
            return_type=self.type_system.types['string']
        ))

    def check(self, program: Program) -> Dict[int, TypeInfo]:
        self.visit(program)
        return self.type_map

    def _error(self, message: str, node: ASTNode) -> None:
        error = TypeCheckError(message, node.line, node.column)
        self.errors.append(error)

    def _set_type(self, node: ASTNode, type_info: TypeInfo) -> TypeInfo:
        self.type_map[id(node)] = type_info
        return type_info

    def _get_type(self, node: ASTNode) -> Optional[TypeInfo]:
        return self.type_map.get(id(node))

    def _resolve_type_ref(self, type_ref) -> TypeInfo:
        if isinstance(type_ref, UnionType):
            types = [self._resolve_type_ref(t) for t in type_ref.types]
            return TypeInfo(name='union', type_args=types)
        if isinstance(type_ref, TupleType):
            types = [self._resolve_type_ref(t) for t in type_ref.types]
            return TypeInfo(name='tuple', type_args=types)
        if isinstance(type_ref, FuncType):
            param_types = [self._resolve_type_ref(p) for p in type_ref.params]
            return_type = self._resolve_type_ref(type_ref.return_type) if type_ref.return_type else self.type_system.types['none']
            return TypeInfo(name='function', is_function=True, param_types=param_types, return_type=return_type)
        base_type = self.type_system.get_type(type_ref.name)
        if type_ref.type_args:
            type_args = [self._resolve_type_ref(arg) for arg in type_ref.type_args]
            return TypeInfo(name=base_type.name, type_args=type_args)
        if type_ref.nullable:
            return TypeInfo(name=base_type.name, nullable=True)
        return base_type

    def visit(self, node: ASTNode) -> Optional[TypeInfo]:
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, None)
        if method:
            return method(node)
        return self.generic_visit(node)

    def generic_visit(self, node: ASTNode) -> Optional[TypeInfo]:
        for child in node.__dict__.values():
            if isinstance(child, ASTNode):
                self.visit(child)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, ASTNode):
                        self.visit(item)
        return None

    def visit_Program(self, node: Program) -> Optional[TypeInfo]:
        for stmt in node.statements:
            self.visit(stmt)
        return None

    def visit_IntLiteral(self, node: IntLiteral) -> TypeInfo:
        type_info = self.type_system.types['int']
        self._set_type(node, type_info)
        return type_info

    def visit_FloatLiteral(self, node: FloatLiteral) -> TypeInfo:
        type_info = self.type_system.types['float']
        self._set_type(node, type_info)
        return type_info

    def visit_StringLiteral(self, node: StringLiteral) -> TypeInfo:
        type_info = self.type_system.types['string']
        self._set_type(node, type_info)
        return type_info

    def visit_BoolLiteral(self, node: BoolLiteral) -> TypeInfo:
        type_info = self.type_system.types['bool']
        self._set_type(node, type_info)
        return type_info

    def visit_NoneLiteral(self, node: NoneLiteral) -> TypeInfo:
        type_info = self.type_system.types['none']
        self._set_type(node, type_info)
        return type_info

    def visit_CharLiteral(self, node: CharLiteral) -> TypeInfo:
        type_info = self.type_system.types['char']
        self._set_type(node, type_info)
        return type_info

    def visit_Identifier(self, node: Identifier) -> TypeInfo:
        type_info = self.symbol_table.lookup(node.name)
        if not type_info:
            self._error(f"Undefined variable '{node.name}'", node)
            type_info = self.type_system.types['any']
        self._set_type(node, type_info)
        return type_info

    def visit_SelfExpr(self, node: SelfExpr) -> TypeInfo:
        if not self.symbol_table.current_class:
            self._error("'self' used outside of class", node)
            return self.type_system.types['any']
        class_info = self.symbol_table.lookup_class(self.symbol_table.current_class)
        if class_info:
            type_info = TypeInfo(name=class_info.name)
        else:
            type_info = TypeInfo(name=self.symbol_table.current_class)
        self._set_type(node, type_info)
        return type_info

    def visit_SuperExpr(self, node: SuperExpr) -> TypeInfo:
        if not self.symbol_table.current_class:
            self._error("'super' used outside of class", node)
            return self.type_system.types['any']
        class_info = self.symbol_table.lookup_class(self.symbol_table.current_class)
        if class_info and class_info.bases:
            type_info = class_info.bases[0]
        else:
            type_info = self.type_system.types['object']
        self._set_type(node, type_info)
        return type_info

    def visit_BinaryExpr(self, node: BinaryExpr) -> TypeInfo:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        if not left_type or not right_type:
            return self._set_type(node, self.type_system.types['any'])

        if node.op in ('==', '!=', '<', '>', '<=', '>=', 'is', 'is not'):
            return self._set_type(node, self.type_system.types['bool'])

        if node.op in ('and', 'or'):
            return self._set_type(node, self.type_system.unify(left_type, right_type))

        if node.op in ('+', '-', '*', '/', '%', '**', '//'):
            if node.op == '+' and (self.type_system.is_string(left_type) or self.type_system.is_string(right_type)):
                return self._set_type(node, self.type_system.types['string'])
            if node.op in ('+', '-', '*', '/', '%', '**', '//'):
                result_type = self.type_system.unify(left_type, right_type)
                if not self.type_system.is_numeric(result_type):
                    self._error(f"Operator '{node.op}' not supported for types '{left_type}' and '{right_type}'", node)
                    return self._set_type(node, self.type_system.types['any'])
                return self._set_type(node, result_type)

        if node.op in ('<<', '>>', '&', '|', '^'):
            if not self.type_system.is_integer(left_type) or not self.type_system.is_integer(right_type):
                self._error(f"Bitwise operator '{node.op}' requires integer operands", node)
            return self._set_type(node, self.type_system.types['int'])

        self._error(f"Unknown operator '{node.op}'", node)
        return self._set_type(node, self.type_system.types['any'])

    def visit_UnaryExpr(self, node: UnaryExpr) -> TypeInfo:
        operand_type = self.visit(node.operand)
        if not operand_type:
            return self.type_system.types['any']

        if node.op == '-':
            if self.type_system.is_numeric(operand_type):
                return self._set_type(node, operand_type)
            self._error(f"Unary '-' not supported for type '{operand_type}'", node)
            return self.type_system.types['any']

        if node.op == '+':
            if self.type_system.is_numeric(operand_type):
                return self._set_type(node, operand_type)
            self._error(f"Unary '+' not supported for type '{operand_type}'", node)
            return self.type_system.types['any']

        if node.op == 'not':
            return self._set_type(node, self.type_system.types['bool'])

        if node.op == '~':
            if self.type_system.is_integer(operand_type):
                return self._set_type(node, self.type_system.types['int'])
            self._error(f"Unary '~' not supported for type '{operand_type}'", node)
            return self.type_system.types['any']

        self._error(f"Unknown unary operator '{node.op}'", node)
        return self.type_system.types['any']

    def visit_CallExpr(self, node: CallExpr) -> TypeInfo:
        if isinstance(node.callee, Identifier):
            func_sig = self.symbol_table.lookup_function(node.callee.name)
            if func_sig:
                self._check_builtin_call(func_sig, node.args, node.kwargs, node)
                result = func_sig.return_type
                self._set_type(node, result)
                return result
            class_info = self.symbol_table.lookup_class(node.callee.name)
            if class_info:
                result = TypeInfo(name=class_info.name)
                self._set_type(node.callee, result)
                self._set_type(node, result)
                for arg in node.args:
                    self.visit(arg)
                return result
        callee_type = self.visit(node.callee)
        if not callee_type:
            return self._set_type(node, self.type_system.types['any'])

        if callee_type.is_function:
            self._check_function_call(callee_type, node.args, node.kwargs, node)
            result = callee_type.return_type or self.type_system.types['any']
            self._set_type(node, result)
            return result

        if callee_type.name == 'type' and len(node.args) == 1:
            self.visit(node.args[0])
            return self._set_type(node, self.type_system.types['type'])

        self._error(f"'{callee_type}' is not callable", node)
        return self._set_type(node, self.type_system.types['any'])

    def _check_function_call(self, func_type: TypeInfo, args: List[ASTNode], kwargs: Dict[str, ASTNode], node: ASTNode) -> None:
        expected_count = len(func_type.param_types)
        actual_count = len(args) + len(kwargs)

        if actual_count < expected_count:
            self._error(f"Expected {expected_count} arguments, got {actual_count}", node)
        elif actual_count > expected_count:
            self._error(f"Expected {expected_count} arguments, got {actual_count}", node)

        for i, arg in enumerate(args):
            arg_type = self.visit(arg)
            if i < len(func_type.param_types):
                expected = func_type.param_types[i]
                if not self.type_system.can_unify(arg_type, expected):
                    self._error(f"Argument {i+1}: expected '{expected}', got '{arg_type}'", arg)

    def _check_builtin_call(self, func_sig: FunctionSignature, args: List[ASTNode], kwargs: Dict[str, ASTNode], node: ASTNode) -> None:
        if func_sig.name == 'len' and len(args) == 1:
            arg_type = self.visit(args[0])
            if arg_type and arg_type.name not in ('list', 'dict', 'set', 'tuple', 'string', 'any'):
                self._error(f"len() not supported for type '{arg_type}'", args[0])
            return

        if func_sig.name == 'range':
            for arg in args:
                arg_type = self.visit(arg)
                if arg_type and not self.type_system.is_integer(arg_type):
                    self._error(f"range() expects integer arguments, got '{arg_type}'", arg)
            return

        if func_sig.name in ('int', 'float', 'string', 'bool'):
            if len(args) == 1:
                self.visit(args[0])
            return

        expected_count = len(func_sig.param_types)
        actual_count = len(args) + len(kwargs)
        if actual_count < expected_count:
            self._error(f"{func_sig.name}() expects {expected_count} arguments, got {actual_count}", node)

    def visit_MethodCallExpr(self, node: MethodCallExpr) -> TypeInfo:
        obj_type = self.visit(node.object)
        if not obj_type:
            return self.type_system.types['any']

        if obj_type.name == 'string':
            return self._check_string_method(node.method, node.args, node)
        if obj_type.name == 'list':
            return self._check_list_method(obj_type, node.method, node.args, node)
        if obj_type.name == 'dict':
            return self._check_dict_method(obj_type, node.method, node.args, node)
        if obj_type.name == 'set':
            return self._check_set_method(obj_type, node.method, node.args, node)

        class_info = self.symbol_table.lookup_class(obj_type.name)
        if class_info and node.method in class_info.methods:
            method_sig = class_info.methods[node.method]
            for i, arg in enumerate(node.args):
                arg_type = self.visit(arg)
                if i < len(method_sig.param_types):
                    expected = method_sig.param_types[i]
                    if not self.type_system.can_unify(arg_type, expected):
                        self._error(f"Argument {i+1}: expected '{expected}', got '{arg_type}'", arg)
            return method_sig.return_type

        self._error(f"Type '{obj_type}' has no method '{node.method}'", node)
        return self.type_system.types['any']

    def _check_string_method(self, method: str, args: List[ASTNode], node: ASTNode) -> TypeInfo:
        for arg in args:
            self.visit(arg)
        string_methods = {
            'upper': self.type_system.types['string'],
            'lower': self.type_system.types['string'],
            'strip': self.type_system.types['string'],
            'split': TypeInfo(name='list', type_args=[self.type_system.types['string']]),
            'join': self.type_system.types['string'],
            'replace': self.type_system.types['string'],
            'startswith': self.type_system.types['bool'],
            'endswith': self.type_system.types['bool'],
            'find': self.type_system.types['int'],
            'count': self.type_system.types['int'],
            'isdigit': self.type_system.types['bool'],
            'isalpha': self.type_system.types['bool'],
            'isalnum': self.type_system.types['bool'],
            'format': self.type_system.types['string'],
        }
        return string_methods.get(method, self.type_system.types['any'])

    def _check_list_method(self, list_type: TypeInfo, method: str, args: List[ASTNode], node: ASTNode) -> TypeInfo:
        elem_type = self.type_system.get_element_type(list_type) or self.type_system.types['any']
        for arg in args:
            self.visit(arg)
        list_methods = {
            'append': self.type_system.types['none'],
            'extend': self.type_system.types['none'],
            'pop': elem_type,
            'insert': self.type_system.types['none'],
            'remove': self.type_system.types['none'],
            'index': self.type_system.types['int'],
            'count': self.type_system.types['int'],
            'sort': self.type_system.types['none'],
            'reverse': self.type_system.types['none'],
            'copy': list_type,
            'clear': self.type_system.types['none'],
        }
        return list_methods.get(method, self.type_system.types['any'])

    def _check_dict_method(self, dict_type: TypeInfo, method: str, args: List[ASTNode], node: ASTNode) -> TypeInfo:
        key_type, val_type = self.type_system.get_dict_types(dict_type)
        key_type = key_type or self.type_system.types['any']
        val_type = val_type or self.type_system.types['any']
        for arg in args:
            self.visit(arg)
        dict_methods = {
            'get': val_type,
            'keys': TypeInfo(name='list', type_args=[key_type]),
            'values': TypeInfo(name='list', type_args=[val_type]),
            'items': TypeInfo(name='list', type_args=[
                TypeInfo(name='tuple', type_args=[key_type, val_type])
            ]),
            'update': self.type_system.types['none'],
            'pop': val_type,
            'clear': self.type_system.types['none'],
            'copy': dict_type,
            'setdefault': val_type,
        }
        return dict_methods.get(method, self.type_system.types['any'])

    def _check_set_method(self, set_type: TypeInfo, method: str, args: List[ASTNode], node: ASTNode) -> TypeInfo:
        elem_type = self.type_system.get_element_type(set_type) or self.type_system.types['any']
        for arg in args:
            self.visit(arg)
        set_methods = {
            'add': self.type_system.types['none'],
            'remove': self.type_system.types['none'],
            'discard': self.type_system.types['none'],
            'pop': elem_type,
            'clear': self.type_system.types['none'],
            'copy': set_type,
            'union': set_type,
            'intersection': set_type,
            'difference': set_type,
            'symmetric_difference': set_type,
            'issubset': self.type_system.types['bool'],
            'issuperset': self.type_system.types['bool'],
        }
        return set_methods.get(method, self.type_system.types['any'])

    def visit_PropertyAccessExpr(self, node: PropertyAccessExpr) -> TypeInfo:
        obj_type = self.visit(node.object)
        if not obj_type:
            return self.type_system.types['any']

        class_info = self.symbol_table.lookup_class(obj_type.name)
        if class_info and node.property in class_info.fields:
            return class_info.fields[node.property]

        if obj_type.name == 'list' and node.property == 'length':
            return self.type_system.types['int']
        if obj_type.name == 'dict' and node.property == 'length':
            return self.type_system.types['int']

        self._error(f"Type '{obj_type}' has no property '{node.property}'", node)
        return self.type_system.types['any']

    def visit_IndexExpr(self, node: IndexExpr) -> TypeInfo:
        obj_type = self.visit(node.object)
        index_type = self.visit(node.index)
        if not obj_type:
            return self.type_system.types['any']

        if obj_type.name == 'list':
            if index_type and not self.type_system.is_integer(index_type):
                self._error(f"List index must be integer, got '{index_type}'", node)
            return self.type_system.get_element_type(obj_type) or self.type_system.types['any']

        if obj_type.name == 'dict':
            return self.type_system.get_dict_types(obj_type)[1] or self.type_system.types['any']

        if obj_type.name == 'tuple':
            if index_type and self.type_system.is_integer(index_type) and isinstance(node.index, IntLiteral):
                idx = node.index.value
                if 0 <= idx < len(obj_type.type_args):
                    return obj_type.type_args[idx]
            return self.type_system.get_element_type(obj_type) or self.type_system.types['any']

        if obj_type.name == 'string':
            if index_type and not self.type_system.is_integer(index_type):
                self._error(f"String index must be integer, got '{index_type}'", node)
            return self.type_system.types['string']

        self._error(f"Type '{obj_type}' is not subscriptable", node)
        return self.type_system.types['any']

    def visit_SliceExpr(self, node: SliceExpr) -> TypeInfo:
        obj_type = self.visit(node.object)
        if node.start:
            start_type = self.visit(node.start)
            if start_type and not self.type_system.is_integer(start_type):
                self._error(f"Slice start must be integer, got '{start_type}'", node)
        if node.end:
            end_type = self.visit(node.end)
            if end_type and not self.type_system.is_integer(end_type):
                self._error(f"Slice end must be integer, got '{end_type}'", node)
        if node.step:
            step_type = self.visit(node.step)
            if step_type and not self.type_system.is_integer(step_type):
                self._error(f"Slice step must be integer, got '{step_type}'", node)
        if obj_type:
            return TypeInfo(name=obj_type.name, type_args=obj_type.type_args)
        return self.type_system.types['any']

    def visit_LambdaExpr(self, node: LambdaExpr) -> TypeInfo:
        self.symbol_table = self.symbol_table.child_scope()
        param_types = []
        for param in node.params:
            if param.type_ref:
                param_type = self._resolve_type_ref(param.type_ref)
            else:
                param_type = self.type_system.types['any']
            param_types.append(param_type)
            self.symbol_table.define(param.name, param_type)
        body_type = self.visit(node.body)
        self.symbol_table = self.symbol_table.parent
        if not body_type:
            body_type = self.type_system.types['none']
        type_info = TypeInfo(
            name='function',
            is_function=True,
            param_types=param_types,
            return_type=body_type
        )
        self._set_type(node, type_info)
        return type_info

    def visit_ListExpr(self, node: ListExpr) -> TypeInfo:
        elem_types = []
        for elem in node.elements:
            elem_type = self.visit(elem)
            if elem_type:
                elem_types.append(elem_type)
        if elem_types:
            unified = elem_types[0]
            for t in elem_types[1:]:
                unified = self.type_system.unify(unified, t)
            type_info = TypeInfo(name='list', type_args=[unified])
        else:
            type_info = TypeInfo(name='list', type_args=[self.type_system.types['any']])
        self._set_type(node, type_info)
        return type_info

    def visit_DictExpr(self, node: DictExpr) -> TypeInfo:
        key_types = []
        val_types = []
        for key, val in zip(node.keys, node.values):
            key_type = self.visit(key)
            val_type = self.visit(val)
            if key_type:
                key_types.append(key_type)
            if val_type:
                val_types.append(val_type)
        if key_types:
            key_unified = key_types[0]
            for t in key_types[1:]:
                key_unified = self.type_system.unify(key_unified, t)
        else:
            key_unified = self.type_system.types['any']
        if val_types:
            val_unified = val_types[0]
            for t in val_types[1:]:
                val_unified = self.type_system.unify(val_unified, t)
        else:
            val_unified = self.type_system.types['any']
        type_info = TypeInfo(name='dict', type_args=[key_unified, val_unified])
        self._set_type(node, type_info)
        return type_info

    def visit_SetExpr(self, node: SetExpr) -> TypeInfo:
        elem_types = []
        for elem in node.elements:
            elem_type = self.visit(elem)
            if elem_type:
                elem_types.append(elem_type)
        if elem_types:
            unified = elem_types[0]
            for t in elem_types[1:]:
                unified = self.type_system.unify(unified, t)
            type_info = TypeInfo(name='set', type_args=[unified])
        else:
            type_info = TypeInfo(name='set', type_args=[self.type_system.types['any']])
        self._set_type(node, type_info)
        return type_info

    def visit_TupleExpr(self, node: TupleExpr) -> TypeInfo:
        elem_types = []
        for elem in node.elements:
            elem_type = self.visit(elem)
            if elem_type:
                elem_types.append(elem_type)
            else:
                elem_types.append(self.type_system.types['any'])
        type_info = TypeInfo(name='tuple', type_args=elem_types)
        self._set_type(node, type_info)
        return type_info

    def visit_IfExpr(self, node: IfExpr) -> TypeInfo:
        cond_type = self.visit(node.condition)
        if cond_type and not self.type_system.is_bool(cond_type) and cond_type.name != 'any':
            self._error(f"Condition must be boolean, got '{cond_type}'", node)
        then_type = self.visit(node.then_body)
        elif_types = []
        for cond, body in node.elif_branches:
            self.visit(cond)
            elif_type = self.visit(body)
            if elif_type:
                elif_types.append(elif_type)
        else_type = self.visit(node.else_body) if node.else_body else self.type_system.types['none']
        if then_type and else_type:
            result = self.type_system.unify(then_type, else_type)
        elif then_type:
            result = then_type
        elif else_type:
            result = else_type
        else:
            result = self.type_system.types['any']
        for et in elif_types:
            result = self.type_system.unify(result, et)
        self._set_type(node, result)
        return result

    def visit_MatchExpr(self, node: MatchExpr) -> TypeInfo:
        value_type = self.visit(node.value)
        result_type = None
        for case in node.cases:
            self.visit(case.pattern)
            if case.guard:
                self.visit(case.guard)
            case_type = self.visit(case.body)
            if case_type:
                if result_type is None:
                    result_type = case_type
                else:
                    result_type = self.type_system.unify(result_type, case_type)
        if result_type is None:
            result_type = self.type_system.types['none']
        self._set_type(node, result_type)
        return result_type

    def visit_MatchCase(self, node: MatchCase) -> Optional[TypeInfo]:
        self.visit(node.pattern)
        if node.guard:
            self.visit(node.guard)
        return self.visit(node.body)

    def visit_IsExpr(self, node: IsExpr) -> TypeInfo:
        self.visit(node.value)
        if node.type_ref:
            self.visit(node.type_ref)
        type_info = self.type_system.types['bool']
        self._set_type(node, type_info)
        return type_info

    def visit_AsExpr(self, node: AsExpr) -> TypeInfo:
        self.visit(node.value)
        type_info = self._resolve_type_ref(node.type_ref)
        self._set_type(node, type_info)
        return type_info

    def visit_PipeExpr(self, node: PipeExpr) -> TypeInfo:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        if right_type and right_type.is_function and right_type.param_types:
            if left_type and not self.type_system.can_unify(left_type, right_type.param_types[0]):
                self._error(f"Pipe: expected '{right_type.param_types[0]}', got '{left_type}'", node)
        self._set_type(node, right_type or self.type_system.types['any'])
        return right_type or self.type_system.types['any']

    def visit_NullishCoalesceExpr(self, node: NullishCoalesceExpr) -> TypeInfo:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        if left_type and right_type:
            if left_type.nullable or left_type.name == 'none':
                result = right_type
            elif right_type.nullable or right_type.name == 'none':
                result = left_type
            else:
                result = self.type_system.unify(left_type, right_type)
        elif left_type:
            result = left_type
        elif right_type:
            result = right_type
        else:
            result = self.type_system.types['any']
        self._set_type(node, result)
        return result

    def visit_SpreadExpr(self, node: SpreadExpr) -> TypeInfo:
        type_info = self.visit(node.value)
        self._set_type(node, type_info or self.type_system.types['any'])
        return type_info or self.type_system.types['any']

    def visit_AwaitExpr(self, node: AwaitExpr) -> TypeInfo:
        type_info = self.visit(node.value)
        self._set_type(node, type_info or self.type_system.types['any'])
        return type_info or self.type_system.types['any']

    def visit_YieldExpr(self, node: YieldExpr) -> TypeInfo:
        if node.value:
            type_info = self.visit(node.value)
        else:
            type_info = self.type_system.types['none']
        self._set_type(node, type_info)
        return type_info

    def visit_TypeOfExpr(self, node: TypeOfExpr) -> TypeInfo:
        self.visit(node.value)
        type_info = self.type_system.types['string']
        self._set_type(node, type_info)
        return type_info

    def visit_ExprStmt(self, node: ExprStmt) -> Optional[TypeInfo]:
        return self.visit(node.expr)

    def visit_AssignStmt(self, node: AssignStmt) -> Optional[TypeInfo]:
        if isinstance(node.target, Identifier):
            if not self.symbol_table.is_mutable(node.target.name):
                self._error(f"Cannot assign to constant '{node.target.name}'", node)
            value_type = self.visit(node.value)
            existing_type = self.symbol_table.lookup(node.target.name)
            if value_type:
                if existing_type:
                    if not self.type_system.can_unify(existing_type, value_type):
                        self._error(f"Cannot assign '{value_type}' to variable of type '{existing_type}'", node)
                    value_type = self.type_system.unify(existing_type, value_type)
                self.symbol_table.define(node.target.name, value_type)
                self._set_type(node.target, value_type)
            return value_type
        elif isinstance(node.target, PropertyAccessExpr):
            value_type = self.visit(node.value)
            if isinstance(node.target.object, SelfExpr) and self.symbol_table.current_class:
                self.visit(node.target.object)
                if value_type:
                    class_info = self.symbol_table.lookup_class(self.symbol_table.current_class)
                    if class_info:
                        existing = class_info.fields.get(node.target.property)
                        if existing and not self.type_system.can_unify(existing, value_type):
                            self._error(f"Cannot assign '{value_type}' to field '{node.target.property}' of type '{existing}'", node)
                        elif not existing:
                            class_info.fields[node.target.property] = value_type
                return value_type
            else:
                obj_type = self.visit(node.target.object)
                if obj_type and value_type:
                    class_info = self.symbol_table.lookup_class(obj_type.name)
                    if class_info:
                        field_type = class_info.fields.get(node.target.property)
                        if field_type and not self.type_system.can_unify(field_type, value_type):
                            self._error(f"Cannot assign '{value_type}' to field '{node.target.property}' of type '{field_type}'", node)
                return value_type
        elif isinstance(node.target, IndexExpr):
            self.visit(node.target.object)
            self.visit(node.target.index)
            value_type = self.visit(node.value)
            return value_type
        else:
            self.visit(node.target)
            value_type = self.visit(node.value)
            return value_type

    def visit_AugAssignStmt(self, node: AugAssignStmt) -> Optional[TypeInfo]:
        target_type = self.visit(node.target)
        value_type = self.visit(node.value)
        if target_type and value_type:
            if node.op in ('+=', '-=', '*=', '/=', '%='):
                if not (self.type_system.is_numeric(target_type) and self.type_system.is_numeric(value_type)):
                    self._error(f"Operator '{node.op}' not supported for types '{target_type}' and '{value_type}'", node)
            elif node.op in ('&=', '|=', '^=', '<<=', '>>='):
                if not (self.type_system.is_integer(target_type) and self.type_system.is_integer(value_type)):
                    self._error(f"Bitwise operator '{node.op}' requires integer operands", node)
            elif node.op == '**=':
                if not (self.type_system.is_numeric(target_type) and self.type_system.is_numeric(value_type)):
                    self._error(f"Operator '{node.op}' not supported for types '{target_type}' and '{value_type}'", node)
        return target_type

    def visit_LetStmt(self, node: LetStmt) -> Optional[TypeInfo]:
        if node.type_ref:
            type_info = self._resolve_type_ref(node.type_ref)
        else:
            type_info = None
        if node.value:
            value_type = self.visit(node.value)
            if type_info:
                if value_type and not self.type_system.can_unify(type_info, value_type):
                    self._error(f"Cannot assign '{value_type}' to variable of type '{type_info}'", node)
                type_info = self.type_system.unify(type_info, value_type)
            else:
                type_info = value_type or self.type_system.types['any']
        elif not type_info:
            type_info = self.type_system.types['any']
        self.symbol_table.define(node.name, type_info, is_const=not node.mutable)
        return type_info

    def visit_ReturnStmt(self, node: ReturnStmt) -> Optional[TypeInfo]:
        if node.value:
            value_type = self.visit(node.value)
            if self._current_return_type and value_type:
                if not self.type_system.can_unify(self._current_return_type, value_type):
                    self._error(f"Cannot return '{value_type}' from function with return type '{self._current_return_type}'", node)
            return value_type
        else:
            if self._current_return_type and self._current_return_type.name != 'none':
                self._error("Function must return a value", node)
        return self.type_system.types['none']

    def visit_BreakStmt(self, node: BreakStmt) -> Optional[TypeInfo]:
        if not self.symbol_table.in_loop:
            self._error("'break' outside of loop", node)
        if node.value:
            return self.visit(node.value)
        return self.type_system.types['none']

    def visit_ContinueStmt(self, node: ContinueStmt) -> Optional[TypeInfo]:
        if not self.symbol_table.in_loop:
            self._error("'continue' outside of loop", node)
        return self.type_system.types['none']

    def visit_IfStmt(self, node: IfStmt) -> Optional[TypeInfo]:
        cond_type = self.visit(node.condition)
        if cond_type and not self.type_system.is_bool(cond_type) and cond_type.name != 'any':
            self._error(f"Condition must be boolean, got '{cond_type}'", node)
        self.visit(node.then_body)
        for cond, body in node.elif_branches:
            self.visit(cond)
            self.visit(body)
        if node.else_body:
            self.visit(node.else_body)
        return None

    def visit_WhileStmt(self, node: WhileStmt) -> Optional[TypeInfo]:
        cond_type = self.visit(node.condition)
        if cond_type and not self.type_system.is_bool(cond_type) and cond_type.name != 'any':
            self._error(f"Condition must be boolean, got '{cond_type}'", node)
        self.symbol_table.in_loop = True
        self.visit(node.body)
        self.symbol_table.in_loop = False
        return None

    def visit_ForStmt(self, node: ForStmt) -> Optional[TypeInfo]:
        iter_type = self.visit(node.iter_expr)
        elem_type = self.type_system.get_element_type(iter_type) if iter_type else self.type_system.types['any']
        self.symbol_table = self.symbol_table.child_scope()
        self.symbol_table.define(node.var, elem_type or self.type_system.types['any'])
        self.symbol_table.in_loop = True
        self.visit(node.body)
        self.symbol_table.in_loop = False
        self.symbol_table = self.symbol_table.parent
        return None

    def visit_LoopStmt(self, node: LoopStmt) -> Optional[TypeInfo]:
        self.symbol_table.in_loop = True
        self.visit(node.body)
        self.symbol_table.in_loop = False
        return None

    def visit_RaiseStmt(self, node: RaiseStmt) -> Optional[TypeInfo]:
        if node.value:
            self.visit(node.value)
        return self.type_system.types['none']

    def visit_TryStmt(self, node: TryStmt) -> Optional[TypeInfo]:
        self.visit(node.body)
        for clause in node.catch_clauses:
            self.visit(clause)
        if node.finally_body:
            self.visit(node.finally_body)
        return None

    def visit_CatchClause(self, node: CatchClause) -> Optional[TypeInfo]:
        self.symbol_table = self.symbol_table.child_scope()
        if node.type_ref:
            type_info = self._resolve_type_ref(node.type_ref)
        else:
            type_info = self.type_system.types['any']
        if node.var_name:
            self.symbol_table.define(node.var_name, type_info)
        self.visit(node.body)
        self.symbol_table = self.symbol_table.parent
        return None

    def visit_AssertStmt(self, node: AssertStmt) -> Optional[TypeInfo]:
        cond_type = self.visit(node.condition)
        if cond_type and not self.type_system.is_bool(cond_type) and cond_type.name != 'any':
            self._error(f"Assert condition must be boolean, got '{cond_type}'", node)
        if node.message:
            self.visit(node.message)
        return None

    def visit_Block(self, node: Block) -> Optional[TypeInfo]:
        self.symbol_table = self.symbol_table.child_scope()
        result_type = None
        for stmt in node.statements:
            result_type = self.visit(stmt)
        self.symbol_table = self.symbol_table.parent
        return result_type

    def visit_Param(self, node: Param) -> Optional[TypeInfo]:
        if node.type_ref:
            type_info = self._resolve_type_ref(node.type_ref)
        else:
            type_info = self.type_system.types['any']
        if node.default:
            default_type = self.visit(node.default)
            if default_type and not self.type_system.can_unify(type_info, default_type):
                self._error(f"Default value type '{default_type}' doesn't match parameter type '{type_info}'", node)
        self.symbol_table.define(node.name, type_info)
        return type_info

    def visit_FnDecl(self, node: FnDecl) -> Optional[TypeInfo]:
        param_types = []
        param_names = []
        param_defaults = []
        old_class = self.symbol_table.current_class
        if node.return_type:
            return_type = self._resolve_type_ref(node.return_type)
        else:
            return_type = self.type_system.types['none']
        sig = FunctionSignature(
            name=node.name,
            param_types=[],
            param_names=[],
            param_defaults=[],
            return_type=return_type,
            is_async=node.is_async,
            is_method=old_class is not None
        )
        self.symbol_table.define_function(node.name, sig)
        self.symbol_table = self.symbol_table.child_scope()
        self.symbol_table.current_function = node.name
        self.symbol_table.current_class = old_class
        for param in node.params:
            if param.type_ref:
                param_type = self._resolve_type_ref(param.type_ref)
            else:
                param_type = self.type_system.types['any']
            param_types.append(param_type)
            param_names.append(param.name)
            param_defaults.append(param.default)
            self.symbol_table.define(param.name, param_type)
        sig.param_types = param_types
        sig.param_names = param_names
        sig.param_defaults = param_defaults
        self._current_return_type = return_type
        old_async = self._async_context
        self._async_context = node.is_async
        if node.body:
            if isinstance(node.body, Block):
                for stmt in node.body.statements:
                    self.visit(stmt)
            else:
                self.visit(node.body)
        self._async_context = old_async
        self._current_return_type = None
        self.symbol_table = self.symbol_table.parent
        self.symbol_table.current_class = old_class
        func_type = TypeInfo(
            name='function',
            is_function=True,
            param_types=param_types,
            return_type=return_type
        )
        self._set_type(node, func_type)
        return func_type

    def visit_ClassDecl(self, node: ClassDecl) -> Optional[TypeInfo]:
        old_class = self.symbol_table.current_class
        self.symbol_table = self.symbol_table.child_scope()
        self.symbol_table.current_class = node.name
        bases = []
        for base in node.bases:
            bases.append(self._resolve_type_ref(base))
        class_info = ClassInfo(
            name=node.name,
            bases=bases,
            fields={},
            methods={},
            is_abstract=node.is_abstract,
            type_params=node.type_params
        )
        for base in bases:
            base_class = self.symbol_table.lookup_class(base.name)
            if base_class:
                class_info.fields.update(base_class.fields)
                class_info.methods.update(base_class.methods)
        self.symbol_table.define('self', TypeInfo(name=node.name))
        self.symbol_table.define_class(node.name, class_info)
        self.visit(node.body)
        self.symbol_table = self.symbol_table.parent
        self.symbol_table.define_class(node.name, class_info)
        self.symbol_table.current_class = old_class
        type_info = TypeInfo(name=node.name)
        self._set_type(node, type_info)
        return type_info

    def visit_RecordDecl(self, node: RecordDecl) -> Optional[TypeInfo]:
        old_class = self.symbol_table.current_class
        self.symbol_table = self.symbol_table.child_scope()
        self.symbol_table.current_class = node.name
        class_info = ClassInfo(
            name=node.name,
            bases=[],
            fields={},
            methods={},
            type_params=node.type_params
        )
        for param in node.fields:
            if param.type_ref:
                field_type = self._resolve_type_ref(param.type_ref)
            else:
                field_type = self.type_system.types['any']
            class_info.fields[param.name] = field_type
            self.symbol_table.define(param.name, field_type)
        self.symbol_table.define_class(node.name, class_info)
        for method in node.methods:
            self.visit(method)
            func_sig = self.symbol_table.lookup_function(method.name)
            if func_sig:
                class_info.methods[method.name] = func_sig
        self.symbol_table = self.symbol_table.parent
        self.symbol_table.define_class(node.name, class_info)
        self.symbol_table.current_class = old_class
        type_info = TypeInfo(name=node.name)
        self._set_type(node, type_info)
        return type_info

    def visit_EnumDecl(self, node: EnumDecl) -> Optional[TypeInfo]:
        self.symbol_table = self.symbol_table.child_scope()
        enum_info = ClassInfo(
            name=node.name,
            bases=[],
            fields={},
            methods={},
            type_params=[]
        )
        self.symbol_table.define_class(node.name, enum_info)
        for variant in node.variants:
            self.visit(variant)
        self.symbol_table = self.symbol_table.parent
        self.symbol_table.define_class(node.name, enum_info)
        type_info = TypeInfo(name=node.name)
        self._set_type(node, type_info)
        return type_info

    def visit_EnumVariant(self, node: EnumVariant) -> Optional[TypeInfo]:
        variant_type = TypeInfo(name=node.name)
        self._set_type(node, variant_type)
        for field in node.fields:
            self._resolve_type_ref(field)
        if node.value:
            self.visit(node.value)
        return variant_type

    def visit_InterfaceDecl(self, node: InterfaceDecl) -> Optional[TypeInfo]:
        self.symbol_table = self.symbol_table.child_scope()
        interface_info = ClassInfo(
            name=node.name,
            bases=[],
            fields={},
            methods={},
            type_params=[]
        )
        self.symbol_table.define_class(node.name, interface_info)
        for method in node.methods:
            self.visit(method)
            func_sig = self.symbol_table.lookup_function(method.name)
            if func_sig:
                interface_info.methods[method.name] = func_sig
        self.symbol_table = self.symbol_table.parent
        self.symbol_table.define_class(node.name, interface_info)
        type_info = TypeInfo(name=node.name)
        self._set_type(node, type_info)
        return type_info

    def visit_TypeAlias(self, node: TypeAlias) -> Optional[TypeInfo]:
        type_info = self._resolve_type_ref(node.type_ref)
        self.type_system.register_type(node.name, type_info)
        self._set_type(node, type_info)
        return type_info

    def visit_ModuleDecl(self, node: ModuleDecl) -> Optional[TypeInfo]:
        self.symbol_table = self.symbol_table.child_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.symbol_table = self.symbol_table.parent
        return None

    def visit_ImportDecl(self, node: ImportDecl) -> Optional[TypeInfo]:
        type_info = self.type_system.types['any']
        if node.alias:
            self.symbol_table.define(node.alias, type_info)
        else:
            for name in node.names:
                self.symbol_table.define(name, type_info)
        return None

    def visit_FromImportDecl(self, node: FromImportDecl) -> Optional[TypeInfo]:
        for name, alias in node.names:
            type_info = self.type_system.types['any']
            self.symbol_table.define(alias or name, type_info)
        return None

    def visit_TestDecl(self, node: TestDecl) -> Optional[TypeInfo]:
        self.symbol_table = self.symbol_table.child_scope()
        self.visit(node.body)
        self.symbol_table = self.symbol_table.parent
        return None

    def visit_TypeRef(self, node: TypeRef) -> TypeInfo:
        type_info = self._resolve_type_ref(node)
        self._set_type(node, type_info)
        return type_info

    def visit_FuncType(self, node: FuncType) -> TypeInfo:
        param_types = [self._resolve_type_ref(p) for p in node.params]
        return_type = self._resolve_type_ref(node.return_type) if node.return_type else self.type_system.types['none']
        type_info = TypeInfo(
            name='function',
            is_function=True,
            param_types=param_types,
            return_type=return_type
        )
        self._set_type(node, type_info)
        return type_info

    def visit_UnionType(self, node: UnionType) -> TypeInfo:
        types = [self._resolve_type_ref(t) for t in node.types]
        type_info = TypeInfo(name='union', type_args=types)
        self._set_type(node, type_info)
        return type_info

    def visit_TupleType(self, node: TupleType) -> TypeInfo:
        types = [self._resolve_type_ref(t) for t in node.types]
        type_info = TypeInfo(name='tuple', type_args=types)
        self._set_type(node, type_info)
        return type_info

    def visit_GeneratorExpr(self, node: GeneratorExpr) -> TypeInfo:
        elem_type = self.visit(node.element)
        self.visit(node.iter_expr)
        if node.condition:
            self.visit(node.condition)
        type_info = TypeInfo(name='generator', type_args=[elem_type or self.type_system.types['any']])
        self._set_type(node, type_info)
        return type_info


def type_check(program: Program) -> Tuple[Dict[int, TypeInfo], List[TypeCheckError]]:
    """Type check a program and return the type map (id -> TypeInfo) and any errors."""
    checker = TypeChecker()
    type_map = checker.check(program)
    return type_map, checker.errors
