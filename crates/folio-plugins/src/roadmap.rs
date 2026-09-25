//! The roadmap built-in: `roadmap:` normalization, the `Roadmap`/`RoadmapPage`
//! components, `lib/roadmap-data.ts` and `lib/roadmap-projects.ts`, the
//! `/docs/roadmap/` page, the optional `/roadmap/` view and the
//! `folio roadmap` rows.

use folio_config::DocsConfig;
use indexmap::IndexMap;
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};

use crate::builder::AssetBuilder;
use crate::builtins::PUBLIC_LAYOUT;
use crate::error::{PluginError, PluginsError};
use crate::hook::Plugin;
use crate::msgfmt::{as_text, kind, quoted_value, truthy};
use crate::registry::{ComponentDefinition, DataModuleDefinition, ExtensionRegistry, ViewBlock};
use crate::Diagnostics;

/// The group a phase without `project` belongs to (`roadmap-utils.ts` agrees).
pub const DEFAULT_PROJECT: &str = "shared";
/// The per-project presentation fields `projects:` may carry.
pub const PROJECT_FIELDS: [&str; 2] = ["label", "description"];
/// The type block of `lib/roadmap-projects.ts`: the one `RoadmapProject`
/// shape `roadmap-utils.ts` already declares.
pub const ROADMAP_PROJECTS_TYPES: &str =
    "import type { RoadmapProject } from \"@/lib/roadmap-utils\"\n\n";
/// The type block `lib/roadmap-data.ts` starts with; ends with `}\n`.
pub const ROADMAP_TYPES: &str = "export type RoadmapStatus = \"shipped\" | \"active\" | \"next\" | \"later\"\n\n// A feature line is either the sentence on its own, which takes its done\n// state from the phase, or the sentence with its own mark. The second form\n// is what lets a release still in progress show the work already finished.\nexport type RoadmapFeature = string | { text: string; done?: boolean }\n\nexport interface RoadmapPhase {\n  id: string\n  version: string\n  project?: string\n  title: string\n  status: RoadmapStatus\n  layer: string\n  summary: string\n  command?: string\n  features: RoadmapFeature[]\n}\n";

/// `routes.docs` publishes `/docs/roadmap/`, `routes.public` the standalone `/roadmap/`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Routes {
    pub docs: bool,
    pub public: bool,
}

/// The normalized `roadmap:` section, always these four keys in this order.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Roadmap {
    pub routes: Routes,
    /// Phase objects pass through verbatim; the renderer reads `features`.
    pub phases: Vec<Value>,
    pub description: String,
    pub projects: IndexMap<String, IndexMap<String, String>>,
}

/// An inert roadmap: default routes, no phases, no copy, no projects.
pub fn empty_roadmap() -> Roadmap {
    Roadmap {
        routes: Routes {
            docs: true,
            public: false,
        },
        phases: Vec::new(),
        description: String::new(),
        projects: IndexMap::new(),
    }
}

fn normalize_projects(raw: Option<&Value>) -> IndexMap<String, IndexMap<String, String>> {
    let mut projects = IndexMap::new();
    for (key, value) in raw.and_then(Value::as_object).into_iter().flatten() {
        let Some(fields) = value.as_object() else {
            continue;
        };
        let entry: IndexMap<String, String> = PROJECT_FIELDS
            .iter()
            .filter_map(|field| {
                let text = fields.get(*field)?.as_str()?.trim();
                (!text.is_empty()).then(|| (field.to_string(), text.to_string()))
            })
            .collect();
        projects.insert(key.clone(), entry);
    }
    projects
}

/// A non-mapping is the empty roadmap; `routes` are truthiness-coerced,
/// `phases` pass through, `description` is stripped, `projects` keep only
/// their non-empty `label`/`description`.
pub fn normalize_roadmap(raw: &Value) -> Roadmap {
    let Some(map) = raw.as_object() else {
        return empty_roadmap();
    };
    let mut routes = empty_roadmap().routes;
    if let Some(raw_routes) = map.get("routes").and_then(Value::as_object) {
        if let Some(docs) = raw_routes.get("docs") {
            routes.docs = truthy(docs);
        }
        if let Some(public) = raw_routes.get("public") {
            routes.public = truthy(public);
        }
    }
    Roadmap {
        routes,
        phases: map
            .get("phases")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default(),
        description: map
            .get("description")
            .and_then(Value::as_str)
            .map(|s| s.trim().to_string())
            .unwrap_or_default(),
        projects: normalize_projects(map.get("projects")),
    }
}

/// The section `configure` stored, re-normalized; `None` when inactive.
pub fn active_roadmap(config: &DocsConfig) -> Option<Roadmap> {
    config
        .extra
        .get("roadmap")
        .filter(|value| value.is_object())
        .map(normalize_roadmap)
}

/// The statuses `RoadmapStatus` declares.
const PHASE_STATUSES: [&str; 4] = ["shipped", "active", "next", "later"];
/// The keys `RoadmapPhase` declares, in its order.
const PHASE_KEYS: [&str; 9] = [
    "id", "version", "project", "title", "status", "layer", "summary", "command", "features",
];
/// The `RoadmapPhase` strings a phase must carry.
const REQUIRED_PHASE_KEYS: [&str; 6] = ["id", "version", "title", "status", "layer", "summary"];
/// The keys a feature mapping (`RoadmapFeature`) declares.
const FEATURE_KEYS: [&str; 2] = ["text", "done"];

fn shape(path: String, expected: &'static str, got: &Value) -> PluginsError {
    PluginsError::RoadmapShape {
        path,
        expected,
        got: kind(got),
    }
}

/// The first key of `fields` outside `known`, with its did-you-mean.
fn unknown_key(
    fields: &Map<String, Value>,
    known: &[&str],
    path: &str,
    entry: &'static str,
    listed: &'static str,
) -> Result<(), PluginsError> {
    match fields.keys().find(|key| !known.contains(&key.as_str())) {
        Some(key) => Err(PluginsError::RoadmapUnknownKey {
            path: path.to_string(),
            key: key.clone(),
            entry,
            hint: folio_config::did_you_mean(key, known.iter().copied()),
            known: listed,
        }),
        None => Ok(()),
    }
}

/// One `features` entry: a string, or a mapping with a string `text` and an
/// optional boolean `done`.
fn check_feature(path: String, feature: &Value) -> Result<(), PluginsError> {
    let fields = match feature {
        Value::String(_) => return Ok(()),
        Value::Object(fields) => fields,
        other => return Err(shape(path, "a string or a mapping with text", other)),
    };
    unknown_key(fields, &FEATURE_KEYS, &path, "feature", "text and done")?;
    match fields.get("text") {
        None => {
            return Err(PluginsError::RoadmapMissing {
                path: format!("{path}.text"),
                needs: "a feature mapping needs its text",
            })
        }
        Some(Value::String(_)) => {}
        Some(other) => return Err(shape(format!("{path}.text"), "a string", other)),
    }
    match fields.get("done") {
        None | Some(Value::Bool(_)) => Ok(()),
        Some(other) => Err(shape(format!("{path}.done"), "true or false", other)),
    }
}

/// One phase against the `RoadmapPhase` type `lib/roadmap-data.ts` declares.
fn check_phase(path: &str, fields: &Map<String, Value>) -> Result<(), PluginsError> {
    unknown_key(
        fields,
        &PHASE_KEYS,
        path,
        "phase",
        "id, version, project, title, status, layer, summary, command and features",
    )?;
    for key in REQUIRED_PHASE_KEYS {
        if !fields.contains_key(key) {
            return Err(PluginsError::RoadmapMissing {
                path: format!("{path}.{key}"),
                needs: "every phase needs id, version, title, status, layer and summary",
            });
        }
    }
    for (key, value) in fields {
        let key_path = format!("{path}.{key}");
        match (key.as_str(), value) {
            ("features", Value::Null) => {}
            ("features", Value::Array(features)) => {
                for (index, feature) in features.iter().enumerate() {
                    check_feature(format!("{key_path}[{index}]"), feature)?;
                }
            }
            ("features", other) => return Err(shape(key_path, "a list", other)),
            ("status", Value::String(status)) if !PHASE_STATUSES.contains(&status.as_str()) => {
                return Err(PluginsError::RoadmapStatus {
                    hint: folio_config::did_you_mean(status, PHASE_STATUSES),
                    got: quoted_value(value),
                    path: key_path,
                });
            }
            (_, Value::String(_)) => {}
            // `version: 0.3` is a YAML number, and `RoadmapPhase.version` a string.
            ("version", other) => {
                return Err(shape(key_path, "a quoted string, such as \"0.1\"", other))
            }
            (_, other) => return Err(shape(key_path, "a string", other)),
        }
    }
    Ok(())
}

/// `roadmap.phases` in the shape the renderer reads: a list of mappings with
/// the `RoadmapPhase` keys and no others, the required ones present, every
/// field a string except `features`, `status` one of the four statuses, and
/// `features`, when present, a list of strings or `{text, done}` mappings.
/// Anything else fails the build and names the entry; an absent or empty
/// `phases:` is no phases.
pub fn check_phases(section: &Value) -> Result<(), PluginsError> {
    let phases = match section.as_object().and_then(|m| m.get("phases")) {
        None | Some(Value::Null) => return Ok(()),
        Some(Value::Array(phases)) => phases,
        Some(other) => return Err(shape("roadmap.phases".into(), "a list of phases", other)),
    };
    for (index, phase) in phases.iter().enumerate() {
        let path = format!("roadmap.phases[{index}]");
        let Some(fields) = phase.as_object() else {
            return Err(shape(
                path,
                "a mapping with id, version, title, status, layer and summary",
                phase,
            ));
        };
        check_phase(&path, fields)?;
    }
    Ok(())
}

/// The phases as `lib/roadmap-data.ts` carries them: a phase without
/// `features` gets an empty list, the one field the renderer always reads.
pub fn renderable_phases(phases: &[Value]) -> Vec<Value> {
    phases
        .iter()
        .cloned()
        .map(|mut phase| {
            if let Some(fields) = phase.as_object_mut() {
                if fields.get("features").is_none_or(Value::is_null) {
                    fields.insert("features".to_string(), json!([]));
                }
            }
            phase
        })
        .collect()
}

/// The phases `folio roadmap` tabulates; empty when inactive.
pub fn get_phases(config: &DocsConfig) -> Vec<Value> {
    active_roadmap(config).map(|r| r.phases).unwrap_or_default()
}

/// Distinct project keys in first-appearance order; no `project` is `shared`.
pub fn project_keys(phases: &[Value]) -> Vec<String> {
    let mut keys: Vec<String> = Vec::new();
    for phase in phases.iter().filter_map(Value::as_object) {
        let key = phase
            .get("project")
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|k| !k.is_empty())
            .unwrap_or(DEFAULT_PROJECT)
            .to_string();
        if !keys.contains(&key) {
            keys.push(key);
        }
    }
    keys
}

/// Declared `projects:` keys that have phases, in declaration order, then the
/// undeclared ones in appearance order.
pub fn ordered_project_keys(
    phases: &[Value],
    projects: &IndexMap<String, IndexMap<String, String>>,
) -> Vec<String> {
    let present = project_keys(phases);
    let mut ordered: Vec<String> = projects
        .keys()
        .filter(|k| present.contains(*k))
        .cloned()
        .collect();
    ordered.extend(present.into_iter().filter(|k| !projects.contains_key(k)));
    ordered
}

/// `{key: {label, description}}` for the projects the page draws; a project
/// with neither field is left out (the component falls back to the key).
pub fn project_block(roadmap: &Roadmap) -> IndexMap<String, IndexMap<String, String>> {
    ordered_project_keys(&roadmap.phases, &roadmap.projects)
        .into_iter()
        .filter_map(|key| {
            let entry = roadmap.projects.get(&key)?.clone();
            (!entry.is_empty()).then_some((key, entry))
        })
        .collect()
}

/// The generated `/docs/roadmap/` page (write-once).
pub fn docs_page_mdx() -> String {
    "import { Roadmap } from \"@/components/roadmap\"\n\n# Roadmap\n\n<Roadmap />\n".to_string()
}

/// `folio roadmap` rows: project, status, version, title, command.
pub fn table_rows(phases: &[Value]) -> Vec<[String; 5]> {
    phases
        .iter()
        .map(|phase| {
            ["project", "status", "version", "title", "command"].map(|key| {
                phase
                    .as_object()
                    .and_then(|p| p.get(key))
                    .map(as_text)
                    .unwrap_or_default()
            })
        })
        .collect()
}

fn props(pairs: &[(&str, &str)]) -> IndexMap<String, String> {
    pairs
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}

/// Owner of the `roadmap:` key.
pub struct RoadmapPlugin;

impl Plugin for RoadmapPlugin {
    fn name(&self) -> String {
        "roadmap".to_string()
    }

    fn config_keys(&self) -> Vec<String> {
        vec!["roadmap".to_string()]
    }

    fn configure(
        &self,
        config: &mut DocsConfig,
        raw: &Map<String, Value>,
        _diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        if let Some(section) = raw.get("roadmap") {
            check_phases(section)?;
            config.extra.insert(
                "roadmap".to_string(),
                serde_json::to_value(normalize_roadmap(section))?,
            );
        }
        Ok(())
    }

    fn register_extensions(
        &self,
        registry: &mut ExtensionRegistry,
        config: &DocsConfig,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        let Some(roadmap) = active_roadmap(config) else {
            return Ok(());
        };
        registry.register_component(
            ComponentDefinition {
                props: props(&[
                    ("phases", "RoadmapPhase[] | undefined"),
                    ("project", "string | undefined"),
                    ("compact", "boolean | undefined"),
                    ("maxPhases", "number | undefined"),
                    ("moreLink", "string | undefined"),
                    ("title", "string | undefined"),
                    ("links", "{ label: string; href: string }[] | undefined"),
                ]),
                ..ComponentDefinition::new("Roadmap", "@/components/roadmap")
            },
            diag,
        )?;
        registry.register_component(
            ComponentDefinition {
                expose_mdx: false,
                props: props(&[
                    ("phases", "RoadmapPhase[] | undefined"),
                    (
                        "projects",
                        "Record<string, { label?: string; description?: string }> | undefined",
                    ),
                    ("title", "string | undefined"),
                    ("description", "string | undefined"),
                    ("links", "{ label: string; href: string }[] | undefined"),
                ]),
                ..ComponentDefinition::new("RoadmapPage", "@/components/roadmap-page")
            },
            diag,
        )?;
        registry.write_data_module(DataModuleDefinition {
            name: "roadmap".to_string(),
            export_name: "roadmapPhases".to_string(),
            data: Value::Array(renderable_phases(&roadmap.phases)),
            type_source: ROADMAP_TYPES.to_string(),
            type_annotation: "RoadmapPhase[]".to_string(),
            module_path: "roadmap-data".to_string(),
        })?;
        // `roadmap.projects` for a page that draws a project card outside the
        // `/roadmap/` view, so its label and description stay in docs.yaml.
        let projects = project_block(&roadmap);
        registry.write_data_module(DataModuleDefinition {
            name: "roadmap-projects".to_string(),
            export_name: "roadmapProjects".to_string(),
            data: serde_json::to_value(&projects)?,
            type_source: ROADMAP_PROJECTS_TYPES.to_string(),
            type_annotation: "Record<string, RoadmapProject>".to_string(),
            module_path: "roadmap-projects".to_string(),
        })?;
        if !roadmap.routes.public {
            return Ok(());
        }

        // The heading names the project; the document title must not, because
        // the root layout appends the project name to every view title.
        let mut block_props = Map::new();
        block_props.insert(
            "title".to_string(),
            json!(format!("{} Roadmap", config.project.name)),
        );
        if !roadmap.description.is_empty() {
            block_props.insert("description".to_string(), json!(roadmap.description));
        }
        if !projects.is_empty() {
            block_props.insert("projects".to_string(), serde_json::to_value(projects)?);
        }
        let mut layout_props = Map::new();
        layout_props.insert("dense".to_string(), Value::Bool(true));
        registry.add_view(
            "/roadmap",
            PUBLIC_LAYOUT,
            IndexMap::from([(
                "main".to_string(),
                vec![ViewBlock {
                    component: "RoadmapPage".to_string(),
                    props: block_props,
                }],
            )]),
            "Roadmap",
            layout_props,
        )?;
        Ok(())
    }

    fn emit_assets(
        &self,
        builder: &mut dyn AssetBuilder,
        config: &DocsConfig,
        _diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        let Some(roadmap) = active_roadmap(config) else {
            return Ok(());
        };
        if roadmap.routes.docs {
            // A persisted page from a warm build stays a valid link target; an
            // authored `docs/roadmap.md` wins and the page is never rewritten.
            builder.register_route("roadmap");
            if !builder.page_exists("roadmap")? {
                builder.write_page("roadmap", &docs_page_mdx())?;
            }
        }
        Ok(())
    }
}

#[cfg(test)]
#[path = "roadmap_tests.rs"]
mod tests;
