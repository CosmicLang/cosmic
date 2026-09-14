use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    Integer(i64),
    Float(f64),
    String(String),
    Bool(bool),
    Char(char),

    Ident(String),
    
    Let, Mut, Fn, Return, If, Else, While, For, In, Match,
    Struct, Enum, Impl, Trait, Import, As, Pub, Priv,
    Async, Await, Loop, Break, Continue, Self_, Null,
    Typeof, Sizeof, Test,

    Plus, Minus, Star, Slash, Percent,
    Caret, Amp, Pipe, Tilde, Bang,
    Eq, EqEq, Ne, Lt, Gt, Le, Ge,
    AmpAmp, PipePipe,
    PlusEq, MinusEq, StarEq, SlashEq,
    Arrow, FatArrow, Dot, DotDot, Question,
    Colon, ColonColon, Semicolon, Comma,
    Shl, Shr,

    LParen, RParen, LBrace, RBrace, LBracket, RBracket,

    Eof,
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
            Token::Import => write!(f, "import"),
            Token::Loop => write!(f, "loop"),
            Token::Break => write!(f, "break"),
            Token::Continue => write!(f, "continue"),
            _ => write!(f, "{:?}", self),
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
                while let Some(ch) = self.peek() {
                    if ch == '\n' { break; }
                    self.advance();
                }
            } else if ch == '/' && self.peek_next() == Some('*') {
                self.advance();
                self.advance();
                let mut depth = 1;
                while depth > 0 {
                    match self.peek() {
                        Some('*') if self.peek_next() == Some('/') => {
                            self.advance(); self.advance(); depth -= 1;
                        }
                        Some('/') if self.peek_next() == Some('*') => {
                            self.advance(); self.advance(); depth += 1;
                        }
                        Some(_) => { self.advance(); }
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
                'n' => '\n', 't' => '\t', 'r' => '\r',
                '\\' => '\\', '\'' => '\'', '0' => '\0',
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

        // Hex literal
        if self.peek() == Some('x') || self.peek() == Some('X') {
            self.advance(); // skip x
            while let Some(ch) = self.peek() {
                if ch.is_ascii_hexdigit() { self.advance(); } else { break; }
            }
            let s: String = self.source[start..self.pos].iter().collect();
            let hex_str = s.trim_start_matches("0x").trim_start_matches("0X");
            return Token::Integer(i64::from_str_radix(hex_str, 16).unwrap_or(0));
        }

        while let Some(ch) = self.peek() {
            if ch.is_ascii_digit() {
                self.advance();
            } else if ch == '.' && !is_float {
                if self.peek_next() == Some('.') { break; }
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
            "let" => Token::Let, "mut" => Token::Mut, "fn" => Token::Fn,
            "return" => Token::Return, "if" => Token::If, "else" => Token::Else,
            "while" => Token::While, "for" => Token::For, "in" => Token::In,
            "match" => Token::Match, "struct" => Token::Struct, "enum" => Token::Enum,
            "impl" => Token::Impl, "trait" => Token::Trait, "import" => Token::Import,
            "as" => Token::As, "pub" => Token::Pub, "priv" => Token::Priv,
            "async" => Token::Async, "await" => Token::Await, "loop" => Token::Loop,
            "break" => Token::Break, "continue" => Token::Continue,
            "self" => Token::Self_, "null" => Token::Null,
            "typeof" => Token::Typeof, "sizeof" => Token::Sizeof,
            "test" => Token::Test,
            "true" => Token::Bool(true), "false" => Token::Bool(false),
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
                tokens.push(Spanned { value: Token::Eof, line, col, len: 0 });
                break;
            };
            let token = match ch {
                '\n' => continue,
                '+' => if self.peek() == Some('=') { self.advance(); Token::PlusEq } else { Token::Plus },
                '-' => if self.peek() == Some('>') { self.advance(); Token::Arrow }
                       else if self.peek() == Some('=') { self.advance(); Token::MinusEq }
                       else { Token::Minus },
                '*' => if self.peek() == Some('=') { self.advance(); Token::StarEq } else { Token::Star },
                '/' => if self.peek() == Some('=') { self.advance(); Token::SlashEq } else { Token::Slash },
                '%' => Token::Percent, '^' => Token::Caret,
                '&' => if self.peek() == Some('&') { self.advance(); Token::AmpAmp } else { Token::Amp },
                '|' => if self.peek() == Some('|') { self.advance(); Token::PipePipe } else { Token::Pipe },
                '~' => Token::Tilde,
                '!' => if self.peek() == Some('=') { self.advance(); Token::Ne } else { Token::Bang },
                '=' => if self.peek() == Some('=') { self.advance(); Token::EqEq }
                       else if self.peek() == Some('>') { self.advance(); Token::FatArrow }
                       else { Token::Eq },
                '<' => if self.peek() == Some('=') { self.advance(); Token::Le }
                       else if self.peek() == Some('<') { self.advance(); Token::Shl }
                       else { Token::Lt },
                '>' => if self.peek() == Some('=') { self.advance(); Token::Ge }
                       else if self.peek() == Some('>') { self.advance(); Token::Shr }
                       else { Token::Gt },
                '.' => if self.peek() == Some('.') { self.advance(); Token::DotDot } else { Token::Dot },
                '?' => Token::Question,
                ':' => if self.peek() == Some(':') { self.advance(); Token::ColonColon } else { Token::Colon },
                ';' => Token::Semicolon, ',' => Token::Comma,
                '(' => Token::LParen, ')' => Token::RParen,
                '{' => Token::LBrace, '}' => Token::RBrace,
                '[' => Token::LBracket, ']' => Token::RBracket,
                '"' => self.read_string()?,
                '\'' => self.read_char()?,
                c if c.is_ascii_digit() => self.read_number(),
                c if c.is_alphabetic() || c == '_' => self.read_ident(),
                _ => return Err(format!("Unexpected character: '{}'", ch)),
            };
            let len = self.col - col + 1;
            tokens.push(Spanned { value: token, line, col, len });
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
        assert_eq!(tokens.len(), 5);
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
        assert_eq!(tokens.len(), 10);
    }

    #[test]
    fn test_true_false() {
        let mut lexer = Lexer::new("true false");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].value, Token::Bool(true));
        assert_eq!(tokens[1].value, Token::Bool(false));
    }

    #[test]
    fn test_logical_operators() {
        let mut lexer = Lexer::new("&& ||");
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0].value, Token::AmpAmp);
        assert_eq!(tokens[1].value, Token::PipePipe);
    }
}
