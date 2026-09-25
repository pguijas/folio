//! `AssetBuilder`: the write surface a plugin's `emit_assets` and
//! `on_watched_change` use.
//! `folio-site`'s `SiteBuilder` implements it; `testing::MemoryBuilder` is
//! the in-memory double.

use std::collections::BTreeSet;
use std::path::Path;

use crate::error::PluginError;

/// Routes are `content/` paths without `.mdx` (`roadmap`, `api-reference/http`).
pub trait AssetBuilder {
    /// The template workspace (`.build/`).
    fn build_dir(&self) -> &Path;
    /// The export directory (`_site/`).
    fn output_dir(&self) -> &Path;
    fn page_exists(&self, route: &str) -> Result<bool, PluginError>;
    fn read_page(&self, route: &str) -> Result<String, PluginError>;
    /// Writes the MDX page and its Markdown mirror, and registers the route.
    fn write_page(&mut self, route: &str, mdx: &str) -> Result<(), PluginError>;
    fn remove_page(&mut self, route: &str) -> Result<(), PluginError>;
    fn list_pages(&self, prefix: &str) -> Result<Vec<String>, PluginError>;
    /// Declare a route live (a valid link target) without writing it.
    fn register_route(&mut self, route: &str);
    fn emitted_routes(&self) -> BTreeSet<String>;
    /// The rollback after a failed `emit_assets` (routes only, never files).
    fn restore_emitted_routes(&mut self, snapshot: BTreeSet<String>);
    fn copy_static_asset(&mut self, relative: &str, source: &Path) -> Result<(), PluginError>;
    fn remove_static_tree(&mut self, relative: &str) -> Result<(), PluginError>;
    /// `directory` is `""` for the content root.
    fn write_meta(&mut self, directory: &str, meta_ts: &str) -> Result<(), PluginError>;
    /// `""` when the directory has no `_meta.ts`.
    fn read_meta(&self, directory: &str) -> Result<String, PluginError>;
    fn write_llm_files(
        &mut self,
        llms_txt: Option<&str>,
        llms_full_txt: Option<&str>,
    ) -> Result<(), PluginError>;
}
