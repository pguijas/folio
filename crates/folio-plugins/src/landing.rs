//! The landing built-in: sole owner of `landing:` normalization;
//! `landing_page.rs` derives what `app/page.tsx` renders.

use folio_config::DocsConfig;
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};

use crate::error::PluginError;
use crate::hook::Plugin;
use crate::msgfmt::{quoted, quoted_value};
use crate::Diagnostics;

/// The hero layouts `app/page.tsx` can render.
pub const HERO_VARIANTS: [&str; 4] = ["docs-map", "source-pipeline", "build-pipeline", "heartbeat"];
/// The hero used when `hero.variant` is missing or unknown.
pub const DEFAULT_HERO_VARIANT: &str = "docs-map";
/// `cta.primary.text` when omitted.
pub const DEFAULT_CTA_PRIMARY_TEXT: &str = "Get Started";
/// `cta.primary.link` when omitted.
pub const DEFAULT_CTA_PRIMARY_LINK: &str = "/docs";
/// Marks the template draws on a funnel tile. Keys name the thing, not the
/// glyph, so a site's config survives the template swapping a glyph.
pub const FUNNEL_ICONS: [&str; 13] = [
    "config",
    "python",
    "javascript",
    "rust",
    "markdown",
    "language",
    "guides",
    "api",
    "pages",
    "folder",
    "search",
    "agents",
    "hash",
];
/// The `landing.sections` types the bundled template renders, sorted.
pub const SECTION_TYPES: [&str; 14] = [
    "cells",
    "comparison",
    "cta",
    "features",
    "funnel",
    "install",
    "link-grid",
    "mechanism",
    "output",
    "pipeline",
    "routes",
    "statement",
    "stats",
    "use-cases",
];
/// Vignette kinds of a `features` bento card.
pub const FEATURE_VISUALS: [&str; 6] = [
    "components",
    "llms",
    "receipt",
    "deploy",
    "plugins",
    "theming",
];
/// Vignette kinds of a `cells` item.
pub const CELL_VISUALS: [&str; 7] = [
    "components",
    "llms",
    "export",
    "plugins",
    "maintainers",
    "agents",
    "migrating",
];

const COMPARISON_REPLACEMENT: &str = "The built-in table is deprecated and will be removed; fill in your own instead: `comparison: {caption, tools: [...], rows: [{feature, values: [...], note}]}` (see https://pguijas.github.io/folio/docs/plugins/landing)";

/// The normalized `landing:` section; field order is the JSON key order.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Landing {
    pub enabled: bool,
    pub hero: Hero,
    pub cta: Cta,
    /// Passthrough; the template types it as `string[]`.
    pub install: Value,
    /// Passthrough; the template types it as `LandingFeature[]`.
    pub features: Value,
    pub sections: Vec<Map<String, Value>>,
    pub comparison: Comparison,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
/// The normalized `hero:` block.
pub struct Hero {
    pub variant: String,
    /// `None` = template default; `Some("")` = a deliberate no-kicker hero.
    pub tagline: Option<String>,
    pub headline: Value,
    pub description: Value,
    pub notice: Notice,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stage: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
/// The hero's announcement chip: one message plus a safe link.
pub struct Notice {
    pub text: String,
    pub link: String,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
/// The primary and secondary calls to action.
pub struct Cta {
    pub primary: CtaLink,
    pub secondary: CtaLink,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
/// One call to action; `text` and `link` pass through untyped.
pub struct CtaLink {
    pub text: Value,
    pub link: Value,
}

/// `false` (off), `true` (the deprecated bundled matrix) or the project's own table.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Comparison {
    Flag(bool),
    Table(ComparisonTable),
}

impl Comparison {
    pub(crate) fn is_on(&self) -> bool {
        !matches!(self, Comparison::Flag(false))
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
/// The project's own comparison table (the `CompareMatrix` prop contract).
pub struct ComparisonTable {
    pub caption: String,
    pub tools: Vec<String>,
    pub rows: Vec<ComparisonRow>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
/// One comparison row: one cell per tool.
pub struct ComparisonRow {
    pub feature: String,
    /// `true`, `false` or `"~"` per tool.
    pub values: Vec<Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub note: Option<String>,
}

fn string_of(value: Option<&Value>) -> String {
    value
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string()
}

fn string_or(value: Option<&Value>, default: &str) -> String {
    value.and_then(Value::as_str).unwrap_or(default).to_string()
}

fn mapping(value: Option<&Value>) -> Map<String, Value> {
    value
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default()
}

fn delete_non_strings(section: &mut Map<String, Value>, keys: &[&str]) {
    for key in keys {
        if section.get(*key).is_some_and(|v| !v.is_string()) {
            section.remove(*key);
        }
    }
}

/// `landing: <bool>` shorthand, the `enabled` subkey (only `false` disables), else true.
pub fn landing_enabled(raw: &Value) -> bool {
    match raw {
        Value::Bool(b) => *b,
        Value::Object(map) => map.get("enabled") != Some(&Value::Bool(false)),
        _ => true,
    }
}

/// One of `HERO_VARIANTS`, else `docs-map`; a configured value that is not
/// one of them warns and names the valid ones.
pub fn landing_hero_variant(raw: &Value, diag: &mut Diagnostics) -> &'static str {
    if let Some(variant) = HERO_VARIANTS
        .iter()
        .copied()
        .find(|v| raw.as_str() == Some(v))
    {
        return variant;
    }
    if !raw.is_null() {
        diag.push(format!(
            "landing: unknown hero variant {} — using {}; valid variants: {}",
            quoted_value(raw),
            quoted(DEFAULT_HERO_VARIANT),
            HERO_VARIANTS.join(", ")
        ));
    }
    DEFAULT_HERO_VARIANT
}

/// A configured href validated by the shared scheme policy, or `default`
/// with a warning. Presentational, so it degrades instead of failing.
pub fn safe_section_href(
    raw: Option<&Value>,
    path: &str,
    default: &str,
    diag: &mut Diagnostics,
) -> String {
    let Some(value) = raw.and_then(Value::as_str).filter(|s| !s.is_empty()) else {
        return default.to_string();
    };
    let yaml = serde_yaml_ng::Value::String(value.to_string());
    match folio_config::theme::theme_href(&yaml, path) {
        Ok(_) => value.to_string(),
        Err(error) => {
            diag.push(format!("{error} — using {} instead", quoted(default)));
            default.to_string()
        }
    }
}

/// A stage label: stripped, or `None` when blank or not a string.
fn clean_stage(raw: &Value) -> Option<String> {
    raw.as_str()
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(str::to_string)
}

fn normalize_stage(section: &mut Map<String, Value>) {
    let Some(raw) = section.get("stage") else {
        return;
    };
    match clean_stage(raw) {
        Some(stage) => {
            section.insert("stage".to_string(), Value::String(stage));
        }
        None => {
            section.remove("stage");
        }
    }
}

fn normalize_actions(section: &mut Map<String, Value>, diag: &mut Diagnostics) {
    let Some(raw_actions) = section.get("actions") else {
        return;
    };
    let Some(raw_actions) = raw_actions.as_array().cloned() else {
        diag.push("landing: section 'actions' must be a list — ignoring it".to_string());
        section.insert("actions".to_string(), json!([]));
        return;
    };
    let mut actions = Vec::new();
    for raw_action in &raw_actions {
        let Some(action_map) = raw_action.as_object() else {
            diag.push(format!(
                "landing: section action {} must be a mapping — dropped",
                quoted_value(raw_action)
            ));
            continue;
        };
        let title = string_of(action_map.get("title")).trim().to_string();
        if title.is_empty() {
            diag.push(format!(
                "landing: section action {} needs a title — dropped",
                quoted_value(raw_action)
            ));
            continue;
        }
        let href = safe_section_href(
            action_map.get("href"),
            &format!("landing: section action {} href", quoted(&title)),
            "",
            diag,
        );
        if href.is_empty() {
            diag.push(format!(
                "landing: section action {} needs an href — dropped",
                quoted(&title)
            ));
            continue;
        }
        let mut action = Map::new();
        action.insert("title".to_string(), Value::String(title));
        action.insert("href".to_string(), Value::String(href));
        let detail = string_of(action_map.get("detail")).trim().to_string();
        if !detail.is_empty() {
            action.insert("detail".to_string(), Value::String(detail));
        }
        for flag in ["primary", "external"] {
            if action_map.get(flag) == Some(&Value::Bool(true)) {
                action.insert(flag.to_string(), Value::Bool(true));
            }
        }
        actions.push(Value::Object(action));
    }
    section.insert("actions".to_string(), Value::Array(actions));
}

fn normalize_hero_notice(raw: Option<&Value>, diag: &mut Diagnostics) -> Notice {
    let notice = mapping(raw);
    let text = string_of(notice.get("text"));
    if text.is_empty() {
        return Notice {
            text: String::new(),
            link: String::new(),
        };
    }
    let link = safe_section_href(
        notice.get("link"),
        &format!("landing: hero notice '{text}' link"),
        "",
        diag,
    );
    Notice { text, link }
}

fn normalize_mechanism(section: &mut Map<String, Value>) {
    delete_non_strings(section, &["eyebrow", "title", "description"]);
    for (key, default) in [("code_title", "docs.yaml"), ("code", ""), ("caption", "")] {
        let value = string_or(section.get(key), default);
        section.insert(key.to_string(), Value::String(value));
    }
    let pills: Vec<Value> = section
        .get("pills")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter(|p| p.as_str().is_some_and(|s| !s.is_empty()))
                .cloned()
                .collect()
        })
        .unwrap_or_default();
    let pills = if pills.is_empty() {
        json!(["git push", "folio build", "deploy"])
    } else {
        Value::Array(pills)
    };
    section.insert("pills".to_string(), pills);
    let commits: Vec<Value> = section
        .get("commits")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_object)
                .map(|c| (string_of(c.get("hash")), string_of(c.get("message"))))
                .filter(|(hash, message)| !hash.is_empty() || !message.is_empty())
                .map(|(hash, message)| json!({"hash": hash, "message": message}))
                .collect()
        })
        .unwrap_or_default();
    section.insert("commits".to_string(), Value::Array(commits));
}

fn normalize_statement(section: &mut Map<String, Value>, diag: &mut Diagnostics) {
    delete_non_strings(section, &["eyebrow", "title", "description"]);
    for key in ["text", "accent"] {
        let value = string_of(section.get(key));
        section.insert(key.to_string(), Value::String(value));
    }
    if section
        .get("size")
        .is_some_and(|s| !matches!(s.as_str(), Some("md" | "lg")))
    {
        section.remove("size");
    }
    let mut actions: Vec<Value> = Vec::new();
    for raw_action in section
        .get("actions")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
    {
        let Some(action_map) = raw_action.as_object() else {
            continue;
        };
        let title = string_of(action_map.get("title"));
        let href = safe_section_href(
            action_map.get("href"),
            &format!("landing: statement section action '{title}' href"),
            "",
            diag,
        );
        if title.is_empty() || href.is_empty() {
            continue;
        }
        let mut action = json!({"title": title, "href": href});
        if let Some(Value::Bool(primary)) = action_map.get("primary") {
            action["primary"] = Value::Bool(*primary);
        } else if actions.is_empty() {
            action["primary"] = Value::Bool(true);
        }
        actions.push(action);
    }
    section.insert("actions".to_string(), Value::Array(actions));
}

/// The funnel plate's retired keys, each with what replaced it. A config that
/// still carries one gets a warning and the key never reaches the template.
const FUNNEL_RETIRED_KEYS: [(&str, &str); 3] = [
    ("guarantees", "the strip is gone"),
    ("command_notes", "the build seam carries only `command`"),
    ("caption", "the FIG. line is gone"),
];

fn normalize_funnel(section: &mut Map<String, Value>, diag: &mut Diagnostics) {
    delete_non_strings(section, &["eyebrow", "title", "description"]);
    let command = string_or(section.get("command"), "folio build");
    section.insert("command".to_string(), Value::String(command));
    let inputs = funnel_tiles(section.get("inputs"), true);
    section.insert("inputs".to_string(), Value::Array(inputs));
    let outputs = funnel_tiles(section.get("outputs"), false);
    section.insert("outputs".to_string(), Value::Array(outputs));
    for (key, note) in FUNNEL_RETIRED_KEYS {
        if section.remove(key).is_some() {
            diag.push(format!(
                "landing: funnel section '{key}' is no longer rendered — {note}"
            ));
        }
    }
}

/// Funnel tiles: `label` required, `icon` only when whitelisted; input tiles
/// also carry `ghost` and an optional `chip`.
fn funnel_tiles(raw: Option<&Value>, inputs: bool) -> Vec<Value> {
    raw.and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_object)
                .filter_map(|tile| {
                    let label = string_of(tile.get("label"));
                    if label.is_empty() {
                        return None;
                    }
                    let mut item = json!({ "label": label });
                    if inputs {
                        item["ghost"] = Value::Bool(tile.get("ghost") == Some(&Value::Bool(true)));
                        let chip = string_of(tile.get("chip"));
                        if !chip.is_empty() {
                            item["chip"] = Value::String(chip);
                        }
                    }
                    let icon = string_of(tile.get("icon"));
                    if FUNNEL_ICONS.contains(&icon.as_str()) {
                        item["icon"] = Value::String(icon);
                    }
                    Some(item)
                })
                .collect()
        })
        .unwrap_or_default()
}

fn normalize_features(section: &mut Map<String, Value>, diag: &mut Diagnostics) {
    delete_non_strings(section, &["eyebrow", "title", "description"]);
    if section
        .get("variant")
        .is_some_and(|v| v.as_str() != Some("bento"))
    {
        section.remove("variant");
    }
    delete_non_strings(section, &["title_muted"]);
    if let Some(raw_actions) = section.get("actions").cloned() {
        let mut actions = Vec::new();
        for action in raw_actions.as_array().cloned().unwrap_or_default() {
            let Some(action_map) = action.as_object() else {
                continue;
            };
            let title = string_of(action_map.get("title"));
            let href = safe_section_href(
                action_map.get("href"),
                &format!("landing: features section action '{title}' href"),
                "",
                diag,
            );
            if !title.is_empty() && !href.is_empty() {
                actions.push(json!({"title": title, "href": href}));
            }
        }
        section.insert("actions".to_string(), Value::Array(actions));
    }
    if let Some(raw_features) = section.get("features").and_then(Value::as_array).cloned() {
        let features: Vec<Value> = raw_features
            .into_iter()
            .map(|feature| match feature {
                Value::Object(mut map) => {
                    if map
                        .get("visual")
                        .is_some_and(|v| !v.as_str().is_some_and(|s| FEATURE_VISUALS.contains(&s)))
                    {
                        map.remove("visual");
                    }
                    Value::Object(map)
                }
                other => other,
            })
            .collect();
        section.insert("features".to_string(), Value::Array(features));
    }
}

fn normalize_cells(section: &mut Map<String, Value>, diag: &mut Diagnostics) {
    delete_non_strings(section, &["eyebrow", "title", "description"]);
    let mut items = Vec::new();
    for raw_item in section
        .get("items")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
    {
        let Some(raw) = raw_item.as_object() else {
            continue;
        };
        let title = string_of(raw.get("title"));
        if title.is_empty() {
            continue;
        }
        let mut item = json!({
            "title": title,
            "label": string_of(raw.get("label")),
            "description": string_of(raw.get("description")),
            "link_text": string_of(raw.get("link_text")),
        });
        let visual = string_of(raw.get("visual"));
        if CELL_VISUALS.contains(&visual.as_str()) {
            item["visual"] = Value::String(visual);
        }
        let image = safe_section_href(
            raw.get("image"),
            &format!("landing: cells item '{title}' image"),
            "",
            diag,
        );
        if !image.is_empty() {
            item["image"] = Value::String(image);
            let alt = string_of(raw.get("image_alt"));
            if !alt.is_empty() {
                item["image_alt"] = Value::String(alt);
            }
        }
        let href = safe_section_href(
            raw.get("href"),
            &format!("landing: cells item '{title}' href"),
            "",
            diag,
        );
        if !href.is_empty() {
            item["href"] = Value::String(href);
        }
        items.push(item);
    }
    section.insert("items".to_string(), Value::Array(items));
}

/// One matrix cell: yes (`true`), no (`false`) or partial (`"~"`).
fn comparison_value(raw: &Value) -> Value {
    match raw {
        Value::Bool(b) => Value::Bool(*b),
        Value::String(s) => match s.trim().to_lowercase().as_str() {
            "yes" | "true" => Value::Bool(true),
            "no" | "false" => Value::Bool(false),
            _ => json!("~"),
        },
        _ => json!("~"),
    }
}

fn comparison_tools(raw: Option<&Value>) -> Vec<String> {
    raw.and_then(Value::as_array)
        .map(|tools| {
            tools
                .iter()
                .filter_map(Value::as_str)
                .map(str::trim)
                .filter(|t| !t.is_empty())
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default()
}

fn comparison_rows(
    raw: Option<&Value>,
    tool_count: usize,
    diag: &mut Diagnostics,
) -> Vec<ComparisonRow> {
    let mut rows = Vec::new();
    for raw_row in raw.and_then(Value::as_array).cloned().unwrap_or_default() {
        let Some(row) = raw_row.as_object() else {
            continue;
        };
        let feature = string_of(row.get("feature")).trim().to_string();
        let Some(values) = row.get("values").and_then(Value::as_array) else {
            continue;
        };
        if feature.is_empty() {
            continue;
        }
        if values.len() != tool_count {
            diag.push(format!(
                "landing: comparison row '{feature}' has {} values for {tool_count} tools; dropping the row",
                values.len()
            ));
            continue;
        }
        let note = string_of(row.get("note")).trim().to_string();
        rows.push(ComparisonRow {
            feature,
            values: values.iter().map(comparison_value).collect(),
            note: (!note.is_empty()).then_some(note),
        });
    }
    rows
}

/// `{caption, tools, rows}` from a mapping, or `None` when unusable.
fn comparison_table(table: &Map<String, Value>, diag: &mut Diagnostics) -> Option<ComparisonTable> {
    let tools = comparison_tools(table.get("tools"));
    let rows = if tools.is_empty() {
        Vec::new()
    } else {
        comparison_rows(table.get("rows"), tools.len(), diag)
    };
    if tools.is_empty() || rows.is_empty() {
        return None;
    }
    Some(ComparisonTable {
        caption: string_of(table.get("caption")).trim().to_string(),
        tools,
        rows,
    })
}

fn warn_builtin_comparison(source: &str, diag: &mut Diagnostics) {
    diag.push(format!(
        "landing: {source} renders Folio's own table of documentation tools on your landing page. {COMPARISON_REPLACEMENT}"
    ));
}

/// `landing.comparison`: the project's own table, the deprecated `true`, or `false`.
pub fn landing_comparison(raw: &Value, diag: &mut Diagnostics) -> Comparison {
    if raw == &Value::Bool(true) {
        warn_builtin_comparison("`comparison: true`", diag);
        return Comparison::Flag(true);
    }
    let Some(table) = raw.as_object() else {
        return Comparison::Flag(false);
    };
    match comparison_table(table, diag) {
        Some(table) => Comparison::Table(table),
        None => {
            diag.push("landing: comparison needs a `tools:` list and at least one usable `rows:` entry; ignoring it".to_string());
            Comparison::Flag(false)
        }
    }
}

fn normalize_comparison_section(section: &mut Map<String, Value>, diag: &mut Diagnostics) {
    delete_non_strings(section, &["eyebrow", "title", "description"]);
    match comparison_table(section, diag) {
        Some(table) => {
            section.insert("caption".to_string(), Value::String(table.caption));
            section.insert("tools".to_string(), json!(table.tools));
            section.insert(
                "rows".to_string(),
                serde_json::to_value(table.rows).expect("rows serialise"),
            );
        }
        None => {
            for key in ["caption", "tools", "rows"] {
                section.remove(key);
            }
            warn_builtin_comparison("a `comparison` section without `tools:` and `rows:`", diag);
        }
    }
}

fn warn_unknown_section_type(raw: Option<&Value>, diag: &mut Diagnostics) {
    let what = match raw {
        Some(kind) => format!("has the unknown type {}", quoted_value(kind)),
        None => "has no `type`".to_string(),
    };
    diag.push(format!(
        "landing: a section {what} — the bundled template does not render it; valid types: {}",
        SECTION_TYPES.join(", ")
    ));
}

/// `landing.sections`: non-mappings drop; shared `stage`/`actions` first,
/// then the per-type normalizer. A missing or unknown type passes through
/// for a theme package that renders it, with a warning naming the types the
/// bundled template renders.
pub fn landing_sections(raw: &Value, diag: &mut Diagnostics) -> Vec<Map<String, Value>> {
    let mut sections = Vec::new();
    for raw_section in raw.as_array().into_iter().flatten() {
        let Some(map) = raw_section.as_object() else {
            continue;
        };
        let mut section = map.clone();
        normalize_stage(&mut section);
        normalize_actions(&mut section, diag);
        match section.get("type").and_then(Value::as_str) {
            Some("cells") => normalize_cells(&mut section, diag),
            Some("comparison") => normalize_comparison_section(&mut section, diag),
            Some("features") => normalize_features(&mut section, diag),
            Some("funnel") => normalize_funnel(&mut section, diag),
            Some("mechanism") => normalize_mechanism(&mut section),
            Some("statement") => normalize_statement(&mut section, diag),
            Some(kind) if SECTION_TYPES.contains(&kind) => {}
            _ => warn_unknown_section_type(section.get("type"), diag),
        }
        sections.push(section);
    }
    sections
}

/// The whole `landing:` section normalized; non-mappings degrade to defaults.
pub fn normalize_landing(raw: &Value, diag: &mut Diagnostics) -> Landing {
    let landing = mapping(Some(raw));
    let hero = mapping(landing.get("hero"));
    let cta = mapping(landing.get("cta"));
    let primary = mapping(cta.get("primary"));
    let secondary = mapping(cta.get("secondary"));
    Landing {
        enabled: landing_enabled(raw),
        hero: Hero {
            variant: landing_hero_variant(hero.get("variant").unwrap_or(&Value::Null), diag)
                .to_string(),
            tagline: hero
                .contains_key("tagline")
                .then(|| string_of(hero.get("tagline"))),
            headline: hero.get("headline").cloned().unwrap_or_else(|| json!("")),
            description: hero
                .get("description")
                .cloned()
                .unwrap_or_else(|| json!("")),
            notice: normalize_hero_notice(hero.get("notice"), diag),
            stage: hero.get("stage").and_then(clean_stage),
        },
        cta: Cta {
            primary: CtaLink {
                text: primary
                    .get("text")
                    .cloned()
                    .unwrap_or_else(|| json!(DEFAULT_CTA_PRIMARY_TEXT)),
                link: primary
                    .get("link")
                    .cloned()
                    .unwrap_or_else(|| json!(DEFAULT_CTA_PRIMARY_LINK)),
            },
            secondary: CtaLink {
                text: secondary.get("text").cloned().unwrap_or_else(|| json!("")),
                link: secondary.get("link").cloned().unwrap_or_else(|| json!("")),
            },
        },
        install: landing.get("install").cloned().unwrap_or_else(|| json!([])),
        features: landing
            .get("features")
            .cloned()
            .unwrap_or_else(|| json!([])),
        sections: landing_sections(landing.get("sections").unwrap_or(&Value::Null), diag),
        comparison: landing_comparison(landing.get("comparison").unwrap_or(&Value::Null), diag),
    }
}

impl Landing {
    /// `enabled: false`, every other field at its default.
    pub fn disabled() -> Landing {
        Landing {
            enabled: false,
            ..normalize_landing(&Value::Object(Map::new()), &mut Vec::new())
        }
    }

    /// The section the landing plugin wrote into `config.extra`; absent means disabled.
    pub fn from_config(config: &DocsConfig) -> Landing {
        config
            .extra
            .get("landing")
            .and_then(|value| serde_json::from_value(value.clone()).ok())
            .unwrap_or_else(Landing::disabled)
    }
}

/// Sole owner of the `landing:` key.
pub struct LandingPlugin;

impl Plugin for LandingPlugin {
    fn name(&self) -> String {
        "landing".to_string()
    }

    fn config_keys(&self) -> Vec<String> {
        vec!["landing".to_string()]
    }

    fn configure(
        &self,
        config: &mut DocsConfig,
        raw: &Map<String, Value>,
        diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        let Some(section) = raw.get("landing") else {
            config.landing_enabled = false;
            return Ok(());
        };
        let landing = normalize_landing(section, diag);
        config.landing_enabled = landing.enabled;
        config
            .extra
            .insert("landing".to_string(), serde_json::to_value(landing)?);
        Ok(())
    }
}

#[cfg(test)]
#[path = "landing_tests.rs"]
mod tests;
