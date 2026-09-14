use crate::lexer::Spanned;

#[derive(Debug, Clone)]
pub enum Ast {
    // Expressions
    Literal(Literal),
    Ident(String),
    BinaryOp {
        op: BinOp,
        left: Box<Spanned<Ast>>,
        right: Box<Spanned<Ast>>,
    },
    UnaryOp {
        op: UnaryOp,
        expr: Box<Spanned<Ast>>,
    },
    Call {
        func: Box<Spanned<Ast>>,
        args: Vec<Spanned<Ast>>,
    },
    Index {
        object: Box<Spanned<Ast>>,
        index: Box<Spanned<Ast>>,
    },
    FieldAccess {
        object: Box<Spanned<Ast>>,
        field: String,
    },
    If {
        condition: Box<Spanned<Ast>>,
        then_branch: Box<Spanned<Ast>>,
        else_branch: Option<Box<Spanned<Ast>>>,
    },
    Match {
        expr: Box<Spanned<Ast>>,
        arms: Vec<MatchArm>,
    },
    Lambda {
        params: Vec<Param>,
        body: Box<Spanned<Ast>>,
    },
    Block(Vec<Spanned<Ast>>),

    // Statements
    Let {
        name: String,
        ty: Option<TypeAnnotation>,
        value: Option<Box<Spanned<Ast>>>,
        mutable: bool,
    },
    Return(Option<Box<Spanned<Ast>>>),
    Assign {
        target: Box<Spanned<Ast>>,
        value: Box<Spanned<Ast>>,
    },
    While {
        condition: Box<Spanned<Ast>>,
        body: Box<Spanned<Ast>>,
    },
    For {
        var: String,
        iter: Box<Spanned<Ast>>,
        body: Box<Spanned<Ast>>,
    },
    Loop(Box<Spanned<Ast>>),
    Break,
    Continue,
    Expr(Box<Spanned<Ast>>),

    // Declarations
    Function {
        name: String,
        params: Vec<Param>,
        return_type: Option<TypeAnnotation>,
        body: Box<Spanned<Ast>>,
        public: bool,
    },
    Struct {
        name: String,
        fields: Vec<Field>,
        public: bool,
    },
    Enum {
        name: String,
        variants: Vec<EnumVariant>,
        public: bool,
    },
    Impl {
        type_name: String,
        methods: Vec<Spanned<Ast>>,
    },
    Trait {
        name: String,
        methods: Vec<TraitMethod>,
        public: bool,
    },
    Import {
        path: Vec<String>,
        alias: Option<String>,
    },
    Array(Vec<Spanned<Ast>>),
    Module(Vec<Spanned<Ast>>),
}

#[derive(Debug, Clone)]
pub enum Literal {
    Integer(i64),
    Float(f64),
    String(String),
    Bool(bool),
    Char(char),
    Null,
}

#[derive(Debug, Clone, PartialEq)]
pub enum BinOp {
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Eq,
    Ne,
    Lt,
    Gt,
    Le,
    Ge,
    And,
    Or,
    BitAnd,
    BitOr,
    BitXor,
    Shl,
    Shr,
    Pow,
}

#[derive(Debug, Clone, PartialEq)]
pub enum UnaryOp {
    Neg,
    Not,
    BitNot,
}

#[derive(Debug, Clone)]
pub struct Param {
    pub name: String,
    pub ty: Option<TypeAnnotation>,
}

#[derive(Debug, Clone)]
pub struct Field {
    pub name: String,
    pub ty: TypeAnnotation,
    pub public: bool,
}

#[derive(Debug, Clone)]
pub struct EnumVariant {
    pub name: String,
    pub fields: Vec<TypeAnnotation>,
}

#[derive(Debug, Clone)]
pub struct MatchArm {
    pub pattern: Pattern,
    pub guard: Option<Box<Spanned<Ast>>>,
    pub body: Box<Spanned<Ast>>,
}

#[derive(Debug, Clone)]
pub enum Pattern {
    Literal(Literal),
    Ident(String),
    Wildcard,
    Tuple(Vec<Pattern>),
    Struct {
        name: String,
        fields: Vec<(String, Pattern)>,
    },
    Enum {
        name: String,
        args: Vec<Pattern>,
    },
}

#[derive(Debug, Clone)]
pub struct TraitMethod {
    pub name: String,
    pub params: Vec<Param>,
    pub return_type: Option<TypeAnnotation>,
}

#[derive(Debug, Clone)]
pub enum TypeAnnotation {
    Simple(String),
    Generic {
        name: String,
        args: Vec<TypeAnnotation>,
    },
    Array(Box<TypeAnnotation>),
    Function {
        params: Vec<TypeAnnotation>,
        return_type: Box<TypeAnnotation>,
    },
    Nullable(Box<TypeAnnotation>),
    Tuple(Vec<TypeAnnotation>),
}

impl TypeAnnotation {
    pub fn simple(name: &str) -> Self {
        TypeAnnotation::Simple(name.to_string())
    }

    pub fn array(inner: TypeAnnotation) -> Self {
        TypeAnnotation::Array(Box::new(inner))
    }

    pub fn nullable(inner: TypeAnnotation) -> Self {
        TypeAnnotation::Nullable(Box::new(inner))
    }
}
