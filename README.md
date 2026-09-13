# Cosmic

A modern, statically-typed programming language with Python & ByteCode backends.

## Overview

Cosmic is a Pythonic language that compiles to **Python source code** or runs directly via a **custom bytecode VM**. It features a clean, modern syntax with powerful abstractions while maintaining full compatibility with the Python ecosystem.

**Key Features:**
- **Static typing with inference** — type annotations optional, types inferred automatically
- **Dual backend** — transpile to Python or compile to custom ByteCode
- **Python library compatibility** — use any Python library from Cosmic
- **Rich syntax** — pattern matching, records, enums, lambdas, pipe operator
- **Batteries included** — stdlib with collections, math, crypto, IO, HTTP, and more
- **Professional tooling** — CLI, REPL, type checker, linter integration

## Installation

```bash
# From source
git clone https://github.com/CosmicLang/cosmic.git
cd cosmic
pip install -e ".[dev]"
```

**Requirements:** Python >= 3.10

## Quick Start

### Hello World

```cosmic
fn main() {
    println("Hello, World!")
}

main()
```

Run it:
```bash
cosmic run hello.cos
# Output: Hello, World!
```

### Transpile to Python

```bash
cosmic transpile hello.cos
# Output: print('Hello, World!')
```

### Compile to ByteCode

```bash
cosmic bytecode hello.cos
# Shows bytecode instructions and runs them
```

## Language Syntax

### Variables and Types

```cosmic
let name = "Cosmic"          # type inferred as string
let age = 25                 # type inferred as int
let pi = 3.14159            # type inferred as float
let active = true            # type inferred as bool

# Explicit types
let count: int = 0
let label: string = "hello"
```

### Functions

```cosmic
# Basic function
fn add(a, b) {
    return a + b
}

# With type annotations
fn multiply(a: int, b: int) -> int {
    return a * b
}

# Expression body
fn square(x) = x * x

# Arrow function
fn greet(name) => println("Hello, " + name)
```

### Records (Structs)

```cosmic
record Point(x: int, y: int)
record User(name: string, email: string, age: int)

fn main() {
    let p = Point(3, 4)
    println(p.x)           # 3
    println(p.y)           # 4
    
    let user = User("Alice", "alice@example.com", 30)
    println(user.name)     # Alice
}
```

### Enums

```cosmic
enum Color {
    RED,
    GREEN,
    BLUE
}

enum Result {
    Ok(value),
    Err(message)
}

fn main() {
    let c = Color.RED
    println(c)
    
    let r = Result.Ok(42)
    println(r)
}
```

### Pattern Matching

```cosmic
fn describe(color: Color) -> string {
    return match color {
        Color.RED => "warm",
        Color.GREEN => "nature",
        Color.BLUE => "cool"
    }
}
```

### Control Flow

```cosmic
# If/else
if age >= 18 {
    println("adult")
} else {
    println("minor")
}

# While loops
let i = 0
while i < 10 {
    println(i)
    i += 1
}

# For loops
for i in range(10) {
    println(i)
}

# Infinite loop with break
loop {
    let input = read_line()
    if input == "quit" { break }
}
```

### Lambdas and Higher-Order Functions

```cosmic
let double = lambda x => x * 2
let square = lambda x => x * x

fn apply(f, x) {
    return f(x)
}

fn main() {
    println(apply(double, 5))   # 10
    println(apply(square, 5))   # 25
    
    # Lambda with multiple statements
    let process = lambda x => {
        let y = x * 2
        return y + 1
    }
    println(process(5))          # 11
}
```

### Operators

```cosmic
# Arithmetic
let a = 10 + 3      # 13
let b = 10 - 3      # 7
let c = 10 * 3      # 30
let d = 10 / 3      # 3.333...
let e = 10 // 3     # 3 (floor division)
let f = 10 % 3      # 1 (modulo)
let g = 2 ** 8      # 256 (power)

# Comparison
let eq = (a == b)   # equal
let ne = (a != b)   # not equal
let lt = (a < b)    # less than
let gt = (a > b)    # greater than

# Logical
let and = (true && false)   # false
let or = (true || false)    # true
let not = !true             # false

# Pipe operator
let result = 5 |> double |> square   # (5*2)^2 = 100

# Nullish coalescing
let value = nullable ?? "default"
```

### Error Handling

```cosmic
fn divide(a: int, b: int) -> int {
    if b == 0 {
        throw "Division by zero"
    }
    return a / b
}

try {
    let result = divide(10, 0)
    println(result)
} catch (error) {
    println("Error: " + error)
}
```

### Async/Await

```cosmic
async fn fetch_data(url: string) -> string {
    # async operations
    return "data"
}

fn main() {
    let data = await fetch_data("https://api.example.com")
    println(data)
}
```

## Standard Library

Cosmic includes a comprehensive standard library:

| Module | Description |
|--------|-------------|
| `math` | Mathematical functions (sin, cos, sqrt, etc.) |
| `collections` | Lists, dicts, sets, deques, queues |
| `strings` | String manipulation utilities |
| `io` | File I/O operations |
| `path` | Path manipulation |
| `datetime` | Date and time utilities |
| `json` | JSON serialization/deserialization |
| `crypto` | Cryptographic functions (hash, uuid) |
| `http` | HTTP client |
| `regex` | Regular expressions |
| `os` | OS utilities (env vars, system info) |
| `testing` | Test assertions and utilities |
| `errors` | Error types and handling |

### Example: Using stdlib

```cosmic
use math

fn main() {
    let x = 9.0
    println(math.sqrt(x))    # 3.0
    println(math.pi)         # 3.141592653589793
}
```

## CLI Commands

```bash
# Run a .cos file
cosmic run file.cos

# Transpile to Python
cosmic transpile file.cos

# Compile to bytecode
cosmic bytecode file.cos

# Show tokens
cosmic tokens file.cos

# Show AST
cosmic ast file.cos

# Type check
cosmic check file.cos

# Show version
cosmic version

# Start REPL
cosmic repl
```

### REPL Commands

```
> :help          Show available commands
> :tokens <code> Show tokenization
> :ast <code>    Show AST
> :bytecode      Show last bytecode
> :quit          Exit REPL
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=cosmic --cov-report=html

# Run specific test file
pytest tests/test_parser.py
```

## Project Structure

```
cosmic/
├── cosmic/
│   ├── lexer/           # Tokenizer
│   │   ├── lexer.py
│   │   └── tokens.py
│   ├── parser/          # Parser (recursive descent + Pratt)
│   │   └── parser.py
│   ├── ast/             # Abstract Syntax Tree
│   │   └── nodes.py
│   ├── types/           # Type checker
│   │   └── checker.py
│   ├── backends/
│   │   ├── python/      # Python transpiler
│   │   │   └── transpiler.py
│   │   └── bytecode/    # ByteCode compiler + VM
│   │       └── compiler.py
│   ├── compiler/        # Pipeline orchestration
│   │   └── pipeline.py
│   ├── stdlib/          # Standard library (13 modules)
│   ├── cli.py           # Command-line interface
│   └── REPL.py          # Interactive REPL
├── tests/               # Test suite
├── examples/            # Example .cos files
├── pyproject.toml       # Build configuration
└── README.md
```

## Examples

See the `examples/` directory for complete programs:
- `recursion.cos` — Fibonacci and factorial
- `records.cos` — Point record and distance function
- `lambdas.cos` — Lambda expressions and higher-order functions
- `enums.cos` — Enum definitions and usage

## Roadmap

- [ ] Pattern matching improvements
- [ ] Module system (`use` statements)
- [ ] Interfaces and traits
- [ ] List comprehensions
- [ ] Decorators
- [ ] Package manager
- [ ] VS Code extension

## License

MIT License

## Contributing

Contributions welcome! Please read CONTRIBUTING.md (coming soon) and submit pull requests.

## Links

- [Repository](https://github.com/CosmicLang/cosmic)
- [Issues](https://github.com/CosmicLang/cosmic/issues)
- [PyPI](https://pypi.org/project/cosmic-lang/) (coming soon)
