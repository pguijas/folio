//! The one error enum of the crate; every variant's `Display` is the user-facing text.

/// What stops a Docs build in this crate: a source that does not parse, a
/// docs directory that cannot be read, or two modules claiming one page.
#[derive(Debug, thiserror::Error)]
pub enum DocsError {
    /// A Python source file failed to read or parse; the message names the file.
    #[error(transparent)]
    Parse(#[from] folio_lang_python::ParseError),
    /// A JavaScript source file failed to read or parse; it names the file.
    #[error(transparent)]
    ParseJavaScript(#[from] folio_lang_javascript::ParseError),
    /// A Rust source file failed to read or parse; the message names the file.
    #[error(transparent)]
    ParseRust(#[from] folio_lang_rust::ParseError),
    /// A Markdown page or docs directory could not be read.
    #[error(transparent)]
    Markdown(#[from] folio_mdx::MdxError),
    /// Two modules (`foo.py` beside `foo/`) publish the same page; the owners
    /// are their source files. Same shape as the documentation route collision.
    #[error("Documentation route collision at public route '{route}': '{route}' ({first}) and '{route}' ({second})")]
    RouteCollision {
        route: String,
        first: String,
        second: String,
    },
}
