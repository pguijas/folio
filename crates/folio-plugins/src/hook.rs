//! The `Plugin` trait: the hooks a built-in implements, in the pipeline's
//! call order, plus `PluginDocument` and `ChangeKind`.

use std::path::{Path, PathBuf};

use folio_config::DocsConfig;
use serde_json::{Map, Value};

use crate::builder::AssetBuilder;
use crate::error::PluginError;
use crate::registry::ExtensionRegistry;
use crate::Diagnostics;

/// A Markdown/MDX source a plugin contributes to the normal page pipeline.
/// `unlisted` delists it from the sidebar and nothing else.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PluginDocument {
    pub source: PathBuf,
    /// Clean relative route (`reports/quality`); no index collapsing.
    pub route: String,
    pub unlisted: bool,
}

/// A watched-path event.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ChangeKind {
    Added,
    Modified,
    Deleted,
}

/// A compiled-in integration. Every method has an inert default; the host
/// calls them in this order: `config_keys`, `configure`, `register_extensions`,
/// `collect_docs`, `emit_assets`, `watch_paths`/`on_watched_change`, `post_build`.
#[allow(unused_variables)]
pub trait Plugin {
    /// The label every error and warning names (`Plugin '<name>' failed ...`).
    /// Owned, not `&'static str`: a plugin that arrives from outside the
    /// binary learns its own name at runtime.
    fn name(&self) -> String;

    /// Top-level docs.yaml keys this plugin owns. Owned for the same reason.
    fn config_keys(&self) -> Vec<String> {
        Vec::new()
    }

    /// Read the raw docs.yaml mapping, write the normalized section into
    /// `config.extra`. Fail fast.
    fn configure(
        &self,
        config: &mut DocsConfig,
        raw: &Map<String, Value>,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        Ok(())
    }

    /// Markdown sources for the page pipeline. Fail fast.
    fn collect_docs(&self, config: &DocsConfig) -> Result<Vec<PluginDocument>, PluginError> {
        Ok(Vec::new())
    }

    /// Components, layouts, data modules and views. Fail fast.
    fn register_extensions(
        &self,
        registry: &mut ExtensionRegistry,
        config: &DocsConfig,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        Ok(())
    }

    /// Generated pages and public files into the prepared workspace. Warn and skip.
    fn emit_assets(
        &self,
        builder: &mut dyn AssetBuilder,
        config: &DocsConfig,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        Ok(())
    }

    /// Directories the watcher should also watch.
    fn watch_paths(&self, config: &DocsConfig) -> Vec<PathBuf> {
        Vec::new()
    }

    /// A change under one of `watch_paths`; `true` when handled. Warn and skip.
    fn on_watched_change(
        &self,
        builder: &mut dyn AssetBuilder,
        config: &DocsConfig,
        path: &Path,
        change: ChangeKind,
        diag: &mut Diagnostics,
    ) -> Result<bool, PluginError> {
        Ok(false)
    }

    /// After the static export was written; `site_dir` is the resolved output
    /// directory. Warn and skip.
    fn post_build(&self, site_dir: &Path, diag: &mut Diagnostics) -> Result<(), PluginError> {
        Ok(())
    }
}
