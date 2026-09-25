//! `PluginHost`: the ordered built-in set, hook dispatch with the two failure
//! policies, document validation and the route-collision check.

use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

use folio_config::DocsConfig;
use folio_mdx::MarkdownPage;
use serde_json::{Map, Value};

use crate::builder::AssetBuilder;
use crate::builtins::{register_builtin_components, register_builtin_extensions};
use crate::config_components::register_config_components;
use crate::error::{PluginError, PluginsError};
use crate::hook::{ChangeKind, Plugin, PluginDocument};
use crate::msgfmt::quoted;
use crate::registry::ExtensionRegistry;
use crate::Diagnostics;

/// The plugins of a build, dispatched in insertion order.
#[derive(Default)]
pub struct PluginHost {
    plugins: Vec<Box<dyn Plugin>>,
}

fn hook_error(plugin: &dyn Plugin, hook_name: &'static str, source: PluginError) -> PluginsError {
    PluginsError::Hook {
        plugin_label: plugin.name().to_string(),
        hook_name,
        source,
    }
}

fn skipped(plugin: &dyn Plugin, hook_name: &str, error: &PluginError) -> String {
    format!(
        "Plugin '{}' failed in hook '{hook_name}': {error} (skipped)",
        plugin.name()
    )
}

impl PluginHost {
    /// The compiled-in built-ins in dispatch order: landing, roadmap, openapi.
    pub fn builtin() -> Self {
        let mut host = PluginHost::default();
        host.push(Box::new(crate::landing::LandingPlugin));
        host.push(Box::new(crate::roadmap::RoadmapPlugin));
        host.push(Box::new(crate::openapi::OpenApiPlugin));
        host
    }

    /// Append a plugin after the built-ins.
    pub fn push(&mut self, plugin: Box<dyn Plugin>) {
        self.plugins.push(plugin);
    }

    /// The plugins in dispatch order.
    pub fn plugins(&self) -> &[Box<dyn Plugin>] {
        &self.plugins
    }

    /// The sorted, de-duplicated union of every plugin's `config_keys()`.
    pub fn config_keys(&self) -> BTreeSet<String> {
        self.plugins.iter().flat_map(|p| p.config_keys()).collect()
    }

    /// Fail fast: the first failing plugin aborts.
    pub fn configure(
        &self,
        config: &mut DocsConfig,
        raw: &Map<String, Value>,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginsError> {
        for plugin in &self.plugins {
            plugin
                .configure(config, raw, diag)
                .map_err(|e| hook_error(plugin.as_ref(), "configure", e))?;
        }
        Ok(())
    }

    /// Fail fast; every document is validated and parsed, results in plugin order.
    pub fn collect_docs(&self, config: &DocsConfig) -> Result<Vec<MarkdownPage>, PluginsError> {
        let mut pages = Vec::new();
        for plugin in &self.plugins {
            let documents = plugin
                .collect_docs(config)
                .map_err(|e| hook_error(plugin.as_ref(), "collect_docs", e))?;
            for document in documents {
                pages.push(parse_plugin_document(&document)?);
            }
        }
        Ok(pages)
    }

    /// Fail fast.
    pub fn register_extensions(
        &self,
        registry: &mut ExtensionRegistry,
        config: &DocsConfig,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginsError> {
        for plugin in &self.plugins {
            plugin
                .register_extensions(registry, config, diag)
                .map_err(|e| hook_error(plugin.as_ref(), "register_extensions", e))?;
        }
        Ok(())
    }

    /// Warn and skip; a failing plugin's registered routes are rolled back
    /// (pages already written stay) before dispatch continues.
    pub fn emit_assets(
        &self,
        builder: &mut dyn AssetBuilder,
        config: &DocsConfig,
        diag: &mut Diagnostics,
    ) {
        for plugin in &self.plugins {
            let snapshot = builder.emitted_routes();
            if let Err(error) = plugin.emit_assets(builder, config, diag) {
                builder.restore_emitted_routes(snapshot);
                diag.push(skipped(plugin.as_ref(), "emit_assets", &error));
            }
        }
    }

    /// Every plugin's `watch_paths` that is an existing directory, in dispatch order.
    pub fn watch_dirs(&self, config: &DocsConfig) -> Vec<PathBuf> {
        self.plugins
            .iter()
            .flat_map(|p| p.watch_paths(config))
            .filter(|path| path.is_dir())
            .collect()
    }

    /// Warn and skip; `true` when any plugin handled the change.
    pub fn dispatch_change(
        &self,
        builder: &mut dyn AssetBuilder,
        config: &DocsConfig,
        path: &Path,
        change: ChangeKind,
        diag: &mut Diagnostics,
    ) -> bool {
        let mut handled = false;
        for plugin in &self.plugins {
            match plugin.on_watched_change(builder, config, path, change, diag) {
                Ok(result) => handled |= result,
                Err(error) => diag.push(skipped(plugin.as_ref(), "on_watched_change", &error)),
            }
        }
        handled
    }

    /// Warn and skip.
    pub fn post_build(&self, site_dir: &Path, diag: &mut Diagnostics) {
        for plugin in &self.plugins {
            if let Err(error) = plugin.post_build(site_dir, diag) {
                diag.push(skipped(plugin.as_ref(), "post_build", &error));
            }
        }
    }
}

fn parse_plugin_document(document: &PluginDocument) -> Result<MarkdownPage, PluginsError> {
    let route = &document.route;
    let clean = !route.is_empty()
        && !route.starts_with('/')
        && !route.contains('\\')
        && route
            .split('/')
            .all(|segment| !matches!(segment, "" | "." | ".."));
    if !clean {
        return Err(PluginsError::DocumentRoute(quoted(route)));
    }
    let suffix = document
        .source
        .extension()
        .map(|e| e.to_string_lossy().to_lowercase());
    if !matches!(suffix.as_deref(), Some("md" | "mdx")) {
        return Err(PluginsError::DocumentSuffix);
    }
    if !document.source.is_file() {
        return Err(PluginsError::DocumentSourceMissing(document.source.clone()));
    }
    let mut page = folio_mdx::parse_markdown_file(&document.source)?;
    page.route = route.clone();
    page.unlisted = document.unlisted;
    Ok(page)
}

/// The public route two content routes collide on: no trailing `/`, a last
/// `index` segment dropped, `_` to `-` outside `api-reference`.
pub(crate) fn canonical_route(route: &str) -> String {
    let mut segments: Vec<&str> = route.trim_end_matches('/').split('/').collect();
    if segments.len() > 1 && segments.last() == Some(&"index") {
        segments.pop();
    }
    if segments.first() == Some(&"api-reference") {
        segments.join("/")
    } else {
        segments
            .iter()
            .map(|s| s.replace('_', "-"))
            .collect::<Vec<_>>()
            .join("/")
    }
}

/// Over authored then plugin documents: two documents on one public route
/// fail before any page is written.
pub fn check_route_collisions(pages: &[MarkdownPage]) -> Result<(), PluginsError> {
    let owner = |page: &MarkdownPage| {
        if page.source_file.is_empty() {
            "<generated document>".to_string()
        } else {
            page.source_file.clone()
        }
    };
    let mut seen: BTreeMap<String, &MarkdownPage> = BTreeMap::new();
    for page in pages {
        let public = canonical_route(&page.route);
        if let Some(previous) = seen.insert(public.clone(), page) {
            return Err(PluginsError::RouteCollision {
                public: quoted(&public),
                previous_route: quoted(&previous.route),
                previous_owner: owner(previous),
                route: quoted(&page.route),
                owner: owner(page),
            });
        }
    }
    Ok(())
}

/// The registry of a build: the public layout, the builtin components, the
/// `components:` entries, then every plugin's `register_extensions`. Fail fast.
pub fn build_registry(
    host: &PluginHost,
    config: &DocsConfig,
    diag: &mut Diagnostics,
) -> Result<ExtensionRegistry, PluginsError> {
    let mut registry = ExtensionRegistry::default();
    register_builtin_extensions(&mut registry)?;
    register_builtin_components(&mut registry)?;
    register_config_components(&mut registry, config, diag)?;
    host.register_extensions(&mut registry, config, diag)?;
    Ok(registry)
}

#[cfg(test)]
#[path = "host_tests.rs"]
mod tests;
