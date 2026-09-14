use crate::ast::*;
use crate::lexer::{Token, TokenSpan, Spanned};
use std::mem;

pub struct Parser {
    tokens: Vec<TokenSpan>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<TokenSpan>) -> Self {
        Parser { tokens, pos: 0 }
    }

    fn peek(&self) -> &Token {
        &self.current().value
    }

    fn current(&self) -> &TokenSpan {
        self.tokens.get(self.pos).unwrap_or(&TokenSpan {
            value: Token::Eof,
            line: 0,
            col: 0,
            len: 0,
        })
    }

    fn advance(&mut self) -> TokenSpan {
        let token = self.tokens[self.pos].clone();
        self.pos += 1;
        token
    }

    fn expect(&mut self, expected: &Token) -> Result<TokenSpan, String> {
        let token = self.current().clone();
        if mem::discriminant(&token.value) == mem::discriminant(expected) {
            self.advance();
            Ok(token)
        } else {
            Err(format!(
                "Expected {:?}, got {:?} at line {}",
                expected, token.value, token.line
            ))
        }
    }

    fn expect_ident(&mut self) -> Result<String, String> {
        match self.advance().value {
            Token::Ident(s) => Ok(s),
            t => Err(format!("Expected identifier, got {:?}", t)),
        }
    }

    fn parse_type_annotation(&mut self) -> Result<TypeAnnotation, String> {
        let base = match self.peek() {
            Token::Ident(_) => {
                let name = self.expect_ident()?;
                if self.peek() == &Token::Lt {
                    self.advance(); // <
                    let mut args = Vec::new();
                    loop {
                        args.push(self.parse_type_annotation()?);
                        if self.peek() == &Token::Gt {
                            self.advance();
                            break;
                        }
                        self.expect(&Token::Comma)?;
                    }
                    TypeAnnotation::Generic { name, args }
                } else {
                    TypeAnnotation::simple(&name)
                }
            }
            Token::LBracket => {
                self.advance();
                let inner = self.parse_type_annotation()?;
                self.expect(&Token::RBracket)?;
                TypeAnnotation::array(inner)
            }
            Token::LParen => {
                self.advance();
                let mut types = Vec::new();
                loop {
                    types.push(self.parse_type_annotation()?);
                    if self.peek() == &Token::RParen {
                        self.advance();
                        break;
                    }
                    self.expect(&Token::Comma)?;
                }
                TypeAnnotation::Tuple(types)
            }
            t => return Err(format!("Expected type, got {:?}", t)),
        };

        if self.peek() == &Token::Question {
            self.advance();
            Ok(TypeAnnotation::nullable(base))
        } else {
            Ok(base)
        }
    }

    fn parse_param(&mut self) -> Result<Param, String> {
        let name = self.expect_ident()?;
        let ty = if self.peek() == &Token::Colon {
            self.advance();
            Some(self.parse_type_annotation()?)
        } else {
            None
        };
        Ok(Param { name, ty })
    }

    fn parse_literal(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance();
        let ast = match &token.value {
            Token::Integer(n) => Ast::Literal(Literal::Integer(*n)),
            Token::Float(n) => Ast::Literal(Literal::Float(*n)),
            Token::String(s) => Ast::Literal(Literal::String(s.clone())),
            Token::Bool(b) => Ast::Literal(Literal::Bool(*b)),
            Token::Char(c) => Ast::Literal(Literal::Char(*c)),
            Token::Null => Ast::Literal(Literal::Null),
            _ => return Err(format!("Expected literal, got {:?}", token.value)),
        };
        Ok(Spanned {
            value: ast,
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_primary(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.current().clone();
        
        match &token.value {
            Token::Integer(_) | Token::Float(_) | Token::String(_) | 
            Token::Bool(_) | Token::Char(_) | Token::Null => {
                self.parse_literal()
            }
            Token::Ident(_) => {
                let name = self.expect_ident()?;
                Ok(Spanned {
                    value: Ast::Ident(name),
                    line: token.line,
                    col: token.col,
                    len: token.len,
                })
            }
            Token::LParen => {
                self.advance(); // (
                let expr = self.parse_expression()?;
                self.expect(&Token::RParen)?;
                Ok(expr)
            }
            Token::LBrace => {
                self.parse_block()
            }
            Token::If => {
                self.parse_if()
            }
            Token::Match => {
                self.parse_match()
            }
            Token::Fn => {
                self.parse_lambda()
            }
            _ => Err(format!("Unexpected token: {:?}", token.value)),
        }
    }

    fn parse_postfix(&mut self, expr: Spanned<Ast>) -> Result<Spanned<Ast>, String> {
        let mut result = expr;
        loop {
            match self.peek() {
                Token::LParen => {
                    let line = result.line;
                    let col = result.col;
                    let len = result.len;
                    // Function call
                    self.advance();
                    let mut args = Vec::new();
                    if self.peek() != &Token::RParen {
                        loop {
                            args.push(self.parse_expression()?);
                            if self.peek() == &Token::RParen {
                                break;
                            }
                            self.expect(&Token::Comma)?;
                        }
                    }
                    self.expect(&Token::RParen)?;
                    result = Spanned {
                        value: Ast::Call {
                            func: Box::new(result),
                            args,
                        },
                        line,
                        col,
                        len,
                    };
                }
                Token::LBracket => {
                    let line = result.line;
                    let col = result.col;
                    let len = result.len;
                    // Index access
                    self.advance();
                    let index = self.parse_expression()?;
                    self.expect(&Token::RBracket)?;
                    result = Spanned {
                        value: Ast::Index {
                            object: Box::new(result),
                            index: Box::new(index),
                        },
                        line,
                        col,
                        len,
                    };
                }
                Token::Dot => {
                    let line = result.line;
                    let col = result.col;
                    let len = result.len;
                    // Field access
                    self.advance();
                    let field = self.expect_ident()?;
                    result = Spanned {
                        value: Ast::FieldAccess {
                            object: Box::new(result),
                            field,
                        },
                        line,
                        col,
                        len,
                    };
                }
                _ => break,
            }
        }
        Ok(result)
    }

    fn parse_unary(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.current().clone();
        match &token.value {
            Token::Minus => {
                self.advance();
                let expr = self.parse_unary()?;
                Ok(Spanned {
                    value: Ast::UnaryOp {
                        op: UnaryOp::Neg,
                        expr: Box::new(expr),
                    },
                    line: token.line,
                    col: token.col,
                    len: token.len,
                })
            }
            Token::Bang => {
                self.advance();
                let expr = self.parse_unary()?;
                Ok(Spanned {
                    value: Ast::UnaryOp {
                        op: UnaryOp::Not,
                        expr: Box::new(expr),
                    },
                    line: token.line,
                    col: token.col,
                    len: token.len,
                })
            }
            Token::Tilde => {
                self.advance();
                let expr = self.parse_unary()?;
                Ok(Spanned {
                    value: Ast::UnaryOp {
                        op: UnaryOp::BitNot,
                        expr: Box::new(expr),
                    },
                    line: token.line,
                    col: token.col,
                    len: token.len,
                })
            }
            _ => {
                let primary = self.parse_primary()?;
                self.parse_postfix(primary)
            }
        }
    }

    fn precedence(op: &BinOp) -> u8 {
        match op {
            BinOp::Or => 1,
            BinOp::And => 2,
            BinOp::BitOr => 3,
            BinOp::BitXor => 4,
            BinOp::BitAnd => 5,
            BinOp::Eq | BinOp::Ne => 6,
            BinOp::Lt | BinOp::Gt | BinOp::Le | BinOp::Ge => 7,
            BinOp::Shl | BinOp::Shr => 8,
            BinOp::Add | BinOp::Sub => 9,
            BinOp::Mul | BinOp::Div | BinOp::Mod => 10,
            BinOp::Pow => 11,
        }
    }

    fn parse_binop(&mut self) -> Result<BinOp, String> {
        match self.peek() {
            Token::Plus => { self.advance(); Ok(BinOp::Add) }
            Token::Minus => { self.advance(); Ok(BinOp::Sub) }
            Token::Star => { self.advance(); Ok(BinOp::Mul) }
            Token::Slash => { self.advance(); Ok(BinOp::Div) }
            Token::Percent => { self.advance(); Ok(BinOp::Mod) }
            Token::EqEq => { self.advance(); Ok(BinOp::Eq) }
            Token::Ne => { self.advance(); Ok(BinOp::Ne) }
            Token::Lt => { self.advance(); Ok(BinOp::Lt) }
            Token::Gt => { self.advance(); Ok(BinOp::Gt) }
            Token::Le => { self.advance(); Ok(BinOp::Le) }
            Token::Ge => { self.advance(); Ok(BinOp::Ge) }
            Token::AmpAmp => { self.advance(); Ok(BinOp::And) }
            Token::PipePipe => { self.advance(); Ok(BinOp::Or) }
            Token::Amp => { self.advance(); Ok(BinOp::BitAnd) }
            Token::Pipe => { self.advance(); Ok(BinOp::BitOr) }
            Token::Caret => { self.advance(); Ok(BinOp::BitXor) }
            _ => Err(format!("Expected operator, got {:?}", self.peek())),
        }
    }

    fn parse_expression_precedence(&mut self, min_prec: u8) -> Result<Spanned<Ast>, String> {
        let mut left = self.parse_unary()?;

        loop {
            let op = match self.parse_binop() {
                Ok(op) => op,
                Err(_) => break,
            };

            let prec = Self::precedence(&op);
            if prec < min_prec {
                break;
            }

            let right = self.parse_expression_precedence(prec + 1)?;
            left = Spanned {
                value: Ast::BinaryOp {
                    op,
                    left: Box::new(left.clone()),
                    right: Box::new(right),
                },
                line: left.line,
                col: left.col,
                len: left.len,
            };
        }

        Ok(left)
    }

    fn parse_expression(&mut self) -> Result<Spanned<Ast>, String> {
        self.parse_expression_precedence(1)
    }

    fn parse_block(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // {
        let mut stmts = Vec::new();

        while self.peek() != &Token::RBrace {
            if self.peek() == &Token::Eof {
                return Err("Unexpected end of file in block".into());
            }
            stmts.push(self.parse_statement()?);
        }

        self.expect(&Token::RBrace)?;

        Ok(Spanned {
            value: Ast::Block(stmts),
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_if(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // if
        let condition = Box::new(self.parse_expression()?);
        let then_branch = Box::new(self.parse_block()?);

        let else_branch = if self.peek() == &Token::Else {
            self.advance();
            if self.peek() == &Token::If {
                Some(Box::new(self.parse_if()?))
            } else {
                Some(Box::new(self.parse_block()?))
            }
        } else {
            None
        };

        Ok(Spanned {
            value: Ast::If {
                condition,
                then_branch,
                else_branch,
            },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_match(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // match
        let expr = Box::new(self.parse_expression()?);
        self.expect(&Token::LBrace)?;

        let mut arms = Vec::new();
        while self.peek() != &Token::RBrace {
            let pattern = self.parse_pattern()?;
            
            let guard = if let Token::Ident(s) = self.peek() {
                if s == "if" {
                    self.advance();
                    Some(Box::new(self.parse_expression()?))
                } else {
                    None
                }
            } else {
                None
            };

            self.expect(&Token::FatArrow)?;
            let body = Box::new(self.parse_expression()?);

            arms.push(MatchArm {
                pattern,
                guard,
                body,
            });

            if self.peek() == &Token::Comma {
                self.advance();
            }
        }

        self.expect(&Token::RBrace)?;

        Ok(Spanned {
            value: Ast::Match { expr, arms },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_pattern(&mut self) -> Result<Pattern, String> {
        match self.peek().clone() {
            Token::Ident(_) => {
                let name = self.expect_ident()?;
                if self.peek() == &Token::LParen {
                    self.advance();
                    let mut args = Vec::new();
                    loop {
                        args.push(self.parse_pattern()?);
                        if self.peek() == &Token::RParen {
                            self.advance();
                            break;
                        }
                        self.expect(&Token::Comma)?;
                    }
                    Ok(Pattern::Enum { name, args })
                } else if name == "_" {
                    Ok(Pattern::Wildcard)
                } else {
                    Ok(Pattern::Ident(name))
                }
            }
            Token::Integer(_) | Token::Float(_) | Token::String(_) | 
            Token::Bool(_) | Token::Char(_) => {
                let lit = self.parse_literal()?;
                match lit.value {
                    Ast::Literal(l) => Ok(Pattern::Literal(l)),
                    _ => unreachable!(),
                }
            }
            Token::LBrace => {
                self.advance();
                let mut fields = Vec::new();
                loop {
                    let field_name = self.expect_ident()?;
                    self.expect(&Token::Colon)?;
                    let pattern = self.parse_pattern()?;
                    fields.push((field_name, pattern));
                    if self.peek() == &Token::RBrace {
                        self.advance();
                        break;
                    }
                    self.expect(&Token::Comma)?;
                }
                Ok(Pattern::Tuple(vec![])) // Simplified for now
            }
            _ => Err(format!("Expected pattern, got {:?}", self.peek())),
        }
    }

    fn parse_lambda(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // fn
        self.expect(&Token::LParen)?;

        let mut params = Vec::new();
        if self.peek() != &Token::RParen {
            loop {
                params.push(self.parse_param()?);
                if self.peek() == &Token::RParen {
                    break;
                }
                self.expect(&Token::Comma)?;
            }
        }
        self.expect(&Token::RParen)?;

        let body = if self.peek() == &Token::Arrow {
            self.advance();
            Box::new(self.parse_expression()?)
        } else {
            Box::new(self.parse_block()?)
        };

        Ok(Spanned {
            value: Ast::Lambda { params, body },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_statement(&mut self) -> Result<Spanned<Ast>, String> {
        match self.peek() {
            Token::Let => self.parse_let(),
            Token::Return => self.parse_return(),
            Token::While => self.parse_while(),
            Token::For => self.parse_for(),
            Token::Loop => self.parse_loop(),
            Token::Break => {
                let token = self.advance();
                self.expect(&Token::Semicolon)?;
                Ok(Spanned {
                    value: Ast::Break,
                    line: token.line,
                    col: token.col,
                    len: token.len,
                })
            }
            Token::Continue => {
                let token = self.advance();
                self.expect(&Token::Semicolon)?;
                Ok(Spanned {
                    value: Ast::Continue,
                    line: token.line,
                    col: token.col,
                    len: token.len,
                })
            }
            Token::Fn => self.parse_function(),
            Token::Struct => self.parse_struct(),
            Token::Enum => self.parse_enum(),
            Token::Import => self.parse_import(),
            _ => {
                let expr = self.parse_expression()?;
                let line = expr.line;
                let col = expr.col;
                let len = expr.len;
                if self.peek() == &Token::Eq {
                    self.advance();
                    let value = self.parse_expression()?;
                    self.expect(&Token::Semicolon)?;
                    Ok(Spanned {
                        value: Ast::Assign {
                            target: Box::new(expr),
                            value: Box::new(value),
                        },
                        line,
                        col,
                        len,
                    })
                } else {
                    self.expect(&Token::Semicolon)?;
                    Ok(Spanned {
                        value: Ast::Expr(Box::new(expr)),
                        line,
                        col,
                        len,
                    })
                }
            }
        }
    }

    fn parse_let(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // let
        let mutable = if self.peek() == &Token::Mut {
            self.advance();
            true
        } else {
            false
        };

        let name = self.expect_ident()?;
        
        let ty = if self.peek() == &Token::Colon {
            self.advance();
            Some(self.parse_type_annotation()?)
        } else {
            None
        };

        let value = if self.peek() == &Token::Eq {
            self.advance();
            Some(Box::new(self.parse_expression()?))
        } else {
            None
        };

        self.expect(&Token::Semicolon)?;

        Ok(Spanned {
            value: Ast::Let {
                name,
                ty,
                value,
                mutable,
            },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_return(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // return
        let value = if self.peek() != &Token::Semicolon {
            Some(Box::new(self.parse_expression()?))
        } else {
            None
        };
        self.expect(&Token::Semicolon)?;

        Ok(Spanned {
            value: Ast::Return(value),
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_while(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // while
        let condition = Box::new(self.parse_expression()?);
        let body = Box::new(self.parse_block()?);

        Ok(Spanned {
            value: Ast::While { condition, body },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_for(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // for
        let var = self.expect_ident()?;
        self.expect(&Token::In)?;
        let iter = Box::new(self.parse_expression()?);
        let body = Box::new(self.parse_block()?);

        Ok(Spanned {
            value: Ast::For { var, iter, body },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_loop(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // loop
        let body = Box::new(self.parse_block()?);

        Ok(Spanned {
            value: Ast::Loop(body),
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_function(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // fn
        let public = if self.peek() == &Token::Pub {
            self.advance();
            true
        } else {
            false
        };

        let name = self.expect_ident()?;
        self.expect(&Token::LParen)?;

        let mut params = Vec::new();
        if self.peek() != &Token::RParen {
            loop {
                params.push(self.parse_param()?);
                if self.peek() == &Token::RParen {
                    break;
                }
                self.expect(&Token::Comma)?;
            }
        }
        self.expect(&Token::RParen)?;

        let return_type = if self.peek() == &Token::Arrow {
            self.advance();
            Some(self.parse_type_annotation()?)
        } else {
            None
        };

        let body = Box::new(self.parse_block()?);

        Ok(Spanned {
            value: Ast::Function {
                name,
                params,
                return_type,
                body,
                public,
            },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_struct(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // struct
        let public = if self.peek() == &Token::Pub {
            self.advance();
            true
        } else {
            false
        };

        let name = self.expect_ident()?;
        self.expect(&Token::LBrace)?;

        let mut fields = Vec::new();
        while self.peek() != &Token::RBrace {
            let field_pub = if self.peek() == &Token::Pub {
                self.advance();
                true
            } else {
                false
            };

            let field_name = self.expect_ident()?;
            self.expect(&Token::Colon)?;
            let ty = self.parse_type_annotation()?;

            fields.push(Field {
                name: field_name,
                ty,
                public: field_pub,
            });

            if self.peek() == &Token::Comma {
                self.advance();
            }
        }

        self.expect(&Token::RBrace)?;

        Ok(Spanned {
            value: Ast::Struct {
                name,
                fields,
                public,
            },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_enum(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // enum
        let public = if self.peek() == &Token::Pub {
            self.advance();
            true
        } else {
            false
        };

        let name = self.expect_ident()?;
        self.expect(&Token::LBrace)?;

        let mut variants = Vec::new();
        while self.peek() != &Token::RBrace {
            let variant_name = self.expect_ident()?;
            
            let fields = if self.peek() == &Token::LParen {
                self.advance();
                let mut fields = Vec::new();
                loop {
                    fields.push(self.parse_type_annotation()?);
                    if self.peek() == &Token::RParen {
                        self.advance();
                        break;
                    }
                    self.expect(&Token::Comma)?;
                }
                fields
            } else {
                Vec::new()
            };

            variants.push(EnumVariant {
                name: variant_name,
                fields,
            });

            if self.peek() == &Token::Comma {
                self.advance();
            }
        }

        self.expect(&Token::RBrace)?;

        Ok(Spanned {
            value: Ast::Enum {
                name,
                variants,
                public,
            },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    fn parse_import(&mut self) -> Result<Spanned<Ast>, String> {
        let token = self.advance(); // import
        
        let mut path = Vec::new();
        path.push(self.expect_ident()?);
        
        while self.peek() == &Token::ColonColon {
            self.advance();
            path.push(self.expect_ident()?);
        }

        let alias = if self.peek() == &Token::As {
            self.advance();
            Some(self.expect_ident()?)
        } else {
            None
        };

        self.expect(&Token::Semicolon)?;

        Ok(Spanned {
            value: Ast::Import { path, alias },
            line: token.line,
            col: token.col,
            len: token.len,
        })
    }

    pub fn parse_program(&mut self) -> Result<Vec<Spanned<Ast>>, String> {
        let mut stmts = Vec::new();

        while self.peek() != &Token::Eof {
            stmts.push(self.parse_statement()?);
        }

        Ok(stmts)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;

    #[test]
    fn test_parse_let() {
        let mut lexer = Lexer::new("let x = 42;");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();
        assert_eq!(ast.len(), 1);
    }

    #[test]
    fn test_parse_function() {
        let mut lexer = Lexer::new("fn add(a: Int, b: Int) -> Int { return a + b; }");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();
        assert_eq!(ast.len(), 1);
    }

    #[test]
    fn test_parse_struct() {
        let mut lexer = Lexer::new("struct Point { x: Float, y: Float }");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();
        assert_eq!(ast.len(), 1);
    }
}
