//! JavaScript source to `ModuleIR`: the `.js`, `.mjs` and `.cjs` files under
//! the configured roots and the exported surface of each. The reader holds no
//! state and no configuration beyond the excludes; it parses with tree-sitter,
//! so a file is read without resolving its imports or running its build.

use std::path::Path;

use folio_ir::ModuleIR;

pub mod discover;
pub mod error;
pub mod jsdoc;
pub mod parse;

pub use discover::{discover, module_name, Discovery, SourceFile, EXTENSIONS};
pub use error::{JavaScriptSyntaxError, ParseError};
pub use folio_ir::excludes::is_excluded;
pub use parse::parse_source;

/// Read the file as UTF-8 and parse it; a missing or undecodable file names its
/// path. `root` is the configured source root the file was discovered under; the
/// IR reports the file as discovered, so source links, the incremental manifest
/// and the watcher all name the same path.
pub fn parse_file(path: &Path, root: &Path) -> Result<ModuleIR, ParseError> {
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
    let source_file = path.display().to_string();
    parse_source(&source, &module_name(path, root), &source_file).map_err(|err| {
        ParseError::Syntax(JavaScriptSyntaxError {
            path: path.to_path_buf(),
            ..err
        })
    })
}
