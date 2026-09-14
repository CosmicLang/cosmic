use crate::ast::Ast;
use crate::codegen::CodeGen;
use crate::lexer::{Lexer, TokenSpan};
use crate::parser::Parser;
use crate::typeck::TypeChecker;

pub struct Compiler;

impl Compiler {
    pub fn new() -> Self {
        Compiler
    }

    pub fn tokenize(&self, source: &str) -> Result<Vec<TokenSpan>, String> {
        let mut lexer = Lexer::new(source);
        lexer.tokenize()
    }

    pub fn parse(&self, source: &str) -> Result<Vec<crate::lexer::Spanned<Ast>>, String> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize()?;
        let mut parser = Parser::new(tokens);
        parser.parse_program()
    }

    pub fn compile(&self, source: &str) -> Result<String, String> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize()?;
        
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program()?;

        let mut typeck = TypeChecker::new();
        typeck.check_program(&ast).map_err(|e| e.join("\n"))?;

        let mut codegen = CodeGen::new();
        let output = codegen.generate(&ast);

        Ok(output)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compiler() {
        let compiler = Compiler::new();
        let source = "let x = 42;";
        let result = compiler.compile(source);
        assert!(result.is_ok());
    }
}
