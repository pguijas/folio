//! The `components:` docs.yaml key: directory entries and named specs become
//! config-origin components.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use folio_config::DocsConfig;
use serde_json::Value;

use crate::error::PluginsError;
use crate::msgfmt::truthy;
use crate::registry::{is_js_identifier, ComponentDefinition, ComponentOrigin, ExtensionRegistry};
use crate::Diagnostics;

struct Spec {
    name: String,
    source: PathBuf,
    export: String,
    expose_mdx: bool,
}

/// Directory entries expand first (sorted top-level `.tsx`/`.jsx` files),
/// then named specs register; both share one import-stem deduplication.
pub fn register_config_components(
    registry: &mut ExtensionRegistry,
    config: &DocsConfig,
    diag: &mut Diagnostics,
) -> Result<(), PluginsError> {
    let mut specs = component_dir_specs(&config.project_dir, &config.components.dirs, diag)?;
    for spec in &config.components.specs {
        let source = spec.from.clone().or_else(|| match spec.rest.get("path") {
            Some(Value::String(path)) => Some(path.clone()),
            _ => None,
        });
        let (Some(name), Some(source)) = (spec.name.clone(), source) else {
            return Err(PluginsError::ComponentSpecFields);
        };
        if spec.rest.contains_key("export") {
            return Err(PluginsError::ComponentExport(name));
        }
        let expose_mdx = spec.expose_mdx.as_ref().is_none_or(truthy);
        specs.push(Spec {
            export: spec.export.clone().unwrap_or_else(|| name.clone()),
            name,
            source: PathBuf::from(source),
            expose_mdx,
        });
    }

    let stem = |path: &Path| {
        path.file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .into_owned()
    };
    let mut used = BTreeSet::new();
    for spec in &specs {
        let source_stem = stem(&spec.source);
        let duplicates = specs
            .iter()
            .filter(|s| stem(&s.source) == source_stem)
            .count()
            > 1;
        let import_stem = component_import_stem(&source_stem, &spec.name, duplicates, &mut used);
        registry.register_component(
            ComponentDefinition {
                export_name: Some(spec.export.clone()),
                expose_mdx: spec.expose_mdx,
                source_path: Some(spec.source.clone()),
                origin: ComponentOrigin::Config,
                ..ComponentDefinition::new(
                    &spec.name,
                    &format!("@/components/__folio_components/{import_stem}"),
                )
            },
            diag,
        )?;
    }
    Ok(())
}

fn component_dir_specs(
    project_dir: &Path,
    dirs: &[String],
    diag: &mut Diagnostics,
) -> Result<Vec<Spec>, PluginsError> {
    let mut specs = Vec::new();
    for raw_dir in dirs {
        let directory = project_dir.join(raw_dir);
        if !directory.is_dir() {
            return Err(PluginsError::ComponentDirNotFound(directory));
        }
        let mut files: Vec<PathBuf> = std::fs::read_dir(&directory)
            .map_err(|_| PluginsError::ComponentDirNotFound(directory.clone()))?
            .filter_map(|entry| entry.ok().map(|e| e.path()))
            .filter(|path| {
                path.is_file()
                    && matches!(
                        path.extension().and_then(|e| e.to_str()),
                        Some("tsx" | "jsx")
                    )
            })
            .collect();
        files.sort();
        if files.is_empty() {
            diag.push(format!(
                "Component directory contains no .tsx/.jsx files: {}",
                directory.display()
            ));
            continue;
        }
        for path in files {
            let name =
                component_name_from_stem(&path.file_stem().unwrap_or_default().to_string_lossy());
            if !is_js_identifier(&name) {
                return Err(PluginsError::ComponentNameFromFile(path));
            }
            specs.push(Spec {
                export: name.clone(),
                name,
                source: path,
                expose_mdx: true,
            });
        }
    }
    Ok(specs)
}

/// `hero` -> `Hero`, `my-chart` -> `MyChart`: split on non-alphanumerics,
/// upper-case each part's first character, join.
pub fn component_name_from_stem(stem: &str) -> String {
    stem.split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|part| !part.is_empty())
        .map(|part| {
            let mut chars = part.chars();
            let first = chars
                .next()
                .map(|c| c.to_ascii_uppercase())
                .unwrap_or_default();
            format!("{first}{}", chars.as_str())
        })
        .collect()
}

/// `stem`, or `stem-Segment` when the stem repeats or is taken, then
/// `stem-Segment-2`, `-3`, ... until free.
fn component_import_stem(
    source_stem: &str,
    component_name: &str,
    duplicate_source_stem: bool,
    used: &mut BTreeSet<String>,
) -> String {
    let segment = component_file_segment(component_name);
    let base = if duplicate_source_stem {
        format!("{source_stem}-{segment}")
    } else {
        source_stem.to_string()
    };
    let mut candidate = base.clone();
    if used.contains(&candidate) {
        candidate = format!("{base}-{segment}");
    }
    let mut index = 2;
    while used.contains(&candidate) {
        candidate = format!("{base}-{segment}-{index}");
        index += 1;
    }
    used.insert(candidate.clone());
    candidate
}

fn component_file_segment(value: &str) -> String {
    let segment: String = value
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '_' || c == '-' {
                c
            } else {
                '_'
            }
        })
        .collect();
    let segment = segment.trim_matches('_');
    if segment.is_empty() {
        "component".to_string()
    } else {
        segment.to_string()
    }
}

#[cfg(test)]
#[path = "config_components_tests.rs"]
mod tests;
