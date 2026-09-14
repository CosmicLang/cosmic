use crate::ast::*;
use crate::bytecode::chunk::{Chunk, Value};
use crate::bytecode::opcodes::Opcode;
use crate::lexer::Spanned;
use std::collections::HashMap;

struct Local {
    name: String,
    depth: usize,
    slot: u16,
}

struct LoopCtx {
    start: usize,
    breaks: Vec<usize>,
}

pub struct BytecodeCompiler {
    chunk: Chunk,
    locals: Vec<Local>,
    scope_depth: usize,
    globals: HashMap<String, u16>,
    functions: HashMap<String, (usize, u8)>,
    chunks: Vec<Chunk>,
    loop_stack: Vec<LoopCtx>,
}



impl BytecodeCompiler {
    pub fn new() -> Self {
        BytecodeCompiler {
            chunk: Chunk::new("<main>"),
            locals: Vec::new(),
            scope_depth: 0,
            globals: HashMap::new(),
            functions: HashMap::new(),
            chunks: Vec::new(),
            loop_stack: Vec::new(),
        }
    }

    pub fn compile(&mut self, program: &[Spanned<Ast>]) -> Result<Vec<Chunk>, String> {
        // Pass 1: collect function signatures
        for stmt in program {
            if let Ast::Function { name, params, .. } = &stmt.value {
                let idx = self.chunks.len();
                let arity = params.len() as u8;
                self.functions.insert(name.clone(), (idx, arity));
                self.chunks.push(Chunk::new(&format!("<fn {}>", name)));
            }
        }

        // Pass 2: compile function bodies
        let fn_info: Vec<(String, usize, u8)> = self.functions.iter()
            .map(|(n, &(i, a))| (n.clone(), i, a))
            .collect();

        for (name, idx, _arity) in &fn_info {
            for stmt in program {
                if let Ast::Function { name: fn_name, params, body, .. } = &stmt.value {
                    if fn_name == name {
                        let old = std::mem::replace(&mut self.chunk, self.chunks[*idx].clone());
                        let old_locals = std::mem::take(&mut self.locals);
                        let old_globals = std::mem::replace(&mut self.globals, HashMap::new());
                        let old_depth = self.scope_depth;

                        self.scope_depth = 1;
                        for (i, param) in params.iter().enumerate() {
                            self.locals.push(Local { name: param.name.clone(), depth: 1, slot: i as u16 });
                        }
                        self.compile_expression(body)?;
                        self.emit(Opcode::Return, 0);

                        self.chunks[*idx] = std::mem::replace(&mut self.chunk, old);
                        self.locals = old_locals;
                        self.globals = old_globals;
                        self.scope_depth = old_depth;
                        break;
                    }
                }
            }
        }

        // Pass 3: compile main
        self.scope_depth = 0;
        let len = program.len();
        for (i, stmt) in program.iter().enumerate() {
            if i == len - 1 {
                // Last statement: keep value on stack for return
                self.compile_statement_last(stmt)?;
            } else {
                self.compile_statement(stmt)?;
            }
        }
        self.emit(Opcode::Return, 0);

        let main = std::mem::replace(&mut self.chunk, Chunk::new("<main>"));
        let _main_idx = self.chunks.len();
        self.chunks.push(main);

        Ok(std::mem::take(&mut self.chunks))
    }

    fn emit(&mut self, opcode: Opcode, line: u16) -> usize {
        self.chunk.emit(opcode, line)
    }

    fn emit_constant(&mut self, value: Value, line: u16) {
        let idx = self.chunk.add_constant(value);
        self.emit(Opcode::Const(idx), line);
    }

    fn begin_scope(&mut self) { self.scope_depth += 1; }

    fn end_scope(&mut self, line: u16) {
        let depth = self.scope_depth;
        self.scope_depth = depth - 1;
        while let Some(local) = self.locals.last() {
            if local.depth > self.scope_depth {
                self.emit(Opcode::Pop, line);
                self.locals.pop();
            } else { break; }
        }
    }

    fn declare_local(&mut self, name: &str, line: u16) -> Result<u16, String> {
        for local in self.locals.iter().rev() {
            if local.depth == self.scope_depth {
                if local.name == name {
                    return Err(format!("Variable '{}' already declared at line {}", name, line));
                }
            } else { break; }
        }
        let slot = self.locals.len() as u16;
        self.locals.push(Local { name: name.to_string(), depth: self.scope_depth, slot });
        Ok(slot)
    }

    fn resolve_local(&self, name: &str) -> Option<u16> {
        self.locals.iter().rev().find(|l| l.name == name).map(|l| l.slot)
    }

    fn patch_jump(&mut self, offset: usize) {
        let jump = (self.chunk.code.len() - offset - 3) as u16;
        self.chunk.code[offset + 1] = (jump & 0xFF) as u8;
        self.chunk.code[offset + 2] = ((jump >> 8) & 0xFF) as u8;
    }

    fn patch_jump_to(&mut self, offset: usize, target: usize) {
        let jump = (target - offset - 3) as u16;
        self.chunk.code[offset + 1] = (jump & 0xFF) as u8;
        self.chunk.code[offset + 2] = ((jump >> 8) & 0xFF) as u8;
    }

    fn compile_statement_last(&mut self, stmt: &Spanned<Ast>) -> Result<(), String> {
        // Like compile_statement but doesn't pop the last expression value
        let _line = stmt.line as u16;
        match &stmt.value {
            Ast::Expr(expr) => {
                self.compile_expression(expr)?;
                Ok(())
            }
            _ => self.compile_statement(stmt),
        }
    }

    fn compile_statement(&mut self, stmt: &Spanned<Ast>) -> Result<(), String> {
        let line = stmt.line as u16;
        match &stmt.value {
            Ast::Let { name, value, .. } => {
                if self.scope_depth > 0 {
                    let slot = self.declare_local(name, line)?;
                    if let Some(val) = value {
                        self.compile_expression(val)?;
                    } else {
                        self.emit(Opcode::Nil, line);
                    }
                    self.emit(Opcode::SetLocal(slot), line);
                    self.emit(Opcode::Pop, line);
                } else {
                    let name_idx = self.chunk.add_constant(Value::Str(name.clone()));
                    if let Some(val) = value {
                        self.compile_expression(val)?;
                    } else {
                        self.emit(Opcode::Nil, line);
                    }
                    self.emit(Opcode::DefineGlobal(name_idx), line);
                }
                Ok(())
            }
            Ast::Function { name, params, body, .. } => {
                if self.scope_depth == 0 {
                    let name_idx = self.chunk.add_constant(Value::Str(name.clone()));
                    if let Some(&(idx, arity)) = self.functions.get(name) {
                        self.emit_constant(Value::Func(idx, arity, 0), line);
                        self.emit(Opcode::DefineGlobal(name_idx), line);
                    }
                } else {
                    // Local function - compile inline as lambda
                    let _name_idx = self.chunk.add_constant(Value::Str(name.clone()));
                    let func_idx = self.chunks.len();
                    let arity = params.len() as u8;
                    self.functions.insert(name.clone(), (func_idx, arity));
                    self.chunks.push(Chunk::new(&format!("<fn {}>", name)));

                    let old = std::mem::replace(&mut self.chunk, self.chunks[func_idx].clone());
                    let old_locals = std::mem::take(&mut self.locals);
                    let old_depth = self.scope_depth;

                    self.scope_depth = 1;
                    for (i, p) in params.iter().enumerate() {
                        self.locals.push(Local { name: p.name.clone(), depth: 1, slot: i as u16 });
                    }
                    self.compile_expression(body)?;
                    self.emit(Opcode::Return, 0);

                    self.chunks[func_idx] = std::mem::replace(&mut self.chunk, old);
                    self.locals = old_locals;
                    self.scope_depth = old_depth;

                    let slot = self.declare_local(name, line)?;
                    self.emit_constant(Value::Func(func_idx, arity, 0), line);
                    self.emit(Opcode::SetLocal(slot), line);
                    self.emit(Opcode::Pop, line);
                }
                Ok(())
            }
            Ast::Struct { name, fields, .. } => {
                if self.scope_depth == 0 {
                    let name_idx = self.chunk.add_constant(Value::Str(name.clone()));
                    let field_names: Vec<(String, Value)> = fields.iter()
                        .map(|f| (f.name.clone(), Value::Nil))
                        .collect();
                    self.emit_constant(Value::Instance(0, field_names), line);
                    self.emit(Opcode::DefineGlobal(name_idx), line);
                }
                Ok(())
            }
            Ast::Enum { .. } => Ok(()),
            Ast::Return(Some(expr)) => {
                self.compile_expression(expr)?;
                self.emit(Opcode::Return, line);
                Ok(())
            }
            Ast::Return(None) => {
                self.emit(Opcode::Nil, line);
                self.emit(Opcode::Return, line);
                Ok(())
            }
            Ast::Expr(expr) => {
                self.compile_expression(expr)?;
                self.emit(Opcode::Pop, line);
                Ok(())
            }
            Ast::Assign { target, value } => {
                self.compile_expression(value)?;
                match &target.value {
                    Ast::Ident(name) => {
                        if let Some(slot) = self.resolve_local(name) {
                            self.emit(Opcode::SetLocal(slot), line);
                            self.emit(Opcode::Pop, line);
                        } else {
                            let name_idx = self.chunk.add_constant(Value::Str(name.clone()));
                            self.globals.insert(name.clone(), name_idx);
                            self.emit(Opcode::SetGlobal(name_idx), line);
                            self.emit(Opcode::Pop, line);
                        }
                    }
                    Ast::Index { object, index } => {
                        self.compile_expression(object)?;
                        self.compile_expression(index)?;
                        self.emit(Opcode::SetIndex, line);
                    }
                    _ => return Err(format!("Invalid assignment target at line {}", line)),
                }
                Ok(())
            }
            Ast::While { condition, body } => {
                let loop_start = self.chunk.code.len();
                self.compile_expression(condition)?;
                let exit_jump = self.emit(Opcode::JumpIfFalse(0), line);
                self.emit(Opcode::Pop, line);
                self.loop_stack.push(LoopCtx { start: loop_start, breaks: Vec::new() });
                self.compile_expression(body)?;
                self.emit(Opcode::Pop, line);
                let back = (self.chunk.code.len() - loop_start + 3) as u16;
                self.emit(Opcode::Loop(back), line);
                let loop_ctx = self.loop_stack.pop().unwrap();
                self.patch_jump(exit_jump);
                self.emit(Opcode::Pop, line);
                self.emit(Opcode::Nil, line);
                for break_offset in &loop_ctx.breaks {
                    self.patch_jump(*break_offset);
                }
                Ok(())
            }
            Ast::For { var, iter, body } => {
                // Desugar for x in iter { body } into:
                //   let __iter = iter;
                //   let __idx = 0;
                //   while __idx < ArrayLen(__iter) {
                //       let x = __iter[__idx];
                //       body;
                //       __idx += 1;
                //   }
                // Use global variables to avoid main-frame stack slot issues.

                // __iter = iter
                self.compile_expression(iter)?;
                let iter_name_idx = self.chunk.add_constant(Value::Str("__iter_for".into()));
                self.emit(Opcode::DefineGlobal(iter_name_idx), line);

                // __idx = 0
                let zero_idx = self.chunk.add_constant(Value::Int(0));
                self.emit(Opcode::Const(zero_idx), line);
                let idx_name_idx = self.chunk.add_constant(Value::Str("__idx_for".into()));
                self.emit(Opcode::DefineGlobal(idx_name_idx), line);

                let loop_start = self.chunk.code.len();

                // while __idx < ArrayLen(__iter)
                let idx_g1 = self.chunk.add_constant(Value::Str("__idx_for".into()));
                self.emit(Opcode::GetGlobal(idx_g1), line);
                let iter_g1 = self.chunk.add_constant(Value::Str("__iter_for".into()));
                self.emit(Opcode::GetGlobal(iter_g1), line);
                self.emit(Opcode::ArrayLen, line);
                self.emit(Opcode::Lt, line);
                let exit_jump = self.emit(Opcode::JumpIfFalse(0), line);
                self.emit(Opcode::Pop, line);

                // x = __iter[__idx]
                let iter_g2 = self.chunk.add_constant(Value::Str("__iter_for".into()));
                self.emit(Opcode::GetGlobal(iter_g2), line);
                let idx_g2 = self.chunk.add_constant(Value::Str("__idx_for".into()));
                self.emit(Opcode::GetGlobal(idx_g2), line);
                self.emit(Opcode::GetIndex, line);
                let var_name_idx = self.chunk.add_constant(Value::Str(var.clone()));
                self.emit(Opcode::DefineGlobal(var_name_idx), line);

                // body
                self.loop_stack.push(LoopCtx { start: loop_start, breaks: Vec::new() });
                self.compile_expression(body)?;
                self.emit(Opcode::Pop, line);

                // __idx += 1
                let idx_g3 = self.chunk.add_constant(Value::Str("__idx_for".into()));
                self.emit(Opcode::GetGlobal(idx_g3), line);
                let one_idx = self.chunk.add_constant(Value::Int(1));
                self.emit(Opcode::Const(one_idx), line);
                self.emit(Opcode::Add, line);
                let idx_g4 = self.chunk.add_constant(Value::Str("__idx_for".into()));
                self.emit(Opcode::SetGlobal(idx_g4), line);
                self.emit(Opcode::Pop, line);

                let back = (self.chunk.code.len() - loop_start + 3) as u16;
                self.emit(Opcode::Loop(back), line);
                let loop_ctx = self.loop_stack.pop().unwrap();
                self.patch_jump(exit_jump);
                self.emit(Opcode::Pop, line);
                self.emit(Opcode::Nil, line);
                for break_offset in &loop_ctx.breaks {
                    self.patch_jump(*break_offset);
                }
                Ok(())
            }
            Ast::Block(stmts) => {
                self.begin_scope();
                for s in stmts { self.compile_statement(s)?; }
                self.end_scope(line);
                Ok(())
            }
            Ast::Break => {
                if self.loop_stack.last().is_some() {
                    let jump = self.emit(Opcode::Jump(0), line);
                    self.loop_stack.last_mut().unwrap().breaks.push(jump);
                } else {
                    return Err(format!("'break' outside loop at line {}", line));
                }
                Ok(())
            }
            Ast::Continue => {
                if let Some(loop_ctx) = self.loop_stack.last() {
                    let back = (self.chunk.code.len() - loop_ctx.start + 3) as u16;
                    self.emit(Opcode::Loop(back), line);
                } else {
                    return Err(format!("'continue' outside loop at line {}", line));
                }
                Ok(())
            }
            Ast::Import { .. } => Ok(()),
            _ => {
                self.compile_expression(stmt)?;
                self.emit(Opcode::Pop, line);
                Ok(())
            }
        }
    }

    fn compile_expression(&mut self, expr: &Spanned<Ast>) -> Result<(), String> {
        let line = expr.line as u16;
        match &expr.value {
            Ast::Literal(lit) => {
                match lit {
                    Literal::Integer(n) => { self.emit_constant(Value::Int(*n), line); }
                    Literal::Float(n) => { self.emit_constant(Value::Float(*n), line); }
                    Literal::String(s) => { self.emit_constant(Value::Str(s.clone()), line); }
                    Literal::Bool(b) => {
                        if *b { self.emit(Opcode::True, line); }
                        else { self.emit(Opcode::False, line); }
                    }
                    Literal::Char(c) => { self.emit_constant(Value::Str(c.to_string()), line); }
                    Literal::Null => { self.emit(Opcode::Nil, line); }
                }
                Ok(())
            }
            Ast::Ident(name) => {
                if let Some(slot) = self.resolve_local(name) {
                    self.emit(Opcode::GetLocal(slot), line);
                } else if let Some(&name_idx) = self.globals.get(name) {
                    self.emit(Opcode::GetGlobal(name_idx), line);
                } else {
                    let name_idx = self.chunk.add_constant(Value::Str(name.clone()));
                    self.globals.insert(name.clone(), name_idx);
                    self.emit(Opcode::GetGlobal(name_idx), line);
                }
                Ok(())
            }
            Ast::BinaryOp { op, left, right } => {
                match op {
                    BinOp::And => {
                        self.compile_expression(left)?;
                        let false_jump = self.emit(Opcode::JumpIfFalse(0), line);
                        self.emit(Opcode::Pop, line);
                        self.compile_expression(right)?;
                        self.patch_jump(false_jump);
                        return Ok(());
                    }
                    BinOp::Or => {
                        self.compile_expression(left)?;
                        let true_jump = self.emit(Opcode::JumpIfTrue(0), line);
                        self.emit(Opcode::Pop, line);
                        self.compile_expression(right)?;
                        self.patch_jump(true_jump);
                        return Ok(());
                    }
                    _ => {}
                }
                self.compile_expression(left)?;
                self.compile_expression(right)?;
                match op {
                    BinOp::Add => self.emit(Opcode::Add, line),
                    BinOp::Sub => self.emit(Opcode::Sub, line),
                    BinOp::Mul => self.emit(Opcode::Mul, line),
                    BinOp::Div => self.emit(Opcode::Div, line),
                    BinOp::Mod => self.emit(Opcode::Mod, line),
                    BinOp::Pow => self.emit(Opcode::Pow, line),
                    BinOp::Eq => self.emit(Opcode::Eq, line),
                    BinOp::Ne => self.emit(Opcode::Ne, line),
                    BinOp::Gt => self.emit(Opcode::Gt, line),
                    BinOp::Ge => self.emit(Opcode::Ge, line),
                    BinOp::Lt => self.emit(Opcode::Lt, line),
                    BinOp::Le => self.emit(Opcode::Le, line),
                    BinOp::BitAnd => self.emit(Opcode::BitAnd, line),
                    BinOp::BitOr => self.emit(Opcode::BitOr, line),
                    BinOp::BitXor => self.emit(Opcode::BitXor, line),
                    BinOp::Shl => self.emit(Opcode::Shl, line),
                    BinOp::Shr => self.emit(Opcode::Shr, line),
                    _ => unreachable!(),
                };
                Ok(())
            }
            Ast::UnaryOp { op, expr } => {
                self.compile_expression(expr)?;
                match op {
                    UnaryOp::Neg => self.emit(Opcode::Neg, line),
                    UnaryOp::Not => self.emit(Opcode::Not, line),
                    UnaryOp::BitNot => self.emit(Opcode::BitNot, line),
                };
                Ok(())
            }
            Ast::Call { func, args } => {
                self.compile_expression(func)?;
                for arg in args { self.compile_expression(arg)?; }
                self.emit(Opcode::Call(args.len() as u8), line);
                Ok(())
            }
            Ast::If { condition, then_branch, else_branch } => {
                self.compile_expression(condition)?;
                let then_jump = self.emit(Opcode::JumpIfFalse(0), line);
                self.emit(Opcode::Pop, line);
                self.compile_expression(then_branch)?;
                if let Some(else_expr) = else_branch {
                    let end_jump = self.emit(Opcode::Jump(0), line);
                    self.patch_jump(then_jump);
                    self.emit(Opcode::Pop, line);
                    self.compile_expression(else_expr)?;
                    self.patch_jump(end_jump);
                } else {
                    self.patch_jump(then_jump);
                    self.emit(Opcode::Pop, line);
                    self.emit(Opcode::Nil, line);
                }
                Ok(())
            }
            Ast::Match { expr, arms } => {
                self.compile_expression(expr)?;
                let match_val_idx = self.chunk.add_constant(Value::Str("__match_val".into()));
                self.emit(Opcode::DefineGlobal(match_val_idx), line);

                let mut then_jumps: Vec<usize> = Vec::new();

                for (i, arm) in arms.iter().enumerate() {
                    match &arm.pattern {
                        Pattern::Wildcard => {
                            // Wildcard: pop any leftover condition, compile body
                            self.emit(Opcode::Pop, line);
                            self.compile_expression(&arm.body)?;
                        }
                        Pattern::Literal(lit) => {
                            let mv_g = self.chunk.add_constant(Value::Str("__match_val".into()));
                            self.emit(Opcode::GetGlobal(mv_g), line);
                            match lit {
                                Literal::Integer(n) => { self.emit_constant(Value::Int(*n), line); }
                                Literal::Float(f) => { self.emit_constant(Value::Float(*f), line); }
                                Literal::String(s) => { self.emit_constant(Value::Str(s.clone()), line); }
                                Literal::Bool(b) => {
                                    if *b { self.emit(Opcode::True, line); }
                                    else { self.emit(Opcode::False, line); }
                                }
                                Literal::Char(c) => { self.emit_constant(Value::Str(c.to_string()), line); }
                                Literal::Null => { self.emit(Opcode::Nil, line); }
                            }
                            self.emit(Opcode::Eq, line);
                            let then_jump = self.emit(Opcode::JumpIfFalse(0), line);
                            // Pattern matched: pop true, compile body, jump to end
                            self.emit(Opcode::Pop, line);
                            self.compile_expression(&arm.body)?;
                            let end_jump = self.emit(Opcode::Jump(0), line);
                            then_jumps.push(end_jump);
                            // Patch JumpIfFalse to here (next arm's test)
                            self.patch_jump(then_jump);
                        }
                        _ => {
                            return Err(format!("Unsupported match pattern at line {}", line));
                        }
                    }
                }

                // If no wildcard, all conditions fell through — pop the last false, push nil
                if !arms.iter().any(|a| matches!(a.pattern, Pattern::Wildcard)) {
                    self.emit(Opcode::Pop, line);
                    self.emit(Opcode::Nil, line);
                }

                // Patch all end_jumps to here
                let end = self.chunk.code.len();
                for &jump in &then_jumps {
                    self.patch_jump_to(jump, end);
                }
                Ok(())
            }
            Ast::Block(stmts) => {
                self.begin_scope();
                let slen = stmts.len();
                for (i, s) in stmts.iter().enumerate() {
                    if i == slen - 1 {
                        self.compile_statement_last(s)?;
                    } else {
                        self.compile_statement(s)?;
                    }
                }
                self.end_scope(line);
                Ok(())
            }
            Ast::Array(elements) => {
                let len = elements.len() as u16;
                for elem in elements {
                    self.compile_expression(elem)?;
                }
                self.emit(Opcode::NewArray(len), line);
                Ok(())
            }
            Ast::Lambda { params, body } => {
                let func_idx = self.chunks.len();
                let argc = params.len() as u8;
                self.chunks.push(Chunk::new("<lambda>"));

                let old = std::mem::replace(&mut self.chunk, self.chunks[func_idx].clone());
                let old_locals = std::mem::take(&mut self.locals);
                let old_depth = self.scope_depth;

                self.scope_depth = 1;
                for (i, p) in params.iter().enumerate() {
                    self.locals.push(Local { name: p.name.clone(), depth: 1, slot: i as u16 });
                }
                self.compile_expression(body)?;
                self.emit(Opcode::Return, 0);

                self.chunks[func_idx] = std::mem::replace(&mut self.chunk, old);
                self.locals = old_locals;
                self.scope_depth = old_depth;

                self.emit_constant(Value::Func(func_idx, argc, 0), line);
                Ok(())
            }
            Ast::Index { object, index } => {
                self.compile_expression(object)?;
                self.compile_expression(index)?;
                self.emit(Opcode::GetIndex, line);
                Ok(())
            }
            Ast::FieldAccess { object, field } => {
                self.compile_expression(object)?;
                let field_idx = self.chunk.add_constant(Value::Str(field.clone()));
                self.emit(Opcode::GetField(field_idx), line);
                Ok(())
            }
            Ast::Loop(body) => {
                let loop_start = self.chunk.code.len();
                self.loop_stack.push(LoopCtx { start: loop_start, breaks: Vec::new() });
                self.compile_expression(body)?;
                self.emit(Opcode::Pop, line);
                let back = (self.chunk.code.len() - loop_start + 3) as u16;
                self.emit(Opcode::Loop(back), line);
                let loop_ctx = self.loop_stack.pop().unwrap();
                for break_offset in &loop_ctx.breaks {
                    self.patch_jump(*break_offset);
                }
                self.emit(Opcode::Nil, line);
                Ok(())
            }
            _ => {
                Err(format!("Unsupported expression at line {}: {:?}", line, std::mem::discriminant(&expr.value)))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;
    use crate::parser::Parser;

    fn compile_source(source: &str) -> Vec<Chunk> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();
        let mut compiler = BytecodeCompiler::new();
        compiler.compile(&ast).unwrap()
    }

    #[test]
    fn test_compile_literal() {
        let chunks = compile_source("42;");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_arithmetic() {
        let chunks = compile_source("2 + 3;");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_variable() {
        let chunks = compile_source("let x = 10;");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_if() {
        let chunks = compile_source("if true { 1; }");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_while() {
        let chunks = compile_source("while true { break; }");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_function() {
        let chunks = compile_source("fn add(a, b) { return a + b; }");
        assert!(chunks.len() >= 2);
    }

    #[test]
    fn test_compile_comparison() {
        let chunks = compile_source("5 > 3;");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_logical() {
        let chunks = compile_source("true && false || true");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_negation() {
        let chunks = compile_source("-42;");
        assert!(chunks[0].code.len() > 0);
    }

    #[test]
    fn test_compile_string() {
        let chunks = compile_source(r#""hello";"#);
        assert!(chunks[0].code.len() > 0);
    }
}
