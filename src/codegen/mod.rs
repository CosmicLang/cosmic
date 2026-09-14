use crate::ast::*;
use crate::lexer::Spanned;

pub struct CodeGen {
    output: String,
    indent: usize,
}

impl CodeGen {
    pub fn new() -> Self {
        CodeGen {
            output: String::new(),
            indent: 0,
        }
    }

    fn indent(&mut self) {
        for _ in 0..self.indent {
            self.output.push_str("    ");
        }
    }

    fn emit(&mut self, s: &str) {
        self.output.push_str(s);
    }

    fn emit_line(&mut self, s: &str) {
        self.indent();
        self.output.push_str(s);
        self.output.push('\n');
    }

    pub fn generate(&mut self, program: &[Spanned<Ast>]) -> String {
        self.emit("#include <stdio.h>\n");
        self.emit("#include <stdlib.h>\n");
        self.emit("#include <string.h>\n");
        self.emit("#include <stdbool.h>\n");
        self.emit("\n");

        for stmt in program {
            self.gen_statement(stmt);
        }

        self.output.clone()
    }

    fn gen_statement(&mut self, stmt: &Spanned<Ast>) {
        match &stmt.value {
            Ast::Let { name, ty, value, .. } => {
                self.indent();
                if let Some(ty_ann) = ty {
                    self.emit(&self.type_to_c(&ty_ann));
                } else {
                    self.emit("auto");
                }
                self.emit(&format!(" {} = ", name));
                if let Some(val) = value {
                    self.gen_expression(val);
                } else {
                    self.emit("NULL");
                }
                self.emit(";\n");
            }
            Ast::Function { name, params, return_type, body, .. } => {
                self.indent();
                if let Some(ret) = return_type {
                    self.emit(&self.type_to_c(&ret));
                } else {
                    self.emit("void");
                }
                self.emit(&format!(" {}(", name));
                for (i, param) in params.iter().enumerate() {
                    if i > 0 {
                        self.emit(", ");
                    }
                    if let Some(ty) = &param.ty {
                        self.emit(&self.type_to_c(&ty));
                    } else {
                        self.emit("auto");
                    }
                    self.emit(&format!(" {}", param.name));
                }
                self.emit(")\n");
                self.gen_expression(body);
                self.emit("\n");
            }
            Ast::Struct { name, fields, .. } => {
                self.emit_line(&format!("typedef struct {} {{", name));
                self.indent += 1;
                for field in fields {
                    self.indent();
                    self.emit(&self.type_to_c(&field.ty));
                    self.emit(&format!(" {};\n", field.name));
                }
                self.indent -= 1;
                self.emit_line(&format!("}} {};", name));
            }
            Ast::Enum { name, variants, .. } => {
                self.emit_line(&format!("// enum {} {{", name));
                self.indent += 1;
                for (i, variant) in variants.iter().enumerate() {
                    self.indent();
                    self.emit(&format!("// {} = {},", variant.name, i));
                    self.emit("\n");
                }
                self.indent -= 1;
                self.emit_line("// }");
            }
            Ast::Import { .. } => {
                // Skip imports for C generation
            }
            Ast::Expr(expr) => {
                self.indent();
                self.gen_expression(expr);
                self.emit(";\n");
            }
            Ast::Assign { target, value } => {
                self.indent();
                self.gen_expression(target);
                self.emit(" = ");
                self.gen_expression(value);
                self.emit(";\n");
            }
            Ast::Return(Some(expr)) => {
                self.indent();
                self.emit("return ");
                self.gen_expression(expr);
                self.emit(";\n");
            }
            Ast::Return(None) => {
                self.indent();
                self.emit("return;\n");
            }
            Ast::While { condition, body } => {
                self.indent();
                self.emit("while (");
                self.gen_expression(condition);
                self.emit(")\n");
                self.gen_expression(body);
                self.emit("\n");
            }
            Ast::For { var, iter, body } => {
                self.indent();
                self.emit(&format!("for (auto {} : ", var));
                self.gen_expression(iter);
                self.emit(")\n");
                self.gen_expression(body);
                self.emit("\n");
            }
            Ast::Loop(body) => {
                self.indent();
                self.emit("while (1)\n");
                self.gen_expression(body);
                self.emit("\n");
            }
            Ast::Break => {
                self.indent();
                self.emit("break;\n");
            }
            Ast::Continue => {
                self.indent();
                self.emit("continue;\n");
            }
            _ => {}
        }
    }

    fn gen_expression(&mut self, expr: &Spanned<Ast>) {
        match &expr.value {
            Ast::Literal(lit) => {
                match lit {
                    Literal::Integer(n) => self.emit(&format!("{}", n)),
                    Literal::Float(n) => self.emit(&format!("{}", n)),
                    Literal::String(s) => {
                        self.emit(&format!("\"{}\"", s.replace('"', "\\\"")))
                    }
                    Literal::Bool(b) => self.emit(if *b { "true" } else { "false" }),
                    Literal::Char(c) => self.emit(&format!("'{}'", c)),
                    Literal::Null => self.emit("NULL"),
                }
            }
            Ast::Ident(name) => {
                self.emit(name.as_str());
            }
            Ast::BinaryOp { op, left, right } => {
                self.emit("(");
                self.gen_expression(left);
                self.emit(&format!(" {} ", self.op_to_c(&op)));
                self.gen_expression(right);
                self.emit(")");
            }
            Ast::UnaryOp { op, expr } => {
                let op_str = match op {
                    UnaryOp::Neg => "-",
                    UnaryOp::Not => "!",
                    UnaryOp::BitNot => "~",
                };
                self.emit(op_str);
                self.gen_expression(expr);
            }
            Ast::Call { func, args } => {
                self.gen_expression(func);
                self.emit("(");
                for (i, arg) in args.iter().enumerate() {
                    if i > 0 {
                        self.emit(", ");
                    }
                    self.gen_expression(arg);
                }
                self.emit(")");
            }
            Ast::If { condition, then_branch, else_branch } => {
                self.emit("(");
                self.gen_expression(condition);
                self.emit(" ? ");
                self.gen_expression(then_branch);
                if let Some(else_expr) = else_branch {
                    self.emit(" : ");
                    self.gen_expression(else_expr);
                } else {
                    self.emit(" : NULL");
                }
                self.emit(")");
            }
            Ast::Block(stmts) => {
                self.emit("{\n");
                self.indent += 1;
                for stmt in stmts {
                    self.gen_statement(stmt);
                }
                self.indent -= 1;
                self.indent();
                self.emit("}");
            }
            Ast::Lambda { params, body } => {
                self.emit("(");
                for (i, param) in params.iter().enumerate() {
                    if i > 0 {
                        self.emit(", ");
                    }
                    if let Some(ty) = &param.ty {
                        self.emit(&self.type_to_c(ty));
                    } else {
                        self.emit("auto");
                    }
                    self.emit(&format!(" {}", param.name));
                }
                self.emit(") => ");
                self.gen_expression(body);
            }
            _ => {}
        }
    }

    fn type_to_c(&self, ty: &TypeAnnotation) -> String {
        match ty {
            TypeAnnotation::Simple(name) => match name.as_str() {
                "Int" | "int" => "int".to_string(),
                "Float" | "float" => "double".to_string(),
                "String" | "string" => "const char*".to_string(),
                "Bool" | "bool" => "bool".to_string(),
                "Char" | "char" => "char".to_string(),
                "Void" | "void" => "void".to_string(),
                _ => name.clone(),
            },
            TypeAnnotation::Array(inner) => {
                format!("{}*", self.type_to_c(inner))
            }
            TypeAnnotation::Function { params, return_type } => {
                let param_str: Vec<String> = params.iter()
                    .map(|t| self.type_to_c(t))
                    .collect();
                format!("{} (*)({})", self.type_to_c(return_type), param_str.join(", "))
            }
            TypeAnnotation::Nullable(inner) => {
                format!("{}*", self.type_to_c(inner))
            }
            TypeAnnotation::Tuple(_) => "void*".to_string(),
            TypeAnnotation::Generic { name, .. } => name.clone(),
        }
    }

    fn op_to_c(&self, op: &BinOp) -> &str {
        match op {
            BinOp::Add => "+",
            BinOp::Sub => "-",
            BinOp::Mul => "*",
            BinOp::Div => "/",
            BinOp::Mod => "%",
            BinOp::Eq => "==",
            BinOp::Ne => "!=",
            BinOp::Lt => "<",
            BinOp::Gt => ">",
            BinOp::Le => "<=",
            BinOp::Ge => ">=",
            BinOp::And => "&&",
            BinOp::Or => "||",
            BinOp::BitAnd => "&",
            BinOp::BitOr => "|",
            BinOp::BitXor => "^",
            BinOp::Shl => "<<",
            BinOp::Shr => ">>",
            BinOp::Pow => "//",
        }
    }

    #[allow(dead_code)]
    fn unary_op_to_c(&self, op: &UnaryOp) -> &str {
        match op {
            UnaryOp::Neg => "-",
            UnaryOp::Not => "!",
            UnaryOp::BitNot => "~",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;
    use crate::parser::Parser;

    #[test]
    fn test_codegen_let() {
        let mut lexer = Lexer::new("let x = 42;");
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();

        let mut codegen = CodeGen::new();
        let output = codegen.generate(&ast);
        assert!(output.contains("x = 42"));
    }
}
