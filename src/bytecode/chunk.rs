use crate::bytecode::opcodes::Opcode;
use std::fmt;

/// All runtime values in the Cosmic VM.
#[derive(Debug, Clone)]
pub enum Value {
    Nil,
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    /// Native function pointer
    NativeFn(fn(&[Value]) -> Value),
    /// User-defined function (chunk index, arity, upvalue count)
    Func(usize, u8, u8),
    /// Closure (function index, captured upvalues)
    Closure(usize, Vec<Upvalue>),
    /// Struct instance (struct definition index, named fields)
    Instance(usize, Vec<(String, Value)>),
    /// Array of values
    Array(Vec<Value>),
}

#[derive(Debug, Clone)]
pub enum Upvalue {
    /// Index into the stack
    Open(usize),
    /// Reference to another upvalue in a closure
    Closed(Value),
}

impl PartialEq for Value {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Nil, Value::Nil) => true,
            (Value::Bool(a), Value::Bool(b)) => a == b,
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => a == b,
            (Value::Str(a), Value::Str(b)) => a == b,
            (Value::Array(a), Value::Array(b)) => a == b,
            _ => false,
        }
    }
}

impl Value {
    pub fn is_truthy(&self) -> bool {
        match self {
            Value::Nil => false,
            Value::Bool(b) => *b,
            Value::Int(n) => *n != 0,
            Value::Float(n) => *n != 0.0,
            Value::Str(s) => !s.is_empty(),
            _ => true,
        }
    }

    pub fn type_name(&self) -> &str {
        match self {
            Value::Nil => "nil",
            Value::Bool(_) => "bool",
            Value::Int(_) => "int",
            Value::Float(_) => "float",
            Value::Str(_) => "string",
            Value::NativeFn(_) => "native_fn",
            Value::Func(_, _, _) => "func",
            Value::Closure(_, _) => "closure",
            Value::Instance(_, _) => "instance",
            Value::Array(_) => "array",
        }
    }

    pub fn to_string_value(&self) -> String {
        match self {
            Value::Nil => "nil".to_string(),
            Value::Bool(b) => b.to_string(),
            Value::Int(n) => n.to_string(),
            Value::Float(n) => {
                if n.fract() == 0.0 {
                    format!("{:.1}", n)
                } else {
                    n.to_string()
                }
            }
            Value::Str(s) => s.clone(),
            Value::NativeFn(_) => "<native fn>".to_string(),
            Value::Func(idx, _, _) => format!("<fn {}>", idx),
            Value::Closure(idx, _) => format!("<closure {}>", idx),
            Value::Instance(sid, _) => format!("<instance {}>", sid),
            Value::Array(arr) => {
                let items: Vec<String> = arr.iter().map(|v| v.to_string_value()).collect();
                format!("[{}]", items.join(", "))
            }
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_string_value())
    }
}

/// A chunk of compiled bytecode.
#[derive(Debug, Clone)]
pub struct Chunk {
    /// The bytecode instructions
    pub code: Vec<u8>,
    /// Line info for each byte (for error reporting)
    pub lines: Vec<u16>,
    /// Constant pool
    pub constants: Vec<Value>,
    /// Source file name
    pub source_file: String,
}

impl Chunk {
    pub fn new(source_file: &str) -> Self {
        Chunk {
            code: Vec::new(),
            lines: Vec::new(),
            constants: Vec::new(),
            source_file: source_file.to_string(),
        }
    }

    /// Emit a single opcode, returns the byte offset where it was written.
    pub fn emit(&mut self, opcode: Opcode, line: u16) -> usize {
        let offset = self.code.len();
        let bytes = opcode.to_bytes();
        for b in &bytes {
            self.code.push(*b);
            self.lines.push(line);
        }
        offset
    }

    /// Add a constant and return its index.
    pub fn add_constant(&mut self, value: Value) -> u16 {
        let idx = self.constants.len();
        self.constants.push(value);
        idx as u16
    }

    /// Get constant by index.
    pub fn get_constant(&self, idx: u16) -> &Value {
        &self.constants[idx as usize]
    }

    /// Patch a jump offset at the given byte position.
    pub fn patch_jump(&mut self, offset: usize) {
        let jump = (self.code.len() - offset - 3) as u16;
        self.code[offset + 1] = (jump & 0xFF) as u8;
        self.code[offset + 2] = ((jump >> 8) & 0xFF) as u8;
    }

    /// Disassemble all instructions in the chunk.
    pub fn disassemble(&self) -> String {
        let mut output = String::new();
        let mut offset = 0;
        while offset < self.code.len() {
            let (opcode, size) = self.read_opcode(offset);
            output.push_str(&format!("{:04} | ", offset));
            output.push_str(&format!("{}\n", opcode));
            offset += size;
        }
        output
    }

    /// Read a single opcode from the bytecode at the given offset.
    /// Returns the opcode and the number of bytes consumed.
    pub fn read_opcode(&self, offset: usize) -> (Opcode, usize) {
        let byte = self.code[offset];
        match byte {
            0x01 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::Const(idx), 3)
            }
            0x02 => (Opcode::Nil, 1),
            0x03 => (Opcode::True, 1),
            0x04 => (Opcode::False, 1),
            0x10 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::GetLocal(idx), 3)
            }
            0x11 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::SetLocal(idx), 3)
            }
            0x20 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::DefineGlobal(idx), 3)
            }
            0x21 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::GetGlobal(idx), 3)
            }
            0x22 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::SetGlobal(idx), 3)
            }
            0x40 => (Opcode::Add, 1),
            0x41 => (Opcode::Sub, 1),
            0x42 => (Opcode::Mul, 1),
            0x43 => (Opcode::Div, 1),
            0x44 => (Opcode::Mod, 1),
            0x45 => (Opcode::Pow, 1),
            0x46 => (Opcode::Neg, 1),
            0x50 => (Opcode::Eq, 1),
            0x51 => (Opcode::Ne, 1),
            0x52 => (Opcode::Gt, 1),
            0x53 => (Opcode::Ge, 1),
            0x54 => (Opcode::Lt, 1),
            0x55 => (Opcode::Le, 1),
            0x60 => (Opcode::Not, 1),
            0x61 => (Opcode::And, 1),
            0x62 => (Opcode::Or, 1),
            0x70 => (Opcode::BitAnd, 1),
            0x71 => (Opcode::BitOr, 1),
            0x72 => (Opcode::BitXor, 1),
            0x73 => (Opcode::Shl, 1),
            0x74 => (Opcode::Shr, 1),
            0x75 => (Opcode::BitNot, 1),
            0x80 => {
                let offset = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::Jump(offset), 3)
            }
            0x81 => {
                let offset = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::JumpIfFalse(offset), 3)
            }
            0x82 => {
                let offset = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::JumpIfTrue(offset), 3)
            }
            0x83 => {
                let offset = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::Loop(offset), 3)
            }
            0x90 => (Opcode::Call(self.code[offset+1]), 2),
            0x91 => (Opcode::NativeCall(self.code[offset+1]), 2),
            0x92 => (Opcode::Return, 1),
            0xA0 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::Closure(idx), 3)
            }
            0xB0 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::NewStruct(idx), 3)
            }
            0xB1 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::GetField(idx), 3)
            }
            0xB2 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::SetField(idx), 3)
            }
            0xB3 => {
                let idx = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::GetMethod(idx), 3)
            }
            0xC0 => {
                let len = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::NewArray(len), 3)
            }
            0xC1 => (Opcode::GetIndex, 1),
            0xC2 => (Opcode::SetIndex, 1),
            0xC3 => (Opcode::ArrayLen, 1),
            0xD0 => (Opcode::Concat, 1),
            0xD1 => {
                let seg = u16::from_le_bytes([self.code[offset+1], self.code[offset+2]]);
                (Opcode::Interpolate(seg), 3)
            }
            0xE0 => (Opcode::Pop, 1),
            0xE1 => (Opcode::Dup, 1),
            0xE2 => (Opcode::Print, 1),
            0xE3 => (Opcode::Assert, 1),
            0xFF => (Opcode::Halt, 1),
            _ => (Opcode::Halt, 1), // Unknown opcode = halt
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chunk_emit_and_read() {
        let mut chunk = Chunk::new("test");
        chunk.emit(Opcode::Const(0), 1);
        chunk.emit(Opcode::Add, 1);
        chunk.emit(Opcode::Return, 1);

        let (op1, size1) = chunk.read_opcode(0);
        assert_eq!(op1, Opcode::Const(0));
        assert_eq!(size1, 3);

        let (op2, size2) = chunk.read_opcode(3);
        assert_eq!(op2, Opcode::Add);
        assert_eq!(size2, 1);

        let (op3, size3) = chunk.read_opcode(4);
        assert_eq!(op3, Opcode::Return);
        assert_eq!(size3, 1);
    }

    #[test]
    fn test_chunk_constants() {
        let mut chunk = Chunk::new("test");
        let idx = chunk.add_constant(Value::Int(42));
        assert_eq!(idx, 0);
        assert_eq!(*chunk.get_constant(0), Value::Int(42));
    }

    #[test]
    fn test_value_truthy() {
        assert!(!Value::Nil.is_truthy());
        assert!(!Value::Bool(false).is_truthy());
        assert!(Value::Bool(true).is_truthy());
        assert!(!Value::Int(0).is_truthy());
        assert!(Value::Int(1).is_truthy());
        assert!(!Value::Float(0.0).is_truthy());
        assert!(Value::Float(1.0).is_truthy());
        assert!(!Value::Str(String::new()).is_truthy());
        assert!(Value::Str("hello".into()).is_truthy());
        assert!(Value::Array(vec![]).is_truthy());
    }

    #[test]
    fn test_value_display() {
        assert_eq!(Value::Nil.to_string(), "nil");
        assert_eq!(Value::Bool(true).to_string(), "true");
        assert_eq!(Value::Int(42).to_string(), "42");
        assert_eq!(Value::Str("hello".into()).to_string(), "hello");
        assert_eq!(
            Value::Array(vec![Value::Int(1), Value::Int(2)]).to_string(),
            "[1, 2]"
        );
    }

    #[test]
    fn test_value_equality() {
        assert_eq!(Value::Nil, Value::Nil);
        assert_eq!(Value::Int(42), Value::Int(42));
        assert_ne!(Value::Int(42), Value::Int(43));
        assert_ne!(Value::Int(42), Value::Float(42.0));
        assert_eq!(Value::Str("hi".into()), Value::Str("hi".into()));
        assert_ne!(Value::Str("hi".into()), Value::Str("bye".into()));
    }
}
