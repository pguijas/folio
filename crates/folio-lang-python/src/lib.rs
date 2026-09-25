//! Python source to `ModuleIR`: discovery under the configured roots, module naming,
//! `__all__` visibility, the ruff parse with CPython's limits, `ast.unparse`-compatible
//! rendering, and the docstring merge into arguments, returns and raises.

pub mod discover;
pub mod error;
pub mod extract;
pub mod finalize;
pub mod raw;
pub mod unparse;

use std::path::Path;

pub use discover::{discover, is_import_root, module_name, SourceFile};
pub use error::{ErrorKind, ParseError, PythonSyntaxError};
pub use extract::parse_source_raw;
pub use finalize::finalize_module;
pub use folio_ir::docstring::DocstringStyle;
pub use folio_ir::excludes::is_excluded;
pub use raw::{ArgRaw, ClassRaw, FunctionRaw, ModuleRaw, VarRaw};

use folio_ir::ModuleIR;

/// Parse one file's source. `root` is the configured source root the file was
/// discovered under and names the module; `source_file` is `path.display()`.
pub fn parse_module(
    path: &Path,
    source: &str,
    root: &Path,
    style: DocstringStyle,
) -> Result<ModuleIR, PythonSyntaxError> {
    let name = module_name(path, root);
    let raw = parse_source_raw(source, &name, &path.display().to_string())?;
    Ok(finalize_module(raw, style))
}

/// Read the file as UTF-8 and parse it; a missing or undecodable file names its path.
pub fn parse_file(path: &Path, root: &Path, style: DocstringStyle) -> Result<ModuleIR, ParseError> {
    let bytes = std::fs::read(path).map_err(|source| ParseError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    let source = String::from_utf8(bytes).map_err(|err| {
        let start = err.utf8_error().valid_up_to();
        let end = err
            .utf8_error()
            .error_len()
            .map_or(err.as_bytes().len(), |len| start + len);
        ParseError::Decode {
            path: path.to_path_buf(),
            start,
            end,
        }
    })?;
    parse_module(path, &source, root, style).map_err(ParseError::Syntax)
}
