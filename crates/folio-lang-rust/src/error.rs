//! The failures a Rust source can produce; every one names the file. Same
//! surface as the Python reader's, so the CLI reports both the same way.

use std::path::PathBuf;

/// A source that does not parse; `line` and `column` are 1-based.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("{message} ({}, line {line})", path.display())]
pub struct RustSyntaxError {
    pub path: PathBuf,
    pub message: String,
    pub line: u32,
    pub column: u32,
}

/// Reading or parsing one file failed.
#[derive(Debug, thiserror::Error)]
pub enum ParseError {
    /// The file could not be read.
    #[error("{source}: {}", path.display())]
    Io {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    /// The bytes `start..end` are not UTF-8.
    #[error("'utf-8' codec can't decode bytes {start}..{end} in {}", path.display())]
    Decode {
        path: PathBuf,
        start: usize,
        end: usize,
    },
    /// The source does not parse; the error names the file.
    #[error(transparent)]
    Syntax(#[from] RustSyntaxError),
}
