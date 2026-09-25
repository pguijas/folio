//! The bundled template and the fixtures agree with the manifest: entry
//! names, import lines, the required contract members, the baseline fixture
//! bytes, the funnel icon whitelist, the landing section types and the data
//! modules the built-ins overwrite.

use std::collections::BTreeMap;
use std::path::PathBuf;

use folio_plugins::drift::{check_template_drift, template_component_entry_names};
use folio_plugins::{
    build_contract, required_component_names, validate_template_mdx_contract, BUILTIN_COMPONENTS,
};

fn repo() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn template() -> PathBuf {
    repo().join("template")
}

fn read(path: PathBuf) -> String {
    std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()))
}

#[test]
fn manifest_imports_and_entries_are_present_and_ordered_in_the_template() {
    let content = read(template().join("mdx-components.tsx"));
    let mut by_module: Vec<(String, Vec<String>)> = Vec::new();
    for component in BUILTIN_COMPONENTS.iter() {
        match by_module
            .iter_mut()
            .find(|(m, _)| *m == component.import_path)
        {
            Some((_, names)) => names.push(component.imported_name().to_string()),
            None => by_module.push((
                component.import_path.clone(),
                vec![component.imported_name().to_string()],
            )),
        }
    }
    for (module, names) in by_module {
        let line = format!("import {{ {} }} from \"{module}\"", names.join(", "));
        assert!(
            content.contains(&line),
            "manifest import drifted from template: {line}"
        );
    }
    let positions: Vec<usize> = BUILTIN_COMPONENTS
        .iter()
        .map(|c| content.find(&format!("    {},", c.name)).expect(&c.name))
        .collect();
    let mut sorted = positions.clone();
    sorted.sort_unstable();
    assert_eq!(positions, sorted, "entry order drifted from template");
    assert_eq!(check_template_drift(&content), Vec::<String>::new());
    assert_eq!(template_component_entry_names(&content).len(), 40);
}

#[test]
fn drift_flags_a_missing_builtin_and_ignores_comments_and_import_lists() {
    let content = read(template().join("mdx-components.tsx"));
    let drift = check_template_drift(&content.replace("    ComparisonMatrix,\n", ""));
    assert_eq!(drift.len(), 1);
    assert!(
        drift[0].contains("ComparisonMatrix")
            && drift[0].contains("no entry in mdx-components.tsx")
    );
    let noisy = format!(
        "import {{\n  IgnoredWidget,\n}} from \"./ignored\"\n{}",
        content.replace(
            "    ...components,",
            "    // GhostWidget,\n    ...components,"
        )
    );
    assert_eq!(check_template_drift(&noisy), Vec::<String>::new());
}

#[test]
fn bundled_template_satisfies_the_required_mdx_contract() {
    let required = required_component_names(&BUILTIN_COMPONENTS);
    assert_eq!(
        validate_template_mdx_contract(&template(), &required),
        Vec::<String>::new()
    );
    let content = read(template().join("mdx-components.tsx"));
    for name in required {
        assert!(content.contains(&format!("    {name},")), "{name}");
    }
}

#[test]
fn contract_matches_the_baseline_fixture_bytes() {
    // The fixture is the contract keyed by name with every key sorted, two-space
    // indent and a trailing newline; regenerate with FOLIO_UPDATE_GOLDEN=1.
    let payload: BTreeMap<String, serde_json::Value> = build_contract(&BUILTIN_COMPONENTS)
        .into_iter()
        .map(|entry| {
            let value = serde_json::to_value(&entry).unwrap();
            let mut sorted: BTreeMap<String, serde_json::Value> =
                value.as_object().unwrap().clone().into_iter().collect();
            let props: BTreeMap<String, serde_json::Value> = sorted["props"]
                .as_object()
                .unwrap()
                .clone()
                .into_iter()
                .collect();
            sorted.insert("props".to_string(), serde_json::to_value(props).unwrap());
            (entry.name, serde_json::to_value(sorted).unwrap())
        })
        .collect();
    let expected = serde_json::to_string_pretty(&payload).unwrap() + "\n";
    let fixture =
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/mdx_contract_baseline.json");
    if std::env::var_os("FOLIO_UPDATE_GOLDEN").is_some() {
        std::fs::write(&fixture, &expected).unwrap();
    }
    assert_eq!(
        read(fixture),
        expected,
        "mdx_contract_baseline.json is stale; regenerate with FOLIO_UPDATE_GOLDEN=1"
    );
    assert_eq!(payload.len(), 22);
}

#[test]
fn funnel_icon_keys_match_the_template_map() {
    let content = read(template().join("components/landing/sections.tsx"));
    let start = content
        .find("const FUNNEL_ICONS: Record<string, IconSvgElement> = {")
        .expect("FUNNEL_ICONS map in sections.tsx");
    let block = &content[start..];
    let block = &block[..block.find("\n}").unwrap()];
    let mut template_keys: Vec<&str> = block
        .lines()
        .skip(1)
        .filter_map(|line| line.trim().split(':').next())
        .filter(|k| !k.is_empty())
        .collect();
    template_keys.sort_unstable();
    let mut ours = folio_plugins::landing::FUNNEL_ICONS.to_vec();
    ours.sort_unstable();
    assert_eq!(
        template_keys, ours,
        "funnel icon keys drifted between landing.rs and sections.tsx"
    );
}

#[test]
fn landing_section_types_match_the_template_registry() {
    let content = read(template().join("components/landing/sections.tsx"));
    let start = content
        .find("export const LANDING_SECTION_COMPONENTS: Record<")
        .expect("LANDING_SECTION_COMPONENTS map in sections.tsx");
    let block = &content[start..];
    let block = &block[block.find("> = {").unwrap()..];
    let block = &block[..block.find("\n}").unwrap()];
    let mut template_types: Vec<&str> = block
        .lines()
        .skip(1)
        .filter_map(|line| line.trim().split(':').next())
        .map(|key| key.trim_matches('"'))
        .filter(|k| !k.is_empty())
        .collect();
    template_types.sort_unstable();
    assert_eq!(
        template_types,
        folio_plugins::landing::SECTION_TYPES.to_vec(),
        "landing section types drifted between landing.rs and sections.tsx"
    );
}

#[test]
fn template_ships_the_data_modules_the_builtins_overwrite() {
    let roadmap = read(template().join("lib/roadmap-data.ts"));
    assert!(roadmap.contains("project?: string") && !roadmap.contains("milestone"));
    assert!(roadmap.contains("export const roadmapPhases: RoadmapPhase[] = []"));
    // The placeholder is the plugin's type block minus its comment lines.
    let types_without_comments: String = folio_plugins::roadmap::ROADMAP_TYPES
        .lines()
        .filter(|l| !l.starts_with("//"))
        .collect::<Vec<_>>()
        .join("\n");
    assert!(
        roadmap.starts_with(types_without_comments.trim_end()),
        "{roadmap}"
    );
    let utils = read(template().join("lib/roadmap-utils.ts"));
    assert!(utils.contains(&format!(
        "export const DEFAULT_PROJECT_KEY = \"{}\"",
        folio_plugins::roadmap::DEFAULT_PROJECT
    )));
    let openapi = read(template().join("lib/openapi-data.ts"));
    assert!(openapi.starts_with(folio_plugins::openapi::OPENAPI_TYPES));
    assert!(openapi.contains("export const openApiSources: OpenApiSource[] = []"));
    let component = read(template().join("components/openapi-reference.tsx"));
    assert!(component.contains("from \"@/lib/openapi-data\""));
    assert!(component.contains("type OpenApiSource"));
    assert!(component.contains("methodStyles"));
    assert!(component.contains("OpenAPI"));
}
