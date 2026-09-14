use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    // Literals
    Integer(i64),
    Float(f64),
    String(String),
    Bool(bool),
    Char(char),

    // Identifiers and keywords
    Ident(String),
    
    // Keywords
    Let,
    Mut,
    Fn,
    Return,
    If,
    Else,
    While,
    For,
    In,
    Match,
    Struct,
    Enum,
    Impl,
    Trait,
    Import,
    As,
    Pub,
    Priv,
    Async,
    Await,
    Loop,
    Break,
    Continue,
    Self_,
    True,
    False,
    Null,
    Typeof,
    Sizeof,

    // Operators
    Plus,
    Minus,
    Star,
    Slash,
    Percent,
    Caret,
    Amp,
    Pipe,
    Tilde,
    Bang,
    Eq,
    EqEq,
    Ne,
    Lt,
    Gt,
    Le,
    Ge,
    AmpAmp,
    PipePipe,
    PlusEq,
    MinusEq,
    StarEq,
    SlashEq,
    Arrow,
    FatArrow,
    Dot,
    DotDot,
    Question,
    Colon,
    ColonColon,
    Semicolon,
    Comma,

    // Delimiters
    LParen,
    RParen,
    LBrace,
    RBrace,
    LBracket,
    RBracket,

    // Special
    Eof,
    Newline,
}

#[derive(Debug, Clone)]
pub struct Spanned<T> {
    pub value: T,
    pub line: usize,
    pub col: usize,
    pub len: usize,
}

pub type TokenSpan = Spanned<Token>;

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Token::Integer(n) => write!(f, "{}", n),
            Token::Float(n) => write!(f, "{}", n),
            Token::String(s) => write!(f, "\"{}\"", s),
            Token::Bool(b) => write!(f, "{}", b),
            Token::Char(c) => write!(f, "'{}'", c),
            Token::Ident(s) => write!(f, "{}", s),
            Token::Let => write!(f, "let"),
            Token::Mut => write!(f, "mut"),
            Token::Fn => write!(f, "fn"),
            Token::Return => write!(f, "return"),
            Token::If => write!(f, "if"),
            Token::Else => write!(f, "else"),
            Token::While => write!(f, "while"),
            Token::For => write!(f, "for"),
            Token::In => write!(f, "in"),
            Token::Match => write!(f, "match"),
            Token::Struct => write!(f, "struct"),
            Token::Enum => write!(f, "enum"),
            Token::Impl => write!(f, "impl"),
            Token::Trait => write!(f, "trait"),
            Token::Import => write!(f, "import"),
            Token::As => write!(f, "as"),
            Token::Pub => write!(f, "pub"),
            Token::Priv => write!(f, "priv"),
            Token::Async => write!(f, "async"),
            Token::Await => write!(f, "await"),
            Token::Loop => write!(f, "loop"),
            Token::Break => write!(f, "break"),
            Token::Continue => write!(f, "continue"),
            Token::Self_ => write!(f, "self"),
            Token::True => write!(f, "true"),
            Token::False => write!(f, "false"),
            Token::Null => write!(f, "null"),
            Token::Typeof => write!(f, "typeof"),
            Token::Sizeof => write!(f, "sizeof"),
            Token::Plus => write!(f, "+"),
            Token::Minus => write!(f, "-"),
            Token::Star => write!(f, "*"),
            Token::Slash => write!(f, "/"),
            Token::Percent => write!(f, "%"),
            Token::Caret => write!(f, "^"),
            Token::Amp => write!(f, "&"),
            Token::Pipe => write!(f, "|"),
            Token::Tilde => write!(f, "~"),
            Token::Bang => write!(f, "!"),
            Token::Eq => write!(f, "="),
            Token::EqEq => write!(f, "=="),
            Token::Ne => write!(f, "!="),
            Token::Lt => write!(f, "<"),
            Token::Gt => write!(f, ">"),
            Token::Le => write!(f, "<="),
            Token::Ge => write!(f, ">="),
            Token::AmpAmp => write!(f, "&&"),
            Token::PipePipe => write!(f, "||"),
            Token::PlusEq => write!(f, "+="),
            Token::MinusEq => write!(f, "-="),
            Token::StarEq => write!(f, "*="),
            Token::SlashEq => write!(f, "/="),
            Token::Arrow => write!(f, "->"),
            Token::FatArrow => write!(f, "=>"),
            Token::Dot => write!(f, "."),
            Token::DotDot => write!(f, ".."),
            Token::Question => write!(f, "?"),
            Token::Colon => write!(f, ":"),
            Token::ColonColon => write!(f, "::"),
            Token::Semicolon => write!(f, ";"),
            Token::Comma => write!(f, ","),
            Token::LParen => write!(f, "("),
            Token::RParen => write!(f, ")"),
            Token::LBrace => write!(f, "{{"),
            Token::RBrace => write!(f, "}}"),
            Token::LBracket => write!(f, "["),
            Token::RBracket => write!(f, "]"),
            Token::Eof => write!(f, "EOF"),
            Token::Newline => write!(f, "\\n"),
        }
    }
}

pub struct Lexer {
    source: Vec<char>,
    pos: usize,
    line: usize,
    col: usize,
}

impl Lexer {
    pub fn new(source: &str) -> Self {
        Lexer {
            source: source.chars().collect(),
            pos: 0,
            line: 1,
            col: 1,
        }
    }

    fn peek(&self) -> Option<char> {
        self.source.get(self.pos).copied()
    }

    fn peek_next(&self) -> Option<char> {
        self.source.get(self.pos + 1).copied()
    }

    fn advance(&mut self) -> Option<char> {
        let ch = self.source.get(self.pos).copied()?;
        self.pos += 1;
        if ch == '\n' {
            self.line += 1;
            self.col = 1;
        } else {
            self.col += 1;
        }
        Some(ch)
    }

    fn skip_whitespace(&mut self) {
        while let Some(ch) = self.peek() {
            if ch.is_whitespace() {
                self.advance();
            } else if ch == '/' && self.peek_next() == Some('/') {
                // Line comment
                while let Some(ch) = self.peek() {
                    if ch == '\n' {
                        break;
                    }
                    self.advance();
                }
            } else if ch == '/' && self.peek_next() == Some('*') {
                // Block comment
                self.advance(); // /
                self.advance(); // *
                let mut depth = 1;
                while depth > 0 {
                    match self.peek() {
                        Some('*') if self.peek_next() == Some('/') => {
                            self.advance();
                            self.advance();
                            depth -= 1;
                        }
                        Some('/') if self.peek_next() == Some('*') => {
                            self.advance();
                            self.advance();
                            depth += 1;
                        }
                        Some(_) => {
                            self.advance();
                        }
                        None => break,
                    }
                }
            } else {
                break;
            }
        }
    }

    fn read_string(&mut self) -> Result<Token, String> {
        let mut s = String::new();
        loop {
            match self.advance() {
                Some('"') => return Ok(Token::String(s)),
                Some('\\') => {
                    match self.advance() {
                        Some('n') => s.push('\n'),
                        Some('t') => s.push('\t'),
                        Some('r') => s.push('\r'),
                        Some('\\') => s.push('\\'),
                        Some('"') => s.push('"'),
                        Some('0') => s.push('\0'),
                        Some(c) => return Err(format!("Invalid escape: \\{}", c)),
                        None => return Err("Unterminated string".into()),
                    }
                }
                Some(c) => s.push(c),
                None => return Err("Unterminated string".into()),
            }
        }
    }

    fn read_char(&mut self) -> Result<Token, String> {
        let c = self.advance().ok_or("Unterminated char literal")?;
        if c == '\\' {
            let escaped = self.advance().ok_or("Unterminated char literal")?;
            let ch = match escaped {
                'n' => '\n',
                't' => '\t',
                'r' => '\r',
                '\\' => '\\',
                '\'' => '\'',
                '0' => '\0',
                _ => return Err(format!("Invalid escape: \\{}", escaped)),
            };
            if self.advance() != Some('\'') {
                return Err("Unterminated char literal".into());
            }
            Ok(Token::Char(ch))
        } else {
            if self.advance() != Some('\'') {
                return Err("Unterminated char literal".into());
            }
            Ok(Token::Char(c))
        }
    }

    fn read_number(&mut self) -> Token {
        let start = self.pos - 1;
        let mut is_float = false;

        while let Some(ch) = self.peek() {
            if ch.is_ascii_digit() {
                self.advance();
            } else if ch == '.' && !is_float {
                if self.peek_next() == Some('.') {
                    break; // Range operator
                }
                is_float = true;
                self.advance();
            } else {
                break;
            }
        }

        let s: String = self.source[start..self.pos].iter().collect();
        if is_float {
            Token::Float(s.parse().unwrap_or(0.0))
        } else {
            Token::Integer(s.parse().unwrap_or(0))
        }
    }

    fn read_ident(&mut self) -> Token {
        let start = self.pos - 1;
        while let Some(ch) = self.peek() {
            if ch.is_alphanumeric() || ch == '_' {
                self.advance();
            } else {
                break;
            }
        }
        let s: String = self.source[start..self.pos].iter().collect();
        
        match s.as_str() {
            "let" => Token::Let,
            "mut" => Token::Mut,
            "fn" => Token::Fn,
            "return" => Token::Return,
            "if" => Token::If,
            "else" => Token::Else,
            "while" => Token::While,
            "for" => Token::For,
            "in" => Token::In,
            "match" => Token::Match,
            "struct" => Token::Struct,
            "enum" => Token::Enum,
            "impl" => Token::Impl,
            "trait" => Token::Trait,
            "import" => Token::Import,
            "as" => Token::As,
            "pub" => Token::Pub,
            "priv" => Token::Priv,
            "async" => Token::Async,
            "await" => Token::Await,
            "loop" => Token::Loop,
            "break" => Token::Break,
            "continue" => Token::Continue,
            "self" => Token::Self_,
            "true" => Token::True,
            "false" => Token::False,
            "null" => Token::Null,
            "typeof" => Token::Typeof,
            "sizeof" => Token::Sizeof,
            _ => Token::Ident(s),
        }
    }

    pub fn tokenize(&mut self) -> Result<Vec<TokenSpan>, String> {
        let mut tokens = Vec::new();

        loop {
            self.skip_whitespace();

            let line = self.line;
            let col = self.col;

            let Some(ch) = self.advance() else {
                tokens.push(Spanned {
                    value: Token::Eof,
                    line,
                    col,
                    len: 0,
                });
                break;
            };

            let token = match ch {
                '\n' => {
                    // Skip newlines but track them
                    continue;
                }
                '+' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::PlusEq
                    } else {
                        Token::Plus
                    }
                }
                '-' => {
                    if self.peek() == Some('>') {
                        self.advance();
                        Token::Arrow
                    } else if self.peek() == Some('=') {
                        self.advance();
                        Token::MinusEq
                    } else {
                        Token::Minus
                    }
                }
                '*' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::StarEq
                    } else {
                        Token::Star
                    }
                }
                '/' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::SlashEq
                    } else {
                        Token::Slash
                    }
                }
                '%' => Token::Percent,
                '^' => Token::Caret,
                '&' => {
                    if self.peek() == Some('&') {
                        self.advance();
                        Token::AmpAmp
                    } else {
                        Token::Amp
                    }
                }
                '|' => {
                    if self.peek() == Some('|') {
                        self.advance();
                        Token::PipePipe
                    } else {
                        Token::Pipe
                    }
                }
                '~' => Token::Tilde,
                '!' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::Ne
                    } else {
                        Token::Bang
                    }
                }
                '=' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::EqEq
                    } else if self.peek() == Some('>') {
                        self.advance();
                        Token::FatArrow
                    } else {
                        Token::Eq
                    }
                }
                '<' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::Le
                    } else {
                        Token::Lt
                    }
                }
                '>' => {
                    if self.peek() == Some('=') {
                        self.advance();
                        Token::Ge
                    } else {
                        Token::Gt
                    }
                }
                '.' => {
                    if self.peek() == Some('.') {
                        self.advance();
                        Token::DotDot
                    } else {
                        Token::Dot
                    }
                }
                '?' => Token::Question,
                ':' => {
                    if self.peek() == Some(':') {
                        self.advance();
                        Token::ColonColon
                    } else {
                        Token::Colon
                    }
                }
                ';' => Token::Semicolon,
                ',' => Token::Comma,
                '(' => Token::LParen,
                ')' => Token::RParen,
                '{' => Token::LBrace,
                '}' => Token::RBrace,
                '[' => Token::LBracket,
                ']' => Token::RBracket,
                '"' => self.read_string()?,
                '\'' => self.read_char()?,
                c if c.is_ascii_digit() => self.read_number(),
                c if c.is_alphabetic() || c == '_' => self.read_ident(),
                _ => return Err(format!("Unexpected character: '{}'", ch)),
            };

            let len = self.col - col + 1;
            tokens.push(Spanned {
                value: token,
                line,
                col,
                len,
            });
        }

        Ok(tokens)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_tokens() {
        let mut lexer = Lexer::new("let x = 42");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens.len(), 5); // let, x, =, 42, EOF
    }

    #[test]
    fn test_string_literal() {
        let mut lexer = Lexer::new(r#""hello world""#);
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].value, Token::String("hello world".into()));
    }

    #[test]
    fn test_operators() {
        let mut lexer = Lexer::new("+-*/%=!<>");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens.len(), 10); // 9 operators + EOF
    }
}
