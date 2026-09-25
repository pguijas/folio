//! Test doubles other crates' tests share: a `DocsConfig` from YAML text and
//! an in-memory `AssetBuilder`.

use std::path::Path;

use folio_config::DocsConfig;

/// Parse `yaml` as a `docs.yaml` anchored at `project_dir`; panics on an
/// invalid config (tests hand it valid text).
pub fn docs_config(yaml: &str, project_dir: &Path) -> DocsConfig {
    let mapping: serde_yaml_ng::Value = serde_yaml_ng::from_str(yaml).expect("valid yaml");
    let mapping = match mapping {
        serde_yaml_ng::Value::Mapping(m) => m,
        serde_yaml_ng::Value::Null => serde_yaml_ng::Mapping::new(),
        _ => panic!("docs.yaml must be a mapping"),
    };
    folio_config::parse_docs_config_with(&mapping, project_dir, "", &mut Vec::new())
        .expect("valid docs.yaml")
}

use std::collections::{BTreeMap, BTreeSet};
use std::path::PathBuf;

use crate::builder::AssetBuilder;
use crate::error::PluginError;

/// An `AssetBuilder` over maps: pages, routes, `_meta.ts` texts, static
/// assets and LLM files, with the order of page writes recorded.
#[derive(Debug, Default)]
pub struct MemoryBuilder {
    pub build_dir: PathBuf,
    pub output_dir: PathBuf,
    pub pages: BTreeMap<String, String>,
    /// Routes of every `write_page`, in call order.
    pub written_pages: Vec<String>,
    pub routes: BTreeSet<String>,
    pub meta: BTreeMap<String, String>,
    pub static_assets: BTreeMap<String, PathBuf>,
    pub llm_files: Option<(Option<String>, Option<String>)>,
}

impl MemoryBuilder {
    /// A builder with these `_meta.ts` texts already present.
    pub fn with_meta<const N: usize>(meta: [(&str, &str); N]) -> Self {
        MemoryBuilder {
            meta: meta
                .into_iter()
                .map(|(k, v)| (k.to_string(), v.to_string()))
                .collect(),
            ..Self::default()
        }
    }

    /// A builder with these pages already on disk.
    pub fn with_pages<const N: usize>(pages: [(&str, &str); N]) -> Self {
        MemoryBuilder {
            pages: pages
                .into_iter()
                .map(|(k, v)| (k.to_string(), v.to_string()))
                .collect(),
            ..Self::default()
        }
    }
}

impl AssetBuilder for MemoryBuilder {
    fn build_dir(&self) -> &Path {
        &self.build_dir
    }
    fn output_dir(&self) -> &Path {
        &self.output_dir
    }
    fn page_exists(&self, route: &str) -> Result<bool, PluginError> {
        Ok(self.pages.contains_key(route))
    }
    fn read_page(&self, route: &str) -> Result<String, PluginError> {
        self.pages
            .get(route)
            .cloned()
            .ok_or_else(|| format!("no page at {route}").into())
    }
    fn write_page(&mut self, route: &str, mdx: &str) -> Result<(), PluginError> {
        self.written_pages.push(route.to_string());
        self.pages.insert(route.to_string(), mdx.to_string());
        self.routes.insert(route.to_string());
        Ok(())
    }
    fn remove_page(&mut self, route: &str) -> Result<(), PluginError> {
        self.pages.remove(route);
        Ok(())
    }
    fn list_pages(&self, prefix: &str) -> Result<Vec<String>, PluginError> {
        Ok(self
            .pages
            .keys()
            .filter(|r| r.starts_with(prefix))
            .cloned()
            .collect())
    }
    fn register_route(&mut self, route: &str) {
        self.routes.insert(route.to_string());
    }
    fn emitted_routes(&self) -> BTreeSet<String> {
        self.routes.clone()
    }
    fn restore_emitted_routes(&mut self, snapshot: BTreeSet<String>) {
        self.routes = snapshot;
    }
    fn copy_static_asset(&mut self, relative: &str, source: &Path) -> Result<(), PluginError> {
        self.static_assets
            .insert(relative.to_string(), source.to_path_buf());
        Ok(())
    }
    fn remove_static_tree(&mut self, relative: &str) -> Result<(), PluginError> {
        self.static_assets
            .retain(|k, _| k != relative && !k.starts_with(&format!("{relative}/")));
        Ok(())
    }
    fn write_meta(&mut self, directory: &str, meta_ts: &str) -> Result<(), PluginError> {
        self.meta.insert(directory.to_string(), meta_ts.to_string());
        Ok(())
    }
    fn read_meta(&self, directory: &str) -> Result<String, PluginError> {
        Ok(self.meta.get(directory).cloned().unwrap_or_default())
    }
    fn write_llm_files(
        &mut self,
        llms_txt: Option<&str>,
        llms_full_txt: Option<&str>,
    ) -> Result<(), PluginError> {
        self.llm_files = Some((llms_txt.map(String::from), llms_full_txt.map(String::from)));
        Ok(())
    }
}
