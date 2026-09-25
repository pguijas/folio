//! The values `app/page.tsx` renders from a normalized landing: derived
//! defaults, the default section catalog and the feature cards; `folio-site`
//! substitutes the markers.

use folio_config::DocsConfig;
use serde::Serialize;
use serde_json::{json, Map, Value};

use crate::landing::{Comparison, Landing};
use crate::msgfmt::truthy;

/// The six feature cards a landing without `features:` shows.
pub fn default_features() -> Value {
    json!([
        {"title": "Automatic API Reference", "description": "Parse source files and docstrings into classes, functions, type annotations, and parameter tables.", "wide": true},
        {"title": "One Config File", "description": "A single docs.yaml holds the whole site: sources, guides, theme, and navigation. About thirty lines."},
        {"title": "Built-in Integrations", "description": "Landing page, roadmap, and OpenAPI activate from docs.yaml sections; nothing else to install or run."},
        {"title": "Dark Mode, Search, Responsive", "description": "Full docs site with dark mode, search, and mobile support out of the box.", "wide": true},
        {"title": "LLM-Friendly Output", "description": "Generates llms.txt following the llmstxt.org spec so AI assistants understand your library."},
        {"title": "Markdown + API in One Site", "description": "Write guides in Markdown alongside auto-generated API reference. One cohesive site.", "wide": true}
    ])
}

fn default_sections(
    features: &Value,
    variant: &str,
    comparison: &Comparison,
) -> Vec<Map<String, Value>> {
    let mut sections = Vec::new();
    let mut push =
        |value: Value| sections.push(value.as_object().cloned().expect("section mapping"));
    if truthy(features) {
        push(json!({"type": "features", "features": features}));
    }
    if variant == "docs-map" {
        push(json!({"type": "routes"}));
    }
    if comparison.is_on() && variant == "source-pipeline" {
        match comparison {
            Comparison::Table(table) => push(
                json!({"type": "comparison", "caption": table.caption, "tools": table.tools, "rows": table.rows}),
            ),
            Comparison::Flag(_) => push(json!({"type": "comparison"})),
        }
    }
    push(json!({"type": "output"}));
    push(json!({"type": "cta"}));
    sections
}

/// The values `app/page.tsx` (and the navbar) receive; `folio-site`
/// substitutes the markers with their JSON.
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct LandingPageData {
    pub name: String,
    pub monogram: String,
    pub version: String,
    pub tagline: String,
    pub notice_text: String,
    pub notice_link: String,
    pub headline: Value,
    pub description: Value,
    pub cta_primary_text: Value,
    pub cta_primary_link: Value,
    pub cta_secondary_text: Value,
    /// `None` renders the literal `null`.
    pub cta_secondary_link: Option<String>,
    pub hero_variant: String,
    pub sections: Vec<Map<String, Value>>,
    pub install_commands: Value,
    pub features: Value,
}

impl LandingPageData {
    /// The values derived from `landing` and the config; an omitted `install:`
    /// emits no commands and an omitted `tagline` no kicker.
    pub fn derive(landing: &Landing, config: &DocsConfig) -> LandingPageData {
        let name = config.project.name.clone();
        let mut cta_primary_link = landing.cta.primary.link.clone();
        if matches!(cta_primary_link.as_str(), Some("/docs" | "/docs/")) {
            cta_primary_link = Value::String(config.template.docs_route_base.clone());
        }
        let cta_secondary_link = landing
            .cta
            .secondary
            .link
            .as_str()
            .filter(|s| !s.is_empty())
            .map(str::to_string)
            .or_else(|| (!config.project.repo.is_empty()).then(|| config.project.repo.clone()));
        let cta_secondary_text = if truthy(&landing.cta.secondary.text) {
            landing.cta.secondary.text.clone()
        } else if cta_secondary_link.is_some() {
            json!("GitHub")
        } else {
            json!("")
        };
        let features = if truthy(&landing.features) {
            landing.features.clone()
        } else {
            default_features()
        };
        let sections = if landing.sections.is_empty() {
            default_sections(&features, &landing.hero.variant, &landing.comparison)
        } else {
            landing.sections.clone()
        };
        LandingPageData {
            monogram: name.chars().take(2).collect::<String>().to_lowercase(),
            version: config.project.version.clone(),
            tagline: landing.hero.tagline.clone().unwrap_or_default(),
            notice_text: landing.hero.notice.text.clone(),
            notice_link: landing.hero.notice.link.clone(),
            headline: if truthy(&landing.hero.headline) {
                landing.hero.headline.clone()
            } else {
                json!(format!("Documentation for {name}"))
            },
            description: if truthy(&landing.hero.description) {
                landing.hero.description.clone()
            } else {
                json!("Beautiful, modern docs. Zero configuration.")
            },
            cta_primary_text: landing.cta.primary.text.clone(),
            cta_primary_link,
            cta_secondary_text,
            cta_secondary_link,
            hero_variant: landing.hero.variant.clone(),
            sections,
            install_commands: if truthy(&landing.install) {
                landing.install.clone()
            } else {
                json!([])
            },
            features,
            name,
        }
    }
}

#[cfg(test)]
#[path = "landing_page_tests.rs"]
mod tests;
