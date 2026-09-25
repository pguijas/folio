//! Generic Markdown to MDX and back: reading `.md` pages with frontmatter,
//! title and description inference, README to `index` routing, MDX escaping
//! and sanitising, mermaid fences, and the lossy MDX to Markdown mirror.
//! No IR, no file writing, no component contract (those belong to
//! `folio-docs`, `folio-site` and `folio-plugins`).

pub mod escape;
pub mod frontmatter;
pub mod mirror;
pub mod page;
pub mod sanitize;

pub use escape::{
    code_fence_flags, escape_curly_outside_math, escape_jsx_attr, escape_mdx, escape_mdx_text,
};
pub use frontmatter::{render_frontmatter, split_frontmatter, Frontmatter};
pub use mirror::mdx_to_markdown;
pub use page::{
    extract_first_paragraph, parse_markdown_directory, parse_markdown_file, source_route,
    DirectoryScan, MarkdownPage, RST_WARNING,
};
pub use sanitize::{convert_mermaid_blocks, markdown_to_mdx, sanitize_for_mdx};

use std::path::PathBuf;

/// Errors reading Markdown pages from disk.
#[derive(Debug, thiserror::Error)]
pub enum MdxError {
    /// The file or directory could not be read.
    #[error("{}: {source}", path.display())]
    Io {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    /// The frontmatter block is not a YAML mapping with string keys.
    #[error("{}: invalid frontmatter: {source}", path.display())]
    Frontmatter {
        path: PathBuf,
        #[source]
        source: serde_yaml_ng::Error,
    },
}

/// Compiles one of the crate's fixed patterns.
pub(crate) fn re(pattern: &str) -> regex::Regex {
    regex::Regex::new(pattern).expect("static pattern")
}
