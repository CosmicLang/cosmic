use std::collections::HashMap;
use crate::ast::*;
use crate::lexer::Spanned;

#[derive(Debug, Clone, PartialEq)]
pub enum Type {
    Int,
    Float,
    String,
    Bool,
    Char,
    Void,
    Array(Box<Type>),
    Function {
        params: Vec<Type>,
        return_type: Box<Type>,
    },
    Struct(String),
    Enum(String),
    Unknown,
}

#[derive(Debug, Clone)]
pub struct TypeEnv {
    scopes: Vec<HashMap<String, Type>>,
}

impl TypeEnv {
    pub fn new() -> Self {
        TypeEnv {
            scopes: vec![HashMap::new()],
        }
    }

    pub fn push_scope(&mut self) {
        self.scopes.push(HashMap::new());
    }

    pub fn pop_scope(&mut self) {
        self.scopes.pop();
    }

    pub fn define(&mut self, name: &str, ty: Type) {
        self.scopes.last_mut().unwrap().insert(name.to_string(), ty);
    }

    pub fn resolve(&self, name: &str) -> Option<&Type> {
        for scope in self.scopes.iter().rev() {
            if let Some(ty) = scope.get(name) {
                return Some(ty);
            }
        }
        None
    }
}

pub struct TypeChecker {
    env: TypeEnv,
    errors: Vec<String>,
}

impl TypeChecker {
    pub fn new() -> Self {
        TypeChecker {
            env: TypeEnv::new(),
            errors: Vec::new(),
        }
    }

    pub fn check_program(&mut self, program: &[Spanned<Ast>]) -> Result<(), Vec<String>> {
        for stmt in program {
            if self.check_statement(stmt).is_err() {
                // Error already recorded
            }
        }

        if self.errors.is_empty() {
            Ok(())
        } else {
            Err(self.errors.clone())
        }
    }

    fn check_statement(&mut self, stmt: &Spanned<Ast>) -> Result<Type, ()> {
        match &stmt.value {
            Ast::Let { name, ty, value, .. } => {
                let inferred = if let Some(val) = value {
                    self.check_expression(val)?
                } else if let Some(ann) = ty {
                    self.resolve_type(ann)
                } else {
                    self.error("Cannot infer type", stmt);
                    Type::Unknown
                };

                if let Some(ann) = ty {
                    let declared = self.resolve_type(ann);
                    if declared != Type::Unknown && inferred != Type::Unknown && declared != inferred {
                        self.error(&format!("Type mismatch: expected {:?}, got {:?}", declared, inferred), stmt);
                    }
                }

                self.env.define(&name, inferred.clone());
                Ok(Type::Void)
            }
            Ast::Function { name, params, return_type, body, .. } => {
                let param_types: Vec<Type> = params.iter()
                    .filter_map(|p| p.ty.as_ref().map(|t| self.resolve_type(t)))
                    .collect();

                let ret_type = return_type.as_ref()
                    .map(|t| self.resolve_type(t))
                    .unwrap_or(Type::Void);

                let func_type = Type::Function {
                    params: param_types,
                    return_type: Box::new(ret_type.clone()),
                };

                self.env.define(&name, func_type);
                self.env.push_scope();

                for param in params {
                    if let Some(ty) = &param.ty {
                        self.env.define(&param.name, self.resolve_type(ty));
                    }
                }

                let body_type = self.check_expression(body)?;
                
                self.env.pop_scope();

                if ret_type != Type::Void && body_type != ret_type {
                    self.error(&format!("Return type mismatch: expected {:?}, got {:?}", ret_type, body_type), stmt);
                }

                Ok(Type::Void)
            }
            Ast::Struct { name, fields: _, .. } => {
                self.env.define(&name, Type::Struct(name.clone()));
                Ok(Type::Void)
            }
            Ast::Enum { name, .. } => {
                self.env.define(&name, Type::Enum(name.clone()));
                Ok(Type::Void)
            }
            Ast::Return(Some(expr)) => {
                self.check_expression(expr)
            }
            Ast::Return(None) => Ok(Type::Void),
            Ast::Expr(expr) => self.check_expression(expr),
            Ast::While { condition, body } => {
                let cond_type = self.check_expression(condition)?;
                if cond_type != Type::Bool {
                    self.error("While condition must be bool", stmt);
                }
                self.check_expression(body)?;
                Ok(Type::Void)
            }
            Ast::For { iter, body, .. } => {
                self.check_expression(iter)?;
                self.check_expression(body)?;
                Ok(Type::Void)
            }
            Ast::Loop(body) => {
                self.check_expression(body)?;
                Ok(Type::Void)
            }
            Ast::Break | Ast::Continue => Ok(Type::Void),
            Ast::Assign { target, value } => {
                let target_type = self.check_expression(target)?;
                let value_type = self.check_expression(value)?;
                if target_type != value_type {
                    self.error(&format!("Assignment type mismatch: {:?} = {:?}", target_type, value_type), stmt);
                }
                Ok(Type::Void)
            }
            _ => {
                self.error("Invalid statement", stmt);
                Err(())
            }
        }
    }

    fn check_expression(&mut self, expr: &Spanned<Ast>) -> Result<Type, ()> {
        match &expr.value {
            Ast::Literal(lit) => Ok(match lit {
                Literal::Integer(_) => Type::Int,
                Literal::Float(_) => Type::Float,
                Literal::String(_) => Type::String,
                Literal::Bool(_) => Type::Bool,
                Literal::Char(_) => Type::Char,
                Literal::Null => Type::Unknown,
            }),
            Ast::Ident(name) => {
                self.env.resolve(&name)
                    .cloned()
                    .ok_or_else(|| {
                        self.error(&format!("Undefined variable: {}", name), expr);
                        ()
                    })
            }
            Ast::BinaryOp { op, left, right } => {
                let left_type = self.check_expression(left)?;
                let right_type = self.check_expression(right)?;

                match op {
                    BinOp::Add | BinOp::Sub | BinOp::Mul | BinOp::Div | BinOp::Mod => {
                        if left_type == Type::String && op == &BinOp::Add {
                            Ok(Type::String)
                        } else if left_type == right_type {
                            Ok(left_type)
                        } else {
                            self.error("Type mismatch in binary operation", expr);
                            Err(())
                        }
                    }
                    BinOp::Eq | BinOp::Ne | BinOp::Lt | BinOp::Gt | BinOp::Le | BinOp::Ge => {
                        Ok(Type::Bool)
                    }
                    BinOp::And | BinOp::Or => {
                        if left_type == Type::Bool && right_type == Type::Bool {
                            Ok(Type::Bool)
                        } else {
                            self.error("Logical operators require bool operands", expr);
                            Err(())
                        }
                    }
                    _ => Ok(left_type),
                }
            }
            Ast::UnaryOp { op, expr: inner } => {
                let inner_type = self.check_expression(inner)?;
                match op {
                    UnaryOp::Neg => Ok(inner_type),
                    UnaryOp::Not => Ok(Type::Bool),
                    UnaryOp::BitNot => Ok(inner_type),
                }
            }
            Ast::Call { func, args } => {
                let func_type = self.check_expression(func)?;
                if let Type::Function { params, return_type } = func_type {
                    if params.len() != args.len() {
                        self.error(&format!("Expected {} arguments, got {}", params.len(), args.len()), expr);
                    }
                    Ok(*return_type)
                } else {
                    self.error("Not a function", expr);
                    Err(())
                }
            }
            Ast::If { condition, then_branch, else_branch } => {
                let cond_type = self.check_expression(condition)?;
                if cond_type != Type::Bool {
                    self.error("If condition must be bool", expr);
                }
                let then_type = self.check_expression(then_branch)?;
                if let Some(else_expr) = else_branch {
                    let else_type = self.check_expression(else_expr)?;
                    if then_type != else_type {
                        self.error("If branches must have same type", expr);
                    }
                }
                Ok(then_type)
            }
            Ast::Block(stmts) => {
                self.env.push_scope();
                let mut last_type = Type::Void;
                for stmt in stmts {
                    last_type = self.check_statement(stmt)?;
                }
                self.env.pop_scope();
                Ok(last_type)
            }
            Ast::Lambda { params, body } => {
                self.env.push_scope();
                let mut param_types = Vec::new();
                for param in params {
                    let ty = param.ty.as_ref()
                        .map(|t| self.resolve_type(t))
                        .unwrap_or(Type::Unknown);
                    self.env.define(&param.name, ty.clone());
                    param_types.push(ty);
                }
                let body_type = self.check_expression(body)?;
                self.env.pop_scope();
                Ok(Type::Function {
                    params: param_types,
                    return_type: Box::new(body_type),
                })
            }
            _ => {
                self.error("Invalid expression", expr);
                Err(())
            }
        }
    }

    fn resolve_type(&self, ann: &TypeAnnotation) -> Type {
        match ann {
            TypeAnnotation::Simple(name) => match name.as_str() {
                "Int" | "int" => Type::Int,
                "Float" | "float" => Type::Float,
                "String" | "string" => Type::String,
                "Bool" | "bool" => Type::Bool,
                "Char" | "char" => Type::Char,
                "Void" | "void" => Type::Void,
                _ => Type::Struct(name.clone()),
            },
            TypeAnnotation::Array(inner) => Type::Array(Box::new(self.resolve_type(inner))),
            TypeAnnotation::Function { params, return_type } => Type::Function {
                params: params.iter().map(|t| self.resolve_type(t)).collect(),
                return_type: Box::new(self.resolve_type(return_type)),
            },
            TypeAnnotation::Nullable(inner) => self.resolve_type(inner),
            TypeAnnotation::Tuple(_) => Type::Unknown,
            TypeAnnotation::Generic { name, .. } => Type::Struct(name.clone()),
        }
    }

    fn error(&mut self, msg: &str, span: &Spanned<Ast>) {
        self.errors.push(format!("{} at line {}", msg, span.line));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;
    use crate::parser::Parser;

    #[test]
    fn test_type_check_let() {
        let mut lexer = Lexer::new("let x = 42;");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();

        let mut checker = TypeChecker::new();
        assert!(checker.check_program(&ast).is_ok());
    }

    #[test]
    fn test_type_check_function() {
        let mut lexer = Lexer::new("fn add(a: Int, b: Int) -> Int { return a + b; }");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();

        let mut checker = TypeChecker::new();
        assert!(checker.check_program(&ast).is_ok());
    }
}
