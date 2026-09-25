//! The MDX component contract (`lib/folio-mdx-contract.ts`) and the authoring
//! contract envelope (`/_folio/contract.json`). `folio-site` writes the files.

use std::collections::BTreeSet;
use std::path::Path;

use indexmap::IndexMap;
use serde::Serialize;

use crate::jsscan::{has_component_entry, strip_import_statements, strip_js_comments};
use crate::registry::ComponentDefinition;

/// Versions the components list only; 1.1 describes what the bundled
/// components always accepted.
pub const FOLIO_MDX_CONTRACT_VERSION: &str = "1.1";

/// The published authoring contract, relative to the workspace `public/`.
pub const FOLIO_AUTHORING_CONTRACT_PATH: &str = "_folio/contract.json";

/// The one instruction the contract carries for its readers.
pub const AUTHORING_CONTRACT_INSTRUCTIONS: &str = "Ignore fields you do not recognise; later Folio releases add them. mdxContractVersion versions the components list only.";

/// One published contract entry; field order is the JSON key order.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ContractComponent {
    pub name: String,
    pub required: bool,
    pub source: String,
    pub props: IndexMap<String, String>,
}

/// The components flagged `contract`, in the given order; `source` is the
/// `source_label`, never the category.
pub fn build_contract(components: &[ComponentDefinition]) -> Vec<ContractComponent> {
    components
        .iter()
        .filter(|c| c.contract)
        .map(|c| ContractComponent {
            name: c.name.clone(),
            required: c.required,
            source: c.source_label.clone(),
            props: c.props.clone(),
        })
        .collect()
}

/// Names of the contract members a custom template must wire.
pub fn required_component_names(components: &[ComponentDefinition]) -> Vec<String> {
    build_contract(components)
        .into_iter()
        .filter(|c| c.required)
        .map(|c| c.name)
        .collect()
}

fn pretty(value: &impl Serialize) -> String {
    serde_json::to_string_pretty(value).expect("contract serialises")
}

/// The text of `lib/folio-mdx-contract.ts`.
pub fn render_mdx_contract_module(components: &[ComponentDefinition]) -> String {
    format!(
        "export const folioMdxContractVersion = {} as const\n\nexport const folioMdxComponents = {} as const\n\nexport type FolioMdxComponentName = (typeof folioMdxComponents)[number][\"name\"]\n",
        pretty(&FOLIO_MDX_CONTRACT_VERSION),
        pretty(&build_contract(components)),
    )
}

/// `/_folio/contract.json`: components, accepted config keys and emitted
/// routes under one envelope. Field order is the JSON key order.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthoringContract {
    pub folio_version: String,
    pub mdx_contract_version: String,
    pub generated_at: String,
    pub instructions: String,
    pub components: Vec<ContractComponent>,
    pub config_keys: Vec<String>,
    pub routes: Vec<String>,
}

/// Keys `folio-config` knows only so the loader can warn that this release
/// ignores them: `plugins`, and the `FOLIO_EXPERIMENTAL`-gated `i18n` and
/// `versions`. The contract never offers them to an author.
pub const UNPUBLISHED_CONFIG_KEYS: [&str; 3] = ["plugins", "i18n", "versions"];

/// The `configKeys` a build publishes: every key `folio-config` knows minus
/// `UNPUBLISHED_CONFIG_KEYS`.
pub fn contract_config_keys() -> Vec<&'static str> {
    folio_config::known_config_keys()
        .into_iter()
        .filter(|key| !UNPUBLISHED_CONFIG_KEYS.contains(key))
        .collect()
}

/// `config_keys` and `routes` are sorted and de-duplicated;
/// `UNPUBLISHED_CONFIG_KEYS` are never published.
pub fn build_authoring_contract(
    folio_version: &str,
    generated_at: &str,
    components: &[ComponentDefinition],
    config_keys: impl IntoIterator<Item = String>,
    routes: impl IntoIterator<Item = String>,
) -> AuthoringContract {
    AuthoringContract {
        folio_version: folio_version.to_string(),
        mdx_contract_version: FOLIO_MDX_CONTRACT_VERSION.to_string(),
        generated_at: generated_at.to_string(),
        instructions: AUTHORING_CONTRACT_INSTRUCTIONS.to_string(),
        components: build_contract(components),
        config_keys: config_keys
            .into_iter()
            .filter(|key| !UNPUBLISHED_CONFIG_KEYS.contains(&key.as_str()))
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect(),
        routes: routes
            .into_iter()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect(),
    }
}

/// The published file text: two-space JSON plus a trailing newline, UTF-8.
pub fn render_authoring_contract(
    folio_version: &str,
    generated_at: &str,
    components: &[ComponentDefinition],
    config_keys: impl IntoIterator<Item = String>,
    routes: impl IntoIterator<Item = String>,
) -> String {
    let contract =
        build_authoring_contract(folio_version, generated_at, components, config_keys, routes);
    pretty(&contract) + "\n"
}

/// The `required` names that `template_dir/mdx-components.tsx` does not wire
/// as a mapping entry (a missing file misses every name). A heuristic: it
/// cannot see components injected through a `{...spread}`.
pub fn validate_template_mdx_contract(template_dir: &Path, required: &[String]) -> Vec<String> {
    let Ok(content) = std::fs::read_to_string(template_dir.join("mdx-components.tsx")) else {
        return required.to_vec();
    };
    let code = strip_import_statements(&strip_js_comments(&content));
    required
        .iter()
        .filter(|name| !has_component_entry(&code, name))
        .cloned()
        .collect()
}

#[cfg(test)]
#[path = "contract_tests.rs"]
mod tests;
