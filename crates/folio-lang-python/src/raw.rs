//! The extraction output before docstrings are parsed.
//! `ModuleIR` is the serialised shape; these never leave the crate as JSON.

use folio_ir::{ArgKind, FunctionKind};

/// One parameter before the docstring merge.
#[derive(Debug, Clone, PartialEq)]
pub struct ArgRaw {
    pub name: String,
    /// `unparse(annotation)` or `""`.
    pub annotation: String,
    pub default: Option<String>,
    pub kind: ArgKind,
}

/// A function or method with its docstring still unparsed.
#[derive(Debug, Clone, PartialEq)]
pub struct FunctionRaw {
    pub name: String,
    pub args: Vec<ArgRaw>,
    pub returns_annotation: String,
    pub decorators: Vec<String>,
    /// The `cleandoc`'ed docstring, `None` when the body has none.
    pub docstring_raw: Option<String>,
    pub is_async: bool,
    pub source_file: String,
    pub line_number: u32,
    pub kind: FunctionKind,
}

/// A module constant or class variable.
#[derive(Debug, Clone, PartialEq)]
pub struct VarRaw {
    pub name: String,
    pub var_type: String,
    pub value: String,
}

/// A class, recursively.
#[derive(Debug, Clone, PartialEq)]
pub struct ClassRaw {
    pub name: String,
    pub bases: Vec<String>,
    pub decorators: Vec<String>,
    pub docstring_raw: Option<String>,
    pub methods: Vec<FunctionRaw>,
    pub class_vars: Vec<VarRaw>,
    pub inner_classes: Vec<ClassRaw>,
    pub source_file: String,
    pub line_number: u32,
}

/// One parsed module before finalize.
#[derive(Debug, Clone, PartialEq)]
pub struct ModuleRaw {
    pub name: String,
    pub docstring_raw: Option<String>,
    pub classes: Vec<ClassRaw>,
    pub functions: Vec<FunctionRaw>,
    pub constants: Vec<VarRaw>,
    pub source_file: String,
}
