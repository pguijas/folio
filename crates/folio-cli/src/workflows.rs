//! The two GitHub Actions workflows `folio init` writes:
//! the production deploy and the branch previews, with the binary installed
//! by the `install.sh` one-liner and run as bare `folio` commands.

/// `.github/workflows/pages.yml`: the production deploy.
pub const FOLIO_PAGES_WORKFLOW: &str = include_str!("workflows/pages.yml");
/// `.github/workflows/branch-previews.yml`: the pull request previews.
pub const FOLIO_BRANCH_PREVIEW_WORKFLOW: &str = include_str!("workflows/branch-previews.yml");

/// Relative path and content, in the order `folio init` writes them.
pub fn github_pages_workflows() -> [(&'static str, &'static str); 2] {
    [
        (".github/workflows/pages.yml", FOLIO_PAGES_WORKFLOW),
        (
            ".github/workflows/branch-previews.yml",
            FOLIO_BRANCH_PREVIEW_WORKFLOW,
        ),
    ]
}

#[cfg(test)]
mod tests;
