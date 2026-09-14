# Cosmic

A modern, elegant, statically-typed programming language written in Rust.

## Features

- **Clean syntax** — inspired by Rust, Kotlin, and modern languages
- **Static typing** with strong type inference
- **Pattern matching** with exhaustive checks
- **First-class functions** and closures
- **Structs and enums** with method support
- **Expression-oriented** control flow
- **Zero-cost abstractions** where possible

## Example

```cosmic
// Variables
let x = 42
let name: String = "Cosmic"
mut counter = 0

// Functions
fn add(a: Int, b: Int) -> Int = a + b

fn greet(name: String) {
    println("Hello, {name}!")
}

// Structs
struct Point {
    x: Float
    y: Float
}

// Enums
enum Color {
    Red
    Green
    Blue
}

// Pattern matching
match color {
    Color.Red -> "red"
    Color.Green -> "green"  
    Color.Blue -> "blue"
}

// Control flow (expressions)
let result = if x > 0 { x } else { -x }

// Closures
let double = |x| x * 2
```

## Building

```bash
cargo build --release
```

## Usage

```bash
# Run a file
cosmic examples/hello.cosmic

# Start REPL
cosmic --repl

# Print tokens
cosmic --tokens examples/hello.cosmic

# Print AST
cosmic --ast examples/hello.cosmic
```

## Examples

See the `examples/` directory for more examples.

## License

MIT
