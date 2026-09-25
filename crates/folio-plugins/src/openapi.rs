//! The openapi built-in: `openapi:` normalization, spec loading, the
//! `OpenApiReference` component, `lib/openapi-data.ts` and one generated page
//! per source with its `_meta.ts` entry.

use std::path::Path;

use folio_config::{canonicalize_lenient, DocsConfig};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};

use crate::builder::AssetBuilder;
use crate::error::{PluginError, PluginsError};
use crate::hook::Plugin;
use crate::meta::write_route_meta;
use crate::msgfmt::{as_text, kind, quoted, truthy};
use crate::registry::{ComponentDefinition, DataModuleDefinition, ExtensionRegistry};
use crate::Diagnostics;

/// The type block `lib/openapi-data.ts` starts with.
pub const OPENAPI_TYPES: &str = "export interface OpenApiOperation {\n  method: string\n  path: string\n  summary: string\n  description: string\n  operationId: string\n  tags: string[]\n}\n\nexport interface OpenApiSource {\n  title: string\n  version: string\n  description: string\n  route: string\n  servers: string[]\n  operations: OpenApiOperation[]\n  schemas: string[]\n}\n";

/// The operation methods, in the order they are emitted per path.
pub const HTTP_METHODS: [&str; 8] = [
    "get", "post", "put", "patch", "delete", "head", "options", "trace",
];

/// One normalized source; `spec` is the whole parsed document and stays out
/// of the data module.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct OpenApiSource {
    pub title: String,
    pub version: String,
    pub description: String,
    pub route: String,
    pub servers: Vec<String>,
    pub operations: Vec<Operation>,
    pub schemas: Vec<String>,
    pub spec: Value,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
/// One operation of a source's `paths`.
pub struct Operation {
    pub method: String,
    pub path: String,
    pub summary: String,
    pub description: String,
    pub operation_id: String,
    pub tags: Vec<String>,
}

/// A parsed YAML document as JSON; entries under non-string mapping keys
/// (`200:` response codes, a numeric path) are dropped.
fn yaml_to_json(value: serde_yaml_ng::Value) -> Value {
    use serde_yaml_ng::Value as Y;
    match value {
        Y::Null => Value::Null,
        Y::Bool(b) => Value::Bool(b),
        Y::Number(n) => serde_json::to_value(n).unwrap_or(Value::Null),
        Y::String(s) => Value::String(s),
        Y::Sequence(items) => Value::Array(items.into_iter().map(yaml_to_json).collect()),
        Y::Mapping(map) => Value::Object(
            map.into_iter()
                .filter_map(|(k, v)| match k {
                    Y::String(key) => Some((key, yaml_to_json(v))),
                    _ => None,
                })
                .collect(),
        ),
        Y::Tagged(tagged) => yaml_to_json(tagged.value),
    }
}

fn source_label(raw: &Map<String, Value>) -> String {
    ["title", "path"]
        .iter()
        .find_map(|key| {
            raw.get(*key)?
                .as_str()
                .map(str::trim)
                .filter(|s| !s.is_empty())
        })
        .map(quoted)
        .unwrap_or_else(|| "<inline content>".to_string())
}

fn parse_yaml(text: &str, label: &str) -> Result<Value, PluginsError> {
    serde_yaml_ng::from_str::<serde_yaml_ng::Value>(text)
        .map(yaml_to_json)
        .map_err(|e| PluginsError::OpenApiSpecParse {
            label: label.to_string(),
            message: e.to_string(),
        })
}

/// `content` (fallback `spec`) as a mapping or YAML/JSON text, else the file at `path`.
fn load_spec(raw: &Map<String, Value>, project_dir: &Path) -> Result<Value, PluginsError> {
    let label = source_label(raw);
    match raw.get("content").or_else(|| raw.get("spec")) {
        Some(Value::Object(spec)) => return Ok(Value::Object(spec.clone())),
        Some(Value::String(text)) if !text.trim().is_empty() => return parse_yaml(text, &label),
        _ => {}
    }
    let Some(raw_path) = raw
        .get("path")
        .and_then(Value::as_str)
        .filter(|p| !p.trim().is_empty())
    else {
        return Ok(Value::Null);
    };
    let path = Path::new(raw_path);
    let path = if path.is_absolute() {
        path.to_path_buf()
    } else {
        project_dir.join(path)
    };
    let path = canonicalize_lenient(&path);
    // The containment rule every other configured path obeys.
    let project_root = canonicalize_lenient(project_dir);
    if !path.starts_with(&project_root) {
        return Err(PluginsError::OpenApiSpecOutsideProject {
            label,
            raw_path: raw_path.to_string(),
            project_dir: project_root,
        });
    }
    if !path.is_file() {
        return Err(PluginsError::OpenApiSpecNotFound {
            label,
            path,
            raw_path: raw_path.to_string(),
            project_dir: canonicalize_lenient(project_dir),
        });
    }
    let text = std::fs::read_to_string(&path).map_err(|e| PluginsError::OpenApiSpecParse {
        label: label.clone(),
        message: e.to_string(),
    })?;
    parse_yaml(&text, &label)
}

fn str_or_empty(value: Option<&Value>) -> String {
    value.filter(|v| truthy(v)).map(as_text).unwrap_or_default()
}

fn operations(spec: &Map<String, Value>) -> Vec<Operation> {
    let mut operations = Vec::new();
    for (path, item) in spec
        .get("paths")
        .and_then(Value::as_object)
        .into_iter()
        .flatten()
    {
        let Some(item) = item.as_object() else {
            continue;
        };
        for method in HTTP_METHODS {
            let Some(operation) = item.get(method).and_then(Value::as_object) else {
                continue;
            };
            operations.push(Operation {
                method: method.to_uppercase(),
                path: path.clone(),
                summary: str_or_empty(operation.get("summary")),
                description: str_or_empty(operation.get("description")),
                operation_id: str_or_empty(operation.get("operationId")),
                tags: operation
                    .get("tags")
                    .and_then(Value::as_array)
                    .map(|tags| {
                        tags.iter()
                            .filter_map(Value::as_str)
                            .map(str::to_string)
                            .collect()
                    })
                    .unwrap_or_default(),
            });
        }
    }
    operations
}

/// A configured route as slugged segments (`API Reference/HTTP` is
/// `api-reference/http`), else `api-reference/<slug of title>`, also when no
/// segment keeps a character (`/`, `***`). A `.` or `..` segment fails: the
/// generated page stays under the docs.
pub fn normalize_route(
    raw: Option<&Value>,
    title: &str,
    label: &str,
) -> Result<String, PluginsError> {
    let default_route = || {
        let slug = folio_config::slugify(title);
        format!(
            "api-reference/{}",
            if slug.is_empty() { "openapi" } else { &slug }
        )
    };
    let Some(route) = raw
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|r| !r.is_empty())
    else {
        return Ok(default_route());
    };
    let mut segments = Vec::new();
    for segment in route.split(['/', '\\']).map(str::trim) {
        if segment == "." || segment == ".." {
            return Err(PluginsError::OpenApiRoute {
                label: label.to_string(),
                route: route.to_string(),
            });
        }
        let slug = folio_config::slugify(segment);
        if !slug.is_empty() {
            segments.push(slug);
        }
    }
    if segments.is_empty() {
        return Ok(default_route());
    }
    Ok(segments.join("/"))
}

/// One `sources:` entry; `None` for a non-mapping entry or a spec that is
/// not a mapping (warned). A missing spec file fails.
pub fn normalize_source(
    raw: &Value,
    project_dir: &Path,
    diag: &mut Diagnostics,
) -> Result<Option<OpenApiSource>, PluginsError> {
    let Some(raw) = raw.as_object() else {
        return Ok(None);
    };
    let spec = load_spec(raw, project_dir)?;
    let Some(spec_map) = spec.as_object() else {
        diag.push(format!(
            "openapi: ignoring source {}: the spec did not parse to a mapping (got {})",
            source_label(raw),
            kind(&spec)
        ));
        return Ok(None);
    };
    let info = spec_map
        .get("info")
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default();
    let title = match raw
        .get("title")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|t| !t.is_empty())
    {
        Some(title) => title.to_string(),
        None => info
            .get("title")
            .filter(|t| truthy(t))
            .map(as_text)
            .unwrap_or_else(|| "OpenAPI".to_string()),
    };
    let description = [raw.get("description"), info.get("description")]
        .into_iter()
        .flatten()
        .find(|v| truthy(v))
        .map(as_text)
        .unwrap_or_default();
    Ok(Some(OpenApiSource {
        route: normalize_route(raw.get("route"), &title, &source_label(raw))?,
        title,
        version: str_or_empty(info.get("version")),
        description,
        servers: spec_map
            .get("servers")
            .and_then(Value::as_array)
            .map(|servers| {
                servers
                    .iter()
                    .filter_map(|s| s.as_object()?.get("url")?.as_str().map(str::to_string))
                    .collect()
            })
            .unwrap_or_default(),
        operations: operations(spec_map),
        schemas: spec_map
            .get("components")
            .and_then(|c| c.get("schemas"))
            .and_then(Value::as_object)
            .map(|schemas| schemas.keys().cloned().collect())
            .unwrap_or_default(),
        spec,
    }))
}

/// The `openapi:` section: `sources` as a list or one mapping.
pub fn normalize_openapi(
    raw: &Value,
    project_dir: &Path,
    diag: &mut Diagnostics,
) -> Result<Vec<OpenApiSource>, PluginsError> {
    let raw_sources = match raw.as_object().and_then(|m| m.get("sources")) {
        Some(Value::Array(items)) => items.clone(),
        Some(mapping @ Value::Object(_)) => vec![mapping.clone()],
        _ => Vec::new(),
    };
    let mut sources = Vec::new();
    for raw_source in &raw_sources {
        if let Some(source) = normalize_source(raw_source, project_dir, diag)? {
            sources.push(source);
        }
    }
    Ok(sources)
}

/// The sources `configure` stored; `None` when the section is absent.
pub fn active_sources(config: &DocsConfig) -> Option<Vec<OpenApiSource>> {
    let sources = config.extra.get("openapi")?.get("sources")?.as_array()?;
    Some(
        sources
            .iter()
            .filter_map(|s| serde_json::from_value(s.clone()).ok())
            .collect(),
    )
}

/// Everything but `spec`, in the data module's key order.
pub fn public_source_data(source: &OpenApiSource) -> Value {
    let mut value = serde_json::to_value(source).expect("source serialises");
    value.as_object_mut().map(|m| m.remove("spec"));
    value
}

/// Backslash-escape what MDX treats as syntax in body text.
pub fn escape_mdx_text(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for c in text.chars() {
        if matches!(c, '\\' | '`' | '{' | '}' | '<' | '>' | '[' | ']') {
            out.push('\\');
        }
        out.push(c);
    }
    out
}

/// Escape a title for a JSX attribute value.
pub fn escape_mdx_attr(text: &str) -> String {
    text.replace('&', "&amp;").replace('"', "&quot;")
}

/// The generated page for one source (write-if-changed on exact bytes).
pub fn docs_page_mdx(title: &str) -> String {
    format!(
        "import {{ OpenApiReference }} from \"@/components/openapi-reference\"\n\n# {}\n\n<OpenApiReference sourceTitle=\"{}\" />\n",
        escape_mdx_text(title),
        escape_mdx_attr(title)
    )
}

/// Owner of the `openapi:` key.
pub struct OpenApiPlugin;

impl Plugin for OpenApiPlugin {
    fn name(&self) -> String {
        "openapi".to_string()
    }

    fn config_keys(&self) -> Vec<String> {
        vec!["openapi".to_string()]
    }

    fn configure(
        &self,
        config: &mut DocsConfig,
        raw: &Map<String, Value>,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        if let Some(section) = raw.get("openapi") {
            let sources = normalize_openapi(section, &config.project_dir, diag)?;
            config
                .extra
                .insert("openapi".to_string(), json!({"sources": sources}));
        }
        Ok(())
    }

    fn register_extensions(
        &self,
        registry: &mut ExtensionRegistry,
        config: &DocsConfig,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        let Some(sources) = active_sources(config) else {
            return Ok(());
        };
        registry.register_component(
            ComponentDefinition::new("OpenApiReference", "@/components/openapi-reference"),
            diag,
        )?;
        registry.write_data_module(DataModuleDefinition {
            name: "openapi".to_string(),
            export_name: "openApiSources".to_string(),
            data: Value::Array(sources.iter().map(public_source_data).collect()),
            type_source: OPENAPI_TYPES.to_string(),
            type_annotation: "OpenApiSource[]".to_string(),
            module_path: "openapi-data".to_string(),
        })?;
        Ok(())
    }

    fn emit_assets(
        &self,
        builder: &mut dyn AssetBuilder,
        config: &DocsConfig,
        _diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        for source in active_sources(config).unwrap_or_default() {
            if source.route.is_empty() {
                continue;
            }
            // The route stays live even when the page persists from a prior build.
            builder.register_route(&source.route);
            let title = if source.title.is_empty() {
                "OpenAPI"
            } else {
                source.title.as_str()
            };
            let content = docs_page_mdx(title);
            let current =
                builder.page_exists(&source.route)? && builder.read_page(&source.route)? == content;
            if !current {
                builder.write_page(&source.route, &content)?;
            }
            write_route_meta(builder, &source.route, title)?;
        }
        Ok(())
    }
}

#[cfg(test)]
#[path = "openapi_tests.rs"]
mod tests;
