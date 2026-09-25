//! The failures a Python source can produce, named after the CPython exceptions
//! they stand for (`SyntaxError`, `RecursionError`, `UnicodeDecodeError`); every
//! one names the file.

use std::fmt;
use std::path::PathBuf;

/// Which CPython exception a `PythonSyntaxError` stands for.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorKind {
    /// `SyntaxError`: the source does not parse or exceeds a tokenizer limit.
    Syntax,
    /// `RecursionError`: an expression nests deeper than the renderer accepts.
    Recursion,
}

/// A source that does not parse; `line` and `column` are 1-based, the column in characters.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PythonSyntaxError {
    pub path: PathBuf,
    pub message: String,
    pub line: u32,
    pub column: u32,
    pub kind: ErrorKind,
}

impl fmt::Display for PythonSyntaxError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{} ({}, line {})",
            self.message,
            self.path.display(),
            self.line
        )
    }
}

impl std::error::Error for PythonSyntaxError {}

/// Reading or parsing one file failed.
#[derive(Debug)]
pub enum ParseError {
    /// The file could not be read.
    Io {
        path: PathBuf,
        source: std::io::Error,
    },
    /// The bytes `start..end` are not UTF-8.
    Decode {
        path: PathBuf,
        start: usize,
        end: usize,
    },
    /// The source does not parse; the error names the file.
    Syntax(PythonSyntaxError),
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParseError::Io { path, source } => write!(f, "{source}: {}", path.display()),
            ParseError::Decode { path, start, end } => write!(
                f,
                "'utf-8' codec can't decode bytes {start}..{end} in {}",
                path.display()
            ),
            ParseError::Syntax(err) => err.fmt(f),
        }
    }
}

impl std::error::Error for ParseError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ParseError::Io { source, .. } => Some(source),
            ParseError::Decode { .. } => None,
            ParseError::Syntax(err) => Some(err),
        }
    }
}

impl From<PythonSyntaxError> for ParseError {
    fn from(err: PythonSyntaxError) -> Self {
        ParseError::Syntax(err)
    }
}

#[cfg(test)]
#[path = "error_tests.rs"]
mod tests;
