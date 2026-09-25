//! `ConfigError` (one message per field) and `Loaded`, what a loader returns.

use std::path::PathBuf;

/// One error message per field: loading stops at the first invalid field and
/// the message names that field. `Display` is the exact user-facing sentence.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ConfigError {
    /// `docs.yaml` is missing.
    #[error("Config file not found: {}", .0.display())]
    NotFound(PathBuf),
    /// I/O or UTF-8 failure while reading the file; the OS error text.
    #[error("{0}")]
    Read(String),
    /// YAML syntax error (duplicate keys included) or a non-mapping document.
    #[error("{0}")]
    Yaml(String),
    /// A field-specific validation failure; `message` already names the field.
    #[error("{message}")]
    Field { field: String, message: String },
}

impl ConfigError {
    /// A `Field` error for the dotted key `field`.
    pub fn field(field: impl Into<String>, message: impl Into<String>) -> Self {
        ConfigError::Field {
            field: field.into(),
            message: message.into(),
        }
    }
}

/// The typed config, every warning raised while loading (emission order) and
/// the raw top-level mapping, so the built-in integrations can read their own
/// section and the cross-section guards can see siblings.
#[derive(Debug, Clone)]
pub struct Loaded<T> {
    pub config: T,
    pub warnings: Vec<String>,
    pub raw: serde_json::Map<String, serde_json::Value>,
}
