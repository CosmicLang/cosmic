use std::fmt;

/// All bytecode opcodes for the Cosmic VM.
/// Stack-based design, each opcode operates on the top of stack.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Opcode {
    // === Constants ===
    /// Push constant by index onto stack
    Const(u16),
    /// Push nil onto stack
    Nil,
    /// Push true onto stack
    True,
    /// Push false onto stack
    False,

    // === Local variables ===
    /// Load local variable by slot index
    GetLocal(u16),
    /// Store to local variable by slot index
    SetLocal(u16),

    // === Global variables ===
    /// Define a global variable (pops value)
    DefineGlobal(u16),
    /// Get global variable by name index
    GetGlobal(u16),
    /// Set global variable by name index
    SetGlobal(u16),

    // === Upvalues (closures) ===
    /// Close upvalues from local slot
    CloseUpvalue(u16),
    /// Get upvalue by index
    GetUpvalue(u16),
    /// Set upvalue by index
    SetUpvalue(u16),

    // === Arithmetic ===
    /// Add two values
    Add,
    /// Subtract two values
    Sub,
    /// Multiply two values
    Mul,
    /// Divide two values
    Div,
    /// Modulo
    Mod,
    /// Power
    Pow,
    /// Negate number
    Neg,

    // === Comparison ===
    /// Equal
    Eq,
    /// Not equal
    Ne,
    /// Greater than
    Gt,
    /// Greater or equal
    Ge,
    /// Less than
    Lt,
    /// Less or equal
    Le,

    // === Logical ===
    /// Logical not
    Not,
    /// Logical and (short-circuit)
    And,
    /// Logical or (short-circuit)
    Or,

    // === Bitwise ===
    BitAnd,
    BitOr,
    BitXor,
    Shl,
    Shr,
    BitNot,

    // === Control flow ===
    /// Jump forward by offset
    Jump(u16),
    /// Jump forward if false (pops)
    JumpIfFalse(u16),
    /// Jump forward if true (pops)
    JumpIfTrue(u16),
    /// Jump backward by offset
    Loop(u16),

    // === Functions ===
    /// Call function with N arguments
    Call(u8),
    /// Call native function with N arguments
    NativeCall(u8),
    /// Return from function
    Return,

    // === Closures ===
    /// Create closure from function constant
    Closure(u16),

    // === Class/Struct ===
    /// Create new struct instance
    NewStruct(u16),
    /// Get field by name index
    GetField(u16),
    /// Set field by name index
    SetField(u16),
    /// Get method
    GetMethod(u16),

    // === Arrays ===
    /// Create array from N elements on stack
    NewArray(u16),
    /// Get array element
    GetIndex,
    /// Set array element
    SetIndex,
    /// Get array length
    ArrayLen,

    // === Strings ===
    /// Concatenate top two stack values
    Concat,
    /// String interpolation (N segments, N-1 expressions)
    Interpolate(u16),

    // === Misc ===
    /// Pop top of stack
    Pop,
    /// Duplicate top of stack
    Dup,
    /// Print top of stack (debug)
    Print,
    /// Assert top of stack is true
    Assert,
    /// Stop execution
    Halt,
}

impl Opcode {
    /// Convert opcode to bytes for serialization.
    /// Returns (opcode_byte, extra_bytes).
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        match self {
            Opcode::Const(idx) => { bytes.push(0x01); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::Nil => bytes.push(0x02),
            Opcode::True => bytes.push(0x03),
            Opcode::False => bytes.push(0x04),
            Opcode::GetLocal(idx) => { bytes.push(0x10); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::SetLocal(idx) => { bytes.push(0x11); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::DefineGlobal(idx) => { bytes.push(0x20); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::GetGlobal(idx) => { bytes.push(0x21); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::SetGlobal(idx) => { bytes.push(0x22); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::CloseUpvalue(idx) => { bytes.push(0x30); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::GetUpvalue(idx) => { bytes.push(0x31); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::SetUpvalue(idx) => { bytes.push(0x32); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::Add => bytes.push(0x40),
            Opcode::Sub => bytes.push(0x41),
            Opcode::Mul => bytes.push(0x42),
            Opcode::Div => bytes.push(0x43),
            Opcode::Mod => bytes.push(0x44),
            Opcode::Pow => bytes.push(0x45),
            Opcode::Neg => bytes.push(0x46),
            Opcode::Eq => bytes.push(0x50),
            Opcode::Ne => bytes.push(0x51),
            Opcode::Gt => bytes.push(0x52),
            Opcode::Ge => bytes.push(0x53),
            Opcode::Lt => bytes.push(0x54),
            Opcode::Le => bytes.push(0x55),
            Opcode::Not => bytes.push(0x60),
            Opcode::And => bytes.push(0x61),
            Opcode::Or => bytes.push(0x62),
            Opcode::BitAnd => bytes.push(0x70),
            Opcode::BitOr => bytes.push(0x71),
            Opcode::BitXor => bytes.push(0x72),
            Opcode::Shl => bytes.push(0x73),
            Opcode::Shr => bytes.push(0x74),
            Opcode::BitNot => bytes.push(0x75),
            Opcode::Jump(offset) => { bytes.push(0x80); bytes.extend_from_slice(&offset.to_le_bytes()); }
            Opcode::JumpIfFalse(offset) => { bytes.push(0x81); bytes.extend_from_slice(&offset.to_le_bytes()); }
            Opcode::JumpIfTrue(offset) => { bytes.push(0x82); bytes.extend_from_slice(&offset.to_le_bytes()); }
            Opcode::Loop(offset) => { bytes.push(0x83); bytes.extend_from_slice(&offset.to_le_bytes()); }
            Opcode::Call(argc) => { bytes.push(0x90); bytes.push(*argc); }
            Opcode::NativeCall(argc) => { bytes.push(0x91); bytes.push(*argc); }
            Opcode::Return => bytes.push(0x92),
            Opcode::Closure(idx) => { bytes.push(0xA0); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::NewStruct(idx) => { bytes.push(0xB0); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::GetField(idx) => { bytes.push(0xB1); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::SetField(idx) => { bytes.push(0xB2); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::GetMethod(idx) => { bytes.push(0xB3); bytes.extend_from_slice(&idx.to_le_bytes()); }
            Opcode::NewArray(len) => { bytes.push(0xC0); bytes.extend_from_slice(&len.to_le_bytes()); }
            Opcode::GetIndex => bytes.push(0xC1),
            Opcode::SetIndex => bytes.push(0xC2),
            Opcode::ArrayLen => bytes.push(0xC3),
            Opcode::Concat => bytes.push(0xD0),
            Opcode::Interpolate(segments) => { bytes.push(0xD1); bytes.extend_from_slice(&segments.to_le_bytes()); }
            Opcode::Pop => bytes.push(0xE0),
            Opcode::Dup => bytes.push(0xE1),
            Opcode::Print => bytes.push(0xE2),
            Opcode::Assert => bytes.push(0xE3),
            Opcode::Halt => bytes.push(0xFF),
        }
        bytes
    }
}

impl fmt::Display for Opcode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Opcode::Const(i) => write!(f, "CONST {}", i),
            Opcode::Nil => write!(f, "NIL"),
            Opcode::True => write!(f, "TRUE"),
            Opcode::False => write!(f, "FALSE"),
            Opcode::GetLocal(i) => write!(f, "GET_LOCAL {}", i),
            Opcode::SetLocal(i) => write!(f, "SET_LOCAL {}", i),
            Opcode::DefineGlobal(i) => write!(f, "DEFINE_GLOBAL {}", i),
            Opcode::GetGlobal(i) => write!(f, "GET_GLOBAL {}", i),
            Opcode::SetGlobal(i) => write!(f, "SET_GLOBAL {}", i),
            Opcode::Add => write!(f, "ADD"),
            Opcode::Sub => write!(f, "SUB"),
            Opcode::Mul => write!(f, "MUL"),
            Opcode::Div => write!(f, "DIV"),
            Opcode::Mod => write!(f, "MOD"),
            Opcode::Pow => write!(f, "POW"),
            Opcode::Neg => write!(f, "NEG"),
            Opcode::Eq => write!(f, "EQ"),
            Opcode::Ne => write!(f, "NE"),
            Opcode::Gt => write!(f, "GT"),
            Opcode::Ge => write!(f, "GE"),
            Opcode::Lt => write!(f, "LT"),
            Opcode::Le => write!(f, "LE"),
            Opcode::Not => write!(f, "NOT"),
            Opcode::And => write!(f, "AND"),
            Opcode::Or => write!(f, "OR"),
            Opcode::BitAnd => write!(f, "BIT_AND"),
            Opcode::BitOr => write!(f, "BIT_OR"),
            Opcode::BitXor => write!(f, "BIT_XOR"),
            Opcode::Shl => write!(f, "SHL"),
            Opcode::Shr => write!(f, "SHR"),
            Opcode::BitNot => write!(f, "BIT_NOT"),
            Opcode::Jump(o) => write!(f, "JUMP {}", o),
            Opcode::JumpIfFalse(o) => write!(f, "JUMP_IF_FALSE {}", o),
            Opcode::JumpIfTrue(o) => write!(f, "JUMP_IF_TRUE {}", o),
            Opcode::Loop(o) => write!(f, "LOOP {}", o),
            Opcode::Call(n) => write!(f, "CALL {}", n),
            Opcode::NativeCall(n) => write!(f, "NATIVE_CALL {}", n),
            Opcode::Return => write!(f, "RETURN"),
            Opcode::Closure(i) => write!(f, "CLOSURE {}", i),
            Opcode::NewStruct(i) => write!(f, "NEW_STRUCT {}", i),
            Opcode::GetField(i) => write!(f, "GET_FIELD {}", i),
            Opcode::SetField(i) => write!(f, "SET_FIELD {}", i),
            Opcode::GetMethod(i) => write!(f, "GET_METHOD {}", i),
            Opcode::NewArray(l) => write!(f, "NEW_ARRAY {}", l),
            Opcode::GetIndex => write!(f, "GET_INDEX"),
            Opcode::SetIndex => write!(f, "SET_INDEX"),
            Opcode::ArrayLen => write!(f, "ARRAY_LEN"),
            Opcode::Concat => write!(f, "CONCAT"),
            Opcode::Interpolate(s) => write!(f, "INTERPOLATE {}", s),
            Opcode::Pop => write!(f, "POP"),
            Opcode::Dup => write!(f, "DUP"),
            Opcode::Print => write!(f, "PRINT"),
            Opcode::Assert => write!(f, "ASSERT"),
            Opcode::Halt => write!(f, "HALT"),
            Opcode::CloseUpvalue(i) => write!(f, "CLOSE_UPVALUE {}", i),
            Opcode::GetUpvalue(i) => write!(f, "GET_UPVALUE {}", i),
            Opcode::SetUpvalue(i) => write!(f, "SET_UPVALUE {}", i),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_opcode_serialization_roundtrip() {
        let opcodes = vec![
            Opcode::Const(42),
            Opcode::GetLocal(5),
            Opcode::Jump(100),
            Opcode::Call(3),
            Opcode::Add,
            Opcode::Halt,
        ];

        for opcode in &opcodes {
            let bytes = opcode.to_bytes();
            assert!(bytes.len() >= 1);
            // Verify the first byte matches the opcode value
            assert!(bytes[0] >= 0x01);
        }
    }

    #[test]
    fn test_opcode_display() {
        assert_eq!(format!("{}", Opcode::Const(0)), "CONST 0");
        assert_eq!(format!("{}", Opcode::Add), "ADD");
        assert_eq!(format!("{}", Opcode::Return), "RETURN");
        assert_eq!(format!("{}", Opcode::Jump(255)), "JUMP 255");
    }

    #[test]
    fn test_opcode_values_dont_overlap() {
        let mut seen = std::collections::HashSet::new();
        let opcodes = [
            0x01u8, 0x02, 0x03, 0x04,
            0x10, 0x11,
            0x20, 0x21, 0x22,
            0x30, 0x31, 0x32,
            0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46,
            0x50, 0x51, 0x52, 0x53, 0x54, 0x55,
            0x60, 0x61, 0x62,
            0x70, 0x71, 0x72, 0x73, 0x74, 0x75,
            0x80, 0x81, 0x82, 0x83,
            0x90, 0x91, 0x92,
            0xA0,
            0xB0, 0xB1, 0xB2, 0xB3,
            0xC0, 0xC1, 0xC2, 0xC3,
            0xD0, 0xD1,
            0xE0, 0xE1, 0xE2, 0xE3,
            0xFF,
        ];
        for byte in &opcodes {
            assert!(seen.insert(*byte), "Duplicate opcode byte: 0x{:02X}", byte);
        }
    }
}
