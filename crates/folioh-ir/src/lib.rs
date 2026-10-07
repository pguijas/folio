//! The language-neutral IR every parser produces and every renderer consumes:
//! `ModuleIR` and its parts with the serde shape the Rust golden pins,
//! the Python signature renderer, and the docstring parsers (Google, NumPy,
//! ReST, `auto`) that fill `DocstringIR` and the argument descriptions.

pub mod docstring;
pub mod excludes;
pub mod ir;
pub mod signature;

pub use ir::*;
