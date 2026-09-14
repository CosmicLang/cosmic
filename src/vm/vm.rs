use crate::bytecode::chunk::{Chunk, Value};
use crate::bytecode::opcodes::Opcode;
use std::collections::HashMap;

const STACK_MAX: usize = 256;
const CALL_MAX: usize = 64;

/// Runtime error with location info.
#[derive(Debug, Clone)]
pub struct RuntimeError {
    pub message: String,
    pub chunk_source: String,
    pub offset: usize,
}

impl std::fmt::Display for RuntimeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Runtime error at {} offset {}: {}", self.chunk_source, self.offset, self.message)
    }
}

impl std::error::Error for RuntimeError {}

/// Call frame for function invocation.
struct CallFrame {
    /// Index into the chunks array
    chunk_idx: usize,
    /// Instruction pointer within the chunk
    ip: usize,
    /// Base pointer into the stack (where args start)
    base: usize,
}

/// The Cosmic Virtual Machine.
pub struct Vm {
    /// Value stack
    stack: Vec<Value>,
    /// Global variables
    globals: HashMap<String, Value>,
    /// Call frames (call stack)
    frames: Vec<CallFrame>,
    /// All compiled chunks
    chunks: Vec<Chunk>,
    /// Output buffer (for testing / captured output)
    output: String,
    /// Native function registry
    natives: HashMap<String, Value>,
}

impl Vm {
    pub fn new() -> Self {
        let mut vm = Vm {
            stack: Vec::with_capacity(STACK_MAX),
            globals: HashMap::new(),
            frames: Vec::with_capacity(CALL_MAX),
            chunks: Vec::new(),
            output: String::new(),
            natives: HashMap::new(),
        };
        vm.register_natives();
        vm
    }

    fn register_natives(&mut self) {
        self.natives.insert("println".into(), Value::NativeFn(|args| {
            let msg: String = args.iter().map(|a| a.to_string_value()).collect::<Vec<_>>().join(" ");
            println!("{}", msg);
            Value::Nil
        }));
        self.natives.insert("print".into(), Value::NativeFn(|args| {
            let msg: String = args.iter().map(|a| a.to_string_value()).collect::<Vec<_>>().join(" ");
            print!("{}", msg);
            Value::Nil
        }));
    }

    /// Load chunks into the VM.
    pub fn load(&mut self, chunks: Vec<Chunk>) {
        self.chunks = chunks;
    }

    /// Run the main chunk (last chunk).
    pub fn run(&mut self) -> Result<Value, RuntimeError> {
        if self.chunks.is_empty() {
            return Err(RuntimeError {
                message: "No code loaded".into(),
                chunk_source: "<none>".into(),
                offset: 0,
            });
        }

        let main_idx = self.chunks.len() - 1;
        self.frames.push(CallFrame {
            chunk_idx: main_idx,
            ip: 0,
            base: 0,
        });

        self.execute()
    }

    /// Main execution loop.
    fn execute(&mut self) -> Result<Value, RuntimeError> {
        loop {
            if self.frames.is_empty() {
                break;
            }

            let frame = self.frames.last().unwrap();
            let chunk_idx = frame.chunk_idx;
            let ip = frame.ip;
            let base = frame.base;

            if ip >= self.chunks[chunk_idx].code.len() {
                break;
            }

            let (opcode, size) = self.chunks[chunk_idx].read_opcode(ip);

            // Advance IP
            self.frames.last_mut().unwrap().ip += size;

            match opcode {
                // === Constants ===
                Opcode::Const(idx) => {
                    let val = self.chunks[chunk_idx].get_constant(idx).clone();
                    self.stack.push(val);
                }
                Opcode::Nil => self.stack.push(Value::Nil),
                Opcode::True => self.stack.push(Value::Bool(true)),
                Opcode::False => self.stack.push(Value::Bool(false)),

                // === Local variables ===
                Opcode::GetLocal(slot) => {
                    let val = self.stack[base + 1 + slot as usize].clone();
                    self.stack.push(val);
                }
                Opcode::SetLocal(slot) => {
                    let val = self.stack.last().unwrap().clone();
                    self.stack[base + 1 + slot as usize] = val;
                }

                // === Global variables ===
                Opcode::DefineGlobal(idx) => {
                    let name = match self.chunks[chunk_idx].get_constant(idx) {
                        Value::Str(s) => s.clone(),
                        _ => return self.error(chunk_idx, ip, "Global name must be a string"),
                    };
                    let val = self.stack.pop().unwrap();
                    self.globals.insert(name, val);
                }
                Opcode::GetGlobal(idx) => {
                    let name = match self.chunks[chunk_idx].get_constant(idx) {
                        Value::Str(s) => s.clone(),
                        _ => return self.error(chunk_idx, ip, "Global name must be a string"),
                    };
                    let val = match self.globals.get(&name) {
                        Some(v) => v.clone(),
                        None => {
                            // Check if it's a native function
                            match self.natives.get(&name) {
                                Some(v) => v.clone(),
                                None => {
                                    return self.error(chunk_idx, ip, &format!("Undefined variable '{}'", name));
                                }
                            }
                        }
                    };
                    self.stack.push(val);
                }
                Opcode::SetGlobal(idx) => {
                    let name = match self.chunks[chunk_idx].get_constant(idx) {
                        Value::Str(s) => s.clone(),
                        _ => return self.error(chunk_idx, ip, "Global name must be a string"),
                    };
                    let val = self.stack.last().unwrap().clone();
                    self.globals.insert(name, val);
                }

                // === Upvalues ===
                Opcode::GetUpvalue(_idx) => {
                    // TODO: implement upvalues
                    self.stack.push(Value::Nil);
                }
                Opcode::SetUpvalue(_idx) => {
                    // TODO: implement upvalues
                }
                Opcode::CloseUpvalue(_idx) => {
                    // TODO: implement upvalues
                }

                // === Arithmetic ===
                Opcode::Add => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => Value::Int(a + b),
                        (Value::Float(a), Value::Float(b)) => Value::Float(a + b),
                        (Value::Int(a), Value::Float(b)) => Value::Float(*a as f64 + b),
                        (Value::Float(a), Value::Int(b)) => Value::Float(a + *b as f64),
                        (Value::Str(a), Value::Str(b)) => Value::Str(format!("{}{}", a, b)),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot add {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(result);
                }
                Opcode::Sub => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => Value::Int(a - b),
                        (Value::Float(a), Value::Float(b)) => Value::Float(a - b),
                        (Value::Int(a), Value::Float(b)) => Value::Float(*a as f64 - b),
                        (Value::Float(a), Value::Int(b)) => Value::Float(a - *b as f64),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot subtract {} from {}", right.type_name(), left.type_name())),
                    };
                    self.stack.push(result);
                }
                Opcode::Mul => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => Value::Int(a * b),
                        (Value::Float(a), Value::Float(b)) => Value::Float(a * b),
                        (Value::Int(a), Value::Float(b)) => Value::Float(*a as f64 * b),
                        (Value::Float(a), Value::Int(b)) => Value::Float(a * *b as f64),
                        (Value::Str(a), Value::Int(b)) => Value::Str(a.repeat(*b as usize)),
                        (Value::Int(a), Value::Str(b)) => Value::Str(b.repeat(*a as usize)),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot multiply {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(result);
                }
                Opcode::Div => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => {
                            if *b == 0 {
                                return self.error(chunk_idx, ip, "Division by zero");
                            }
                            Value::Int(a / b)
                        }
                        (Value::Float(a), Value::Float(b)) => Value::Float(a / b),
                        (Value::Int(a), Value::Float(b)) => Value::Float(*a as f64 / b),
                        (Value::Float(a), Value::Int(b)) => Value::Float(a / *b as f64),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot divide {} by {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(result);
                }
                Opcode::Mod => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => {
                            if *b == 0 {
                                return self.error(chunk_idx, ip, "Modulo by zero");
                            }
                            Value::Int(a % b)
                        }
                        _ => return self.error(chunk_idx, ip, &format!("Cannot modulo {} by {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(result);
                }
                Opcode::Pow => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => Value::Int(a.pow(*b as u32)),
                        (Value::Float(a), Value::Float(b)) => Value::Float(a.powf(*b)),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot exponentiate {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(result);
                }
                Opcode::Neg => {
                    let val = self.stack.pop().unwrap();
                    let result = match val {
                        Value::Int(n) => Value::Int(-n),
                        Value::Float(n) => Value::Float(-n),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot negate {}", val.type_name())),
                    };
                    self.stack.push(result);
                }

                // === Comparison ===
                Opcode::Eq => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    self.stack.push(Value::Bool(left == right));
                }
                Opcode::Ne => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    self.stack.push(Value::Bool(left != right));
                }
                Opcode::Gt => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => a > b,
                        (Value::Float(a), Value::Float(b)) => a > b,
                        (Value::Int(a), Value::Float(b)) => (*a as f64) > *b,
                        (Value::Float(a), Value::Int(b)) => *a > (*b as f64),
                        (Value::Str(a), Value::Str(b)) => a > b,
                        _ => return self.error(chunk_idx, ip, &format!("Cannot compare {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(Value::Bool(result));
                }
                Opcode::Ge => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => a >= b,
                        (Value::Float(a), Value::Float(b)) => a >= b,
                        (Value::Int(a), Value::Float(b)) => (*a as f64) >= *b,
                        (Value::Float(a), Value::Int(b)) => *a >= (*b as f64),
                        (Value::Str(a), Value::Str(b)) => a >= b,
                        _ => return self.error(chunk_idx, ip, &format!("Cannot compare {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(Value::Bool(result));
                }
                Opcode::Lt => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => a < b,
                        (Value::Float(a), Value::Float(b)) => a < b,
                        (Value::Int(a), Value::Float(b)) => (*a as f64) < *b,
                        (Value::Float(a), Value::Int(b)) => *a < (*b as f64),
                        (Value::Str(a), Value::Str(b)) => a < b,
                        _ => return self.error(chunk_idx, ip, &format!("Cannot compare {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(Value::Bool(result));
                }
                Opcode::Le => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => a <= b,
                        (Value::Float(a), Value::Float(b)) => a <= b,
                        (Value::Int(a), Value::Float(b)) => (*a as f64) <= *b,
                        (Value::Float(a), Value::Int(b)) => *a <= (*b as f64),
                        (Value::Str(a), Value::Str(b)) => a <= b,
                        _ => return self.error(chunk_idx, ip, &format!("Cannot compare {} and {}", left.type_name(), right.type_name())),
                    };
                    self.stack.push(Value::Bool(result));
                }

                // === Logical ===
                Opcode::Not => {
                    let val = self.stack.pop().unwrap();
                    self.stack.push(Value::Bool(!val.is_truthy()));
                }
                Opcode::And => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    self.stack.push(Value::Bool(left.is_truthy() && right.is_truthy()));
                }
                Opcode::Or => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    self.stack.push(Value::Bool(left.is_truthy() || right.is_truthy()));
                }

                // === Bitwise ===
                Opcode::BitAnd => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => self.stack.push(Value::Int(a & b)),
                        _ => return self.error(chunk_idx, ip, "Bitwise AND requires integers"),
                    }
                }
                Opcode::BitOr => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => self.stack.push(Value::Int(a | b)),
                        _ => return self.error(chunk_idx, ip, "Bitwise OR requires integers"),
                    }
                }
                Opcode::BitXor => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => self.stack.push(Value::Int(a ^ b)),
                        _ => return self.error(chunk_idx, ip, "Bitwise XOR requires integers"),
                    }
                }
                Opcode::Shl => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => self.stack.push(Value::Int(a << b)),
                        _ => return self.error(chunk_idx, ip, "Shift left requires integers"),
                    }
                }
                Opcode::Shr => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    match (&left, &right) {
                        (Value::Int(a), Value::Int(b)) => self.stack.push(Value::Int(a >> b)),
                        _ => return self.error(chunk_idx, ip, "Shift right requires integers"),
                    }
                }
                Opcode::BitNot => {
                    let val = self.stack.pop().unwrap();
                    match val {
                        Value::Int(n) => self.stack.push(Value::Int(!n)),
                        _ => return self.error(chunk_idx, ip, "Bitwise NOT requires integer"),
                    }
                }

                // === Control flow ===
                Opcode::Jump(offset) => {
                    self.frames.last_mut().unwrap().ip += offset as usize;
                }
                Opcode::JumpIfFalse(offset) => {
                    let val = self.stack.last().unwrap();
                    if !val.is_truthy() {
                        self.frames.last_mut().unwrap().ip += offset as usize;
                    }
                }
                Opcode::JumpIfTrue(offset) => {
                    let val = self.stack.last().unwrap();
                    if val.is_truthy() {
                        self.frames.last_mut().unwrap().ip += offset as usize;
                    }
                }
                Opcode::Loop(offset) => {
                    self.frames.last_mut().unwrap().ip -= offset as usize;
                }

                // === Functions ===
                Opcode::Call(argc) => {
                    let callee = self.stack[self.stack.len() - 1 - argc as usize].clone();
                    match callee {
                        Value::Func(func_idx, arity, _upvalues) => {
                            if argc != arity {
                                return self.error(chunk_idx, ip, &format!("Expected {} arguments, got {}", arity, argc));
                            }
                            let new_base = self.stack.len() - argc as usize - 1;
                            self.frames.push(CallFrame {
                                chunk_idx: func_idx,
                                ip: 0,
                                base: new_base,
                            });
                        }
                        Value::NativeFn(func) => {
                            let args: Vec<Value> = self.stack[self.stack.len() - argc as usize..].to_vec();
                            self.stack.truncate(self.stack.len() - argc as usize - 1);
                            let result = func(&args);
                            // Handle special native functions
                            self.handle_native_call(&args, &result, chunk_idx, ip)?;
                            self.stack.push(result);
                        }
                        _ => {
                            return self.error(chunk_idx, ip, &format!("Cannot call {}", callee.type_name()));
                        }
                    }
                }
                Opcode::NativeCall(argc) => {
                    let callee = self.stack[self.stack.len() - 1 - argc as usize].clone();
                    if let Value::NativeFn(func) = callee {
                        let args: Vec<Value> = self.stack[self.stack.len() - argc as usize..].to_vec();
                        self.stack.truncate(self.stack.len() - argc as usize - 1);
                        let result = func(&args);
                        self.handle_native_call(&args, &result, chunk_idx, ip)?;
                        self.stack.push(result);
                    } else {
                        return self.error(chunk_idx, ip, "Not a native function");
                    }
                }
                Opcode::Return => {
                    let result = self.stack.pop().unwrap();
                    let frame = self.frames.pop().unwrap();
                    self.stack.truncate(frame.base);
                    if self.frames.is_empty() {
                        return Ok(result.clone());
                    }
                    self.stack.push(result);
                }

                // === Closures ===
                Opcode::Closure(_func_idx) => {
                    // TODO: implement closure creation with upvalues
                    let val = self.stack.pop().unwrap();
                    self.stack.push(val);
                }

                // === Structs ===
                Opcode::NewStruct(field_count) => {
                    let mut fields: Vec<(String, Value)> = Vec::with_capacity(field_count as usize);
                    for _ in 0..field_count {
                        let val = self.stack.pop().unwrap();
                        fields.push((String::new(), val));
                    }
                    fields.reverse();
                    self.stack.push(Value::Instance(0, fields));
                }
                Opcode::GetField(idx) => {
                    let obj = self.stack.pop().unwrap();
                    let field_name = match self.chunks[chunk_idx].get_constant(idx) {
                        Value::Str(s) => s.clone(),
                        _ => return self.error(chunk_idx, ip, "Field name must be a string"),
                    };
                    match obj {
                        Value::Instance(_, fields) => {
                            if let Some((_, val)) = fields.iter().find(|(name, _)| name == &field_name) {
                                self.stack.push(val.clone());
                            } else {
                                self.stack.push(Value::Nil);
                            }
                        }
                        Value::Array(arr) => {
                            if let Ok(index) = field_name.parse::<usize>() {
                                if index < arr.len() {
                                    self.stack.push(arr[index].clone());
                                } else {
                                    self.stack.push(Value::Nil);
                                }
                            } else {
                                self.stack.push(Value::Nil);
                            }
                        }
                        _ => return self.error(chunk_idx, ip, &format!("Cannot access field on {}", obj.type_name())),
                    }
                }
                Opcode::SetField(idx) => {
                    let val = self.stack.pop().unwrap();
                    let mut obj = self.stack.pop().unwrap();
                    let field_name = match self.chunks[chunk_idx].get_constant(idx) {
                        Value::Str(s) => s.clone(),
                        _ => return self.error(chunk_idx, ip, "Field name must be a string"),
                    };
                    match &mut obj {
                        Value::Instance(_, fields) => {
                            if let Some((_, f)) = fields.iter_mut().find(|(name, _)| name == &field_name) {
                                *f = val.clone();
                            }
                        }
                        _ => return self.error(chunk_idx, ip, &format!("Cannot set field on {}", obj.type_name())),
                    }
                    self.stack.push(val);
                }
                Opcode::GetMethod(_idx) => {
                    let obj = self.stack.pop().unwrap();
                    // For now, just push the object (method binding TODO)
                    self.stack.push(obj);
                }

                // === Arrays ===
                Opcode::NewArray(len) => {
                    let mut elements = Vec::with_capacity(len as usize);
                    for _ in 0..len {
                        elements.push(self.stack.pop().unwrap());
                    }
                    elements.reverse();
                    self.stack.push(Value::Array(elements));
                }
                Opcode::GetIndex => {
                    let index = self.stack.pop().unwrap();
                    let obj = self.stack.pop().unwrap();
                    match (&obj, &index) {
                        (Value::Array(arr), Value::Int(i)) => {
                            if *i >= 0 && (*i as usize) < arr.len() {
                                self.stack.push(arr[*i as usize].clone());
                            } else {
                                return self.error(chunk_idx, ip, "Array index out of bounds");
                            }
                        }
                        (Value::Str(s), Value::Int(i)) => {
                            if *i >= 0 && (*i as usize) < s.len() {
                                let ch = s.chars().nth(*i as usize).unwrap_or('\0');
                                self.stack.push(Value::Str(ch.to_string()));
                            } else {
                                return self.error(chunk_idx, ip, "String index out of bounds");
                            }
                        }
                        _ => return self.error(chunk_idx, ip, &format!("Cannot index {}", obj.type_name())),
                    }
                }
                Opcode::SetIndex => {
                    let val = self.stack.pop().unwrap();
                    let index = self.stack.pop().unwrap();
                    let mut obj = self.stack.pop().unwrap();
                    match (&mut obj, &index) {
                        (Value::Array(arr), Value::Int(i)) => {
                            if *i >= 0 && (*i as usize) < arr.len() {
                                arr[*i as usize] = val.clone();
                            } else {
                                return self.error(chunk_idx, ip, "Array index out of bounds");
                            }
                        }
                        _ => return self.error(chunk_idx, ip, "Cannot set index"),
                    }
                    self.stack.push(val);
                }
                Opcode::ArrayLen => {
                    let obj = self.stack.pop().unwrap();
                    match obj {
                        Value::Array(arr) => self.stack.push(Value::Int(arr.len() as i64)),
                        Value::Str(s) => self.stack.push(Value::Int(s.len() as i64)),
                        _ => return self.error(chunk_idx, ip, &format!("Cannot get length of {}", obj.type_name())),
                    }
                }

                // === Strings ===
                Opcode::Concat => {
                    let right = self.stack.pop().unwrap();
                    let left = self.stack.pop().unwrap();
                    let result = format!("{}{}", left.to_string_value(), right.to_string_value());
                    self.stack.push(Value::Str(result));
                }
                Opcode::Interpolate(segments) => {
                    // Segments: N string parts, N-1 expressions between them
                    // Stack layout: [str0, expr0, str1, expr1, ..., strN]
                    let total = segments as usize * 2 - 1;
                    let mut parts = Vec::with_capacity(total);
                    for _ in 0..total {
                        parts.push(self.stack.pop().unwrap());
                    }
                    parts.reverse();
                    let mut result = String::new();
                    for (_i, part) in parts.iter().enumerate() {
                        result.push_str(&part.to_string_value());
                    }
                    self.stack.push(Value::Str(result));
                }

                // === Misc ===
                Opcode::Pop => {
                    self.stack.pop();
                }
                Opcode::Dup => {
                    let val = self.stack.last().unwrap().clone();
                    self.stack.push(val);
                }
                Opcode::Print => {
                    let val = self.stack.pop().unwrap();
                    let output = val.to_string_value();
                    println!("{}", output);
                    self.output.push_str(&output);
                    self.output.push('\n');
                }
                Opcode::Assert => {
                    let val = self.stack.pop().unwrap();
                    if !val.is_truthy() {
                        return self.error(chunk_idx, ip, "Assertion failed");
                    }
                }
                Opcode::Halt => {
                    break;
                }
            }
        }

        Ok(self.stack.pop().unwrap_or(Value::Nil))
    }

    fn handle_native_call(&mut self, _args: &[Value], _result: &Value, _chunk_idx: usize, _ip: usize) -> Result<(), RuntimeError> {
        Ok(())
    }

    fn error(&self, chunk_idx: usize, ip: usize, message: &str) -> Result<Value, RuntimeError> {
        Err(RuntimeError {
            message: message.to_string(),
            chunk_source: self.chunks[chunk_idx].source_file.clone(),
            offset: ip,
        })
    }

    /// Get the captured output (for testing).
    pub fn output(&self) -> &str {
        &self.output
    }

    /// Get the stack.
    pub fn stack(&self) -> &[Value] {
        &self.stack
    }

    /// Get global variables.
    pub fn globals(&self) -> &HashMap<String, Value> {
        &self.globals
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;
    use crate::parser::Parser;
    use crate::bytecode::compiler::BytecodeCompiler;

    fn run_source(source: &str) -> Result<Value, RuntimeError> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let ast = parser.parse_program().unwrap();
        let mut compiler = BytecodeCompiler::new();
        let chunks = compiler.compile(&ast).unwrap();
        let mut vm = Vm::new();
        vm.load(chunks);
        vm.run()
    }

    #[test]
    fn test_vm_integer() {
        let result = run_source("42;").unwrap();
        assert_eq!(result, Value::Int(42));
    }

    #[test]
    fn test_vm_arithmetic() {
        let result = run_source("2 + 3;").unwrap();
        assert_eq!(result, Value::Int(5));
    }

    #[test]
    fn test_vm_subtraction() {
        let result = run_source("10 - 3;").unwrap();
        assert_eq!(result, Value::Int(7));
    }

    #[test]
    fn test_vm_multiplication() {
        let result = run_source("4 * 5;").unwrap();
        assert_eq!(result, Value::Int(20));
    }

    #[test]
    fn test_vm_division() {
        let result = run_source("10 / 2;").unwrap();
        assert_eq!(result, Value::Int(5));
    }

    #[test]
    fn test_vm_modulo() {
        let result = run_source("10 % 3;").unwrap();
        assert_eq!(result, Value::Int(1));
    }

    #[test]
    fn test_vm_negation() {
        let result = run_source("-42;").unwrap();
        assert_eq!(result, Value::Int(-42));
    }

    #[test]
    fn test_vm_comparison() {
        let result = run_source("5 > 3;").unwrap();
        assert_eq!(result, Value::Bool(true));

        let result = run_source("5 < 3;").unwrap();
        assert_eq!(result, Value::Bool(false));

        let result = run_source("5 == 5;").unwrap();
        assert_eq!(result, Value::Bool(true));

        let result = run_source("5 != 5;").unwrap();
        assert_eq!(result, Value::Bool(false));
    }

    #[test]
    fn test_vm_logical() {
        let result = run_source("true && false;").unwrap();
        assert_eq!(result, Value::Bool(false));

        let result = run_source("true || false;").unwrap();
        assert_eq!(result, Value::Bool(true));

        let result = run_source("!true;").unwrap();
        assert_eq!(result, Value::Bool(false));
    }

    #[test]
    fn test_vm_variable() {
        let result = run_source("let x = 42; x;").unwrap();
        assert_eq!(result, Value::Int(42));
    }

    #[test]
    fn test_vm_string() {
        let result = run_source(r#""hello";"#).unwrap();
        assert_eq!(result, Value::Str("hello".into()));
    }

    #[test]
    fn test_vm_string_concat() {
        let result = run_source(r#""hello" + " " + "world";"#).unwrap();
        assert_eq!(result, Value::Str("hello world".into()));
    }

    #[test]
    fn test_vm_string_repeat() {
        let result = run_source(r#""ha" * 3;"#).unwrap();
        assert_eq!(result, Value::Str("hahaha".into()));
    }

    #[test]
    fn test_vm_if() {
        let result = run_source("if true { 1; } else { 2; }").unwrap();
        assert_eq!(result, Value::Int(1));

        let result = run_source("if false { 1; } else { 2; }").unwrap();
        assert_eq!(result, Value::Int(2));
    }

    #[test]
    fn test_vm_while() {
        let result = run_source("let i = 0; while i < 5 { i = i + 1; } i;").unwrap();
        assert_eq!(result, Value::Int(5));
    }

    #[test]
    fn test_vm_function() {
        let result = run_source("fn add(a, b) { return a + b; } add(2, 3);").unwrap();
        assert_eq!(result, Value::Int(5));
    }

    #[test]
    fn test_vm_recursive_function() {
        let source = r#"
            fn fib(n) {
                if n <= 1 { return n; }
                return fib(n - 1) + fib(n - 2);
            }
            fib(10);
        "#;
        let result = run_source(source).unwrap();
        assert_eq!(result, Value::Int(55));
    }

    #[test]
    fn test_vm_nested_if() {
        let source = r#"
            let x = 10;
            if x > 5 {
                if x > 8 { 1; } else { 2; }
            } else { 3; }
        "#;
        let result = run_source(source).unwrap();
        assert_eq!(result, Value::Int(1));
    }

    #[test]
    fn test_vm_short_circuit_and() {
        let result = run_source("false && (1 / 0 == 0);").unwrap();
        assert_eq!(result, Value::Bool(false));
    }

    #[test]
    fn test_vm_short_circuit_or() {
        let result = run_source("true || (1 / 0 == 0);").unwrap();
        assert_eq!(result, Value::Bool(true));
    }

    #[test]
    fn test_vm_array() {
        let result = run_source("let arr = [1, 2, 3]; arr[1];").unwrap();
        assert_eq!(result, Value::Int(2));
    }

    #[test]
    fn test_vm_array_length() {
        let result = run_source("let arr = [1, 2, 3]; arr;").unwrap();
        assert_eq!(result, Value::Array(vec![Value::Int(1), Value::Int(2), Value::Int(3)]));
    }

    #[test]
    fn test_vm_power() {
        let result = run_source("2 ** 10;").unwrap();
        assert_eq!(result, Value::Int(1024));
    }

    #[test]
    fn test_vm_float_arithmetic() {
        let result = run_source("3.14 * 2.0;").unwrap();
        assert_eq!(result, Value::Float(6.28));
    }

    #[test]
    fn test_vm_mixed_arithmetic() {
        let result = run_source("1 + 2.5;").unwrap();
        assert_eq!(result, Value::Float(3.5));
    }

    #[test]
    fn test_vm_nil() {
        let result = run_source("null;").unwrap();
        assert_eq!(result, Value::Nil);
    }

    #[test]
    fn test_vm_bool() {
        let result = run_source("true;").unwrap();
        assert_eq!(result, Value::Bool(true));
    }

    #[test]
    fn test_vm_string_index() {
        let result = run_source(r#"let s = "hello"; s[0];"#).unwrap();
        assert_eq!(result, Value::Str("h".into()));
    }

    #[test]
    fn test_vm_bitwise() {
        let result = run_source("0xFF & 0x0F;").unwrap();
        assert_eq!(result, Value::Int(0x0F));

        let result = run_source("0xF0 | 0x0F;").unwrap();
        assert_eq!(result, Value::Int(0xFF));

        let result = run_source("0xFF ^ 0x0F;").unwrap();
        assert_eq!(result, Value::Int(0xF0));

        let result = run_source("1 << 4;").unwrap();
        assert_eq!(result, Value::Int(16));
    }

    #[test]
    fn test_vm_compound_assignment() {
        let result = run_source("let x = 10; x += 5; x;").unwrap();
        assert_eq!(result, Value::Int(15));

        let result = run_source("let x = 10; x -= 3; x;").unwrap();
        assert_eq!(result, Value::Int(7));

        let result = run_source("let x = 10; x *= 2; x;").unwrap();
        assert_eq!(result, Value::Int(20));

        let result = run_source("let x = 10; x /= 2; x;").unwrap();
        assert_eq!(result, Value::Int(5));
    }

    #[test]
    fn test_vm_power_two_star() {
        let result = run_source("2 ** 10;").unwrap();
        assert_eq!(result, Value::Int(1024));

        let result = run_source("3 ** 3;").unwrap();
        assert_eq!(result, Value::Int(27));
    }

    #[test]
    fn test_vm_for_loop() {
        let result = run_source("let sum = 0; for x in [1, 2, 3, 4, 5] { sum += x; } sum;").unwrap();
        assert_eq!(result, Value::Int(15));
    }

    #[test]
    fn test_vm_match() {
        let result = run_source(r#"
            match 2 {
                1 => "one",
                2 => "two",
                3 => "three",
                _ => "other"
            };
        "#).unwrap();
        assert_eq!(result, Value::Str("two".into()));
    }

    #[test]
    fn test_vm_match_fallthrough() {
        let result = run_source(r#"
            match 99 {
                1 => "one",
                2 => "two",
                _ => "default"
            };
        "#).unwrap();
        assert_eq!(result, Value::Str("default".into()));
    }

    #[test]
    fn test_vm_match_first_arm() {
        let result = run_source(r#"
            match 1 {
                1 => "first",
                2 => "second",
                _ => "other"
            };
        "#).unwrap();
        assert_eq!(result, Value::Str("first".into()));
    }

    #[test]
    fn test_vm_match_last_literal() {
        let result = run_source(r#"
            match 3 {
                1 => "one",
                2 => "two",
                3 => "three"
            };
        "#).unwrap();
        assert_eq!(result, Value::Str("three".into()));
    }
}
