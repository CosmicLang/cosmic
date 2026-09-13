# Cosmic Language — Development Standards

## Architecture

```
Source (.cos)
  → Lexer   (tokens.py, lexer.py)     Hand-written tokenizer
  → Parser  (parser.py)                Recursive descent
  → AST     (nodes.py)                 67 node types, dataclass-based
  → Checker (checker.py)               Type checking, symbol table
  → Backend
    ├→ Transpiler (transpiler.py)      AST → Python
    └→ Bytecode   (compiler.py)        AST → Bytecode → VM
```

## Entry Points

| Command | Entry |
|---------|-------|
| `cosmic <cmd>` | `cosmic.cli:main` |
| `python -m cosmic` | `cosmic/__main__.py` |
| `import cosmic` | `cosmic/__init__.py` → `compile_source()` |

## Module Layout

```
cosmic/
  __init__.py          Public API: compile_source, Compiler, CosmicVM
  __main__.py          python -m cosmic
  diagnostics.py       Structured diagnostic system (Diagnostic, DiagnosticCollector)
  cli/                 CLI package — dedicated command modules
    __init__.py        Exports main()
    main.py            Pure dispatcher (zero business logic)
    cmd_run.py         Run command
    cmd_check.py       Check command (injectable streams for testability)
    cmd_compile.py     Compile command
    cmd_transpile.py   Transpile command
    cmd_bytecode.py    Bytecode command
    cmd_tokens.py      Tokens command
    cmd_ast.py         AST command
    cmd_repl.py        REPL command
    cmd_version.py     Version command
    support.py         Shared utilities (file validation, source reading)
  REPL.py              Interactive REPL
  ast/nodes.py         All AST node dataclasses
  lexer/tokens.py      TokenType enum, Token dataclass
  lexer/lexer.py       Tokenizer
  parser/parser.py     Recursive descent parser
  types/checker.py     Type checker
  backends/python/transpiler.py    Python codegen
  backends/bytecode/compiler.py    Bytecode compiler + VM
  compiler/pipeline.py Compiler orchestration
  stdlib/              Standard library modules
tests/                 pytest test suite
examples/              Example .cos programs
```

## Code Rules

### Naming
- **Files**: `snake_case.py` (no PascalCase filenames)
- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`
- **AST nodes**: Suffix `Expr`, `Stmt`, `Decl` (e.g., `BinaryExpr`, `FnDecl`)
- **Visitor methods**: `visit_<NodeType>` / `_compile_<NodeType>`
- **CLI commands**: `cmd_<name>.py` with `run(args)` entry point

### Imports
- **NEVER** use `from X import *` — always explicit imports
- Group: stdlib → third-party → local (each separated by blank line)
- Use `from __future__ import annotations` in every file
- Prefer `X | None` over `Optional[X]` (with `from __future__ import annotations`)
- Prefer builtin generics `dict`, `list`, `set`, `tuple` over `typing.Dict`, etc.

### Type Annotations
- All public functions must have full type annotations
- Use `Any` only when type is truly dynamic
- Return types are mandatory

### Error Handling
- Use structured `Diagnostic` system for compiler errors/warnings
- Custom runtime exceptions inherit from `CosmicError` in `stdlib/errors.py`
- Error classes that shadow builtins use trailing underscore: `TypeError_`, `ValueError_`
- Error classes that don't shadow builtins have no underscore: `DivisionByZeroError`
- Never silently swallow exceptions — log or re-raise

### Diagnostic System (Kof4j pattern)
- Every compiler error carries: severity, file, line, column, length, message, code
- Error codes: `LEX###` (lexer), `PAR###` (parser), `TYP###` (type checker), `CMP###` (compiler)
- Use `DiagnosticCollector` to accumulate diagnostics through pipeline phases
- `Diagnostic.format()` produces `file:line:col: severity: message [CODE]`

### CLI Architecture (Kof4j pattern)
- `main.py` is a pure dispatcher — zero business logic beyond routing
- Each command is a dedicated `cmd_<name>.py` module with `run(args) -> int`
- `support.py` holds shared utilities (file validation, source reading)
- `CmdCheck` accepts injectable `out`/`err` streams for testability

### Testing
- Framework: `pytest`
- Test file naming: `test_<module>.py`
- Test class naming: `Test<Feature>`
- Test method naming: `test_<behavior>`
- **Every test must assert a concrete value** — no `assert result is None` for output checks
- E2E tests: compile → execute → assert stdout output (Kof4j pattern)
- Run: `python -m pytest tests/ -v --tb=short --override-ini="addopts="`

### Documentation
- Module-level docstring on every `.py` file
- Docstring on every public function/class
- No comments in code unless explaining WHY, not WHAT

### Dead Code
- If it's not called, delete it
- If a visitor method exists but the node is never created, mark it or remove it
- No commented-out code

## Pipeline Invariants

1. `CompileResult.bytecode` is always `tuple[list[Instruction], list[Any]] | None`
2. To run bytecode: unpack first, then call `vm.run(instructions, constants)`
3. `tokenize()` always receives `(source, filename)` — never just source
4. Parser always receives `(tokens, filename)` — never just tokens
5. Type checker returns `(type_map, errors)` — both are dicts/lists, never None

## Commit Protocol

1. All 392+ tests must pass
2. No unused imports
3. No wildcard imports
4. No dead code
5. Commit message: imperative mood, <72 chars subject
6. Push to `main` on GitHub
