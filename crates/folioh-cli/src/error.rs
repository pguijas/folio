//! The binary's error type and its exit codes.

use std::fmt;

/// Every failure the binary reports. Usage errors never reach this type:
/// clap prints them and exits 2 on its own.
#[derive(Debug, thiserror::Error)]
pub enum CliError {
    /// `Error: {0}` in red, exit 1: a missing config, bad arguments, a
    /// command that refused to run.
    #[error("Error: {0}")]
    Message(String),
    /// `Build failed: {0}` in red, exit 1: any pipeline failure.
    #[error("Build failed: {0}")]
    Build(String),
    /// Already reported on the console; only the exit code remains.
    #[error("exit {0}")]
    Exit(u8),
}

impl CliError {
    /// An `Error: ...` failure from any displayable text.
    pub fn message(text: impl fmt::Display) -> CliError {
        CliError::Message(text.to_string())
    }

    /// The process exit code for this error.
    pub fn exit_code(&self) -> u8 {
        match self {
            CliError::Exit(code) => *code,
            _ => 1,
        }
    }
}

impl From<std::io::Error> for CliError {
    fn from(err: std::io::Error) -> CliError {
        CliError::Message(err.to_string())
    }
}
