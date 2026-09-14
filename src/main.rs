use clap::Parser as ClapParser;
use std::path::PathBuf;

#[derive(ClapParser)]
#[command(name = "cosmic")]
#[command(about = "A modern, elegant, statically-typed programming language")]
struct Cli {
    /// Input file
    file: Option<PathBuf>,

    /// Run in REPL mode
    #[arg(short, long)]
    repl: bool,

    /// Print tokens
    #[arg(long)]
    tokens: bool,

    /// Print AST
    #[arg(long)]
    ast: bool,
}

fn main() {
    let cli = Cli::parse();

    if let Some(file) = cli.file {
        let source = match std::fs::read_to_string(&file) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("Error reading file: {}", e);
                std::process::exit(1);
            }
        };
        let compiler = cosmic_lib::Compiler::new();

        if cli.tokens {
            match compiler.tokenize(&source) {
                Ok(tokens) => {
                    for token in &tokens {
                        println!("{:?}", token);
                    }
                }
                Err(e) => {
                    eprintln!("Error: {}", e);
                    std::process::exit(1);
                }
            }
            return;
        }

        if cli.ast {
            match compiler.parse(&source) {
                Ok(ast) => {
                    println!("{:#?}", ast);
                }
                Err(e) => {
                    eprintln!("Error: {}", e);
                    std::process::exit(1);
                }
            }
            return;
        }

        match compiler.compile(&source) {
            Ok(result) => println!("{}", result),
            Err(e) => {
                eprintln!("Error: {}", e);
                std::process::exit(1);
            }
        }
    } else if cli.repl {
        println!("Cosmic REPL v0.1.0");
        println!("Type 'exit' to quit.");
        
        let compiler = cosmic_lib::Compiler::new();
        let stdin = std::io::stdin();
        
        loop {
            print!("> ");
            use std::io::Write;
            let _ = std::io::stdout().flush();
            
            let mut input = String::new();
            if stdin.read_line(&mut input).is_err() {
                break;
            }
            
            let input = input.trim();
            if input == "exit" || input == "quit" {
                break;
            }
            
            if input.is_empty() {
                continue;
            }
            
            match compiler.compile(input) {
                Ok(result) => println!("{}", result),
                Err(e) => eprintln!("Error: {}", e),
            }
        }
    } else {
        eprintln!("Usage: cosmic <file> or cosmic --repl");
        std::process::exit(1);
    }
}
