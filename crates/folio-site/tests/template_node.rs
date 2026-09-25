//! The bundled template's JavaScript and TypeScript helpers driven by Node
//! (skipped when `node` is absent or cannot import TypeScript directly).

mod common;

use std::path::Path;
use std::process::Command;

fn node_available() -> bool {
    Command::new("node")
        .arg("--version")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

/// Run `node args...`; `Ok(stdout)`, `Err(None)` when Node cannot load TypeScript, `Err(Some(stderr))` otherwise.
fn run_node(args: &[&str], cwd: &Path) -> Result<String, Option<String>> {
    let output = Command::new("node")
        .args(args)
        .current_dir(cwd)
        .output()
        .expect("node runs");
    if output.status.success() {
        return Ok(String::from_utf8_lossy(&output.stdout).into_owned());
    }
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    if stderr.contains("ERR_UNKNOWN_FILE_EXTENSION") {
        Err(None)
    } else {
        Err(Some(stderr))
    }
}

fn driver_json(dir: &Path, script: &str, module: &Path) -> Option<serde_json::Value> {
    let driver = common::write(dir, "driver.mjs", script);
    match run_node(
        &[
            "--no-warnings",
            driver.to_str().unwrap(),
            module.to_str().unwrap(),
        ],
        dir,
    ) {
        Ok(stdout) => Some(serde_json::from_str(stdout.trim()).expect("driver prints json")),
        Err(None) => None,
        Err(Some(stderr)) => panic!("node driver failed:\n{stderr}"),
    }
}

#[test]
fn docs_route_params_expand_index_html_and_underscore_aliases() {
    if !node_available() {
        return;
    }
    let helper = common::bundled_template().join("lib/docs-route-params.js");
    let helper_url = format!("file://{}", helper.display());
    let script = format!(
        r##"
import {{ expandStaticParams, isDisabledMdxPath, isUnderscoreAlias, normalizeMdxPath }} from {helper_url:?}
const assert = (condition, message) => {{ if (!condition) throw new Error(message) }}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b)
assert(same(normalizeMdxPath(["index.html"]), []), "index.html should resolve to the docs root")
assert(same(normalizeMdxPath(["components", "index.html"]), ["components"]), "nested index.html should resolve to its directory route")
assert(same(normalizeMdxPath(["source", "common_errors"]), ["source", "common-errors"]), "hand-written docs paths should accept underscore aliases")
assert(same(normalizeMdxPath(["source", "common_errors", "index.html"]), ["source", "common-errors"]), "underscore aliases should compose with index.html aliases")
assert(same(normalizeMdxPath(["api-reference", "example_package", "module_name"]), ["api-reference", "example_package", "module_name"]), "API reference names keep underscores")
assert(isUnderscoreAlias(["source", "common_errors"]) && isUnderscoreAlias(["source", "common_errors", "index.html"]), "underscore paths are aliases")
assert(!isUnderscoreAlias(["source", "common-errors"]) && !isUnderscoreAlias([]) && !isUnderscoreAlias(undefined), "hyphenated paths and the root are not aliases")
assert(!isUnderscoreAlias(["api-reference", "example_package"]), "API reference names are not aliases")
assert(isDisabledMdxPath(["i18n"]) && isDisabledMdxPath(["i18n", "index.html"]) && isDisabledMdxPath(["versioning"]), "gated routes are recognized")
for (const path of [["configuration"], ["roadmap"], ["landing"], ["plugins"], ["api-reference", "folio", "plugins", "roadmap"]]) {{
  assert(!isDisabledMdxPath(path), `released route must not be gated: ${{path.join("/")}}`)
}}
const params = expandStaticParams(
  [{{ mdxPath: [""] }}, {{ mdxPath: ["components"] }}, {{ mdxPath: ["source", "common-errors"] }}, {{ mdxPath: ["api-reference", "example_package"] }}, {{ lang: "en", mdxPath: ["guide"] }}],
  {{ includeIndexHtmlAliases: true, includeDisabledParams: true }},
)
const has = (path, extra = () => true) => params.some((p) => same(p.mdxPath, path) && extra(p))
assert(has([]), "root param should be normalized")
assert(has(["index.html"]), "root index.html alias should be included")
assert(has(["components", "index.html"]), "nested index.html alias should be included")
assert(has(["source", "common_errors"]), "underscore aliases should be included for hand-written docs routes")
assert(has(["source", "common_errors", "index.html"]), "underscore index.html aliases should be included")
assert(!has(["api-reference", "example-package"]), "API reference static params should not get hyphenated aliases")
assert(has(["guide", "index.html"], (p) => p.lang === "en"), "locale params should keep their non-route fields on aliases")
assert(has(["i18n"]) && has(["i18n", "index.html"]) && has(["versioning"]), "disabled routes are included for dev export requests")
const production = expandStaticParams(
  [{{ mdxPath: [""] }}, {{ mdxPath: ["components"] }}, {{ mdxPath: ["source", "common-errors"] }}],
  {{ includeIndexHtmlAliases: false, includeDisabledParams: false }},
)
assert(!production.some((p) => p.mdxPath.includes("index.html")), "index.html aliases stay out of production exports")
assert(!production.some((p) => p.mdxPath.includes("i18n")), "disabled params stay out of production exports")
assert(production.some((p) => same(p.mdxPath, ["source", "common_errors"])), "underscore aliases are generated for static exports")
"##
    );
    if let Err(Some(stderr)) = run_node(
        &["--input-type=module", "--eval", &script],
        &common::bundled_template(),
    ) {
        panic!("{stderr}");
    }
}

const REGISTRY_DRIVER: &str = r##"
import { pathToFileURL } from "node:url"
const [registryPath] = process.argv.slice(2)
const { registerPreset, registerGroup, getPresets, getGroups, groupPresetsForDisplay } = await import(pathToFileURL(registryPath).href)
const theme = { preview: { light: "#fff", dark: "#000" }, radius: "0", style: {}, light: {}, dark: {} }
const makePreset = (id, name = id) => ({ id, name, description: "", scene: "", preview: { light: "#fff", dark: "#000" }, defaultOptions: {}, controls: [], resolve: () => theme })
registerPreset(makePreset("atlas", "Atlas"))
registerPreset(makePreset("beacon", "Beacon"))
registerPreset(makePreset("atlas", "Customized Atlas"), "project")
registerPreset(makePreset("ext-preset", "Extension"), "someGroup")
registerPreset(makePreset("loose", "Loose"))
registerGroup("project", "Project", ["atlas"])
registerGroup("someGroup", "Some Group", [])
registerGroup("reference", "Reference", ["atlas", "beacon"])
registerGroup("empty", "Empty", [])
const presets = getPresets()
const groups = getGroups()
const display = groupPresetsForDisplay(groups, presets)
console.log(JSON.stringify({
  atlasEntries: presets.filter((p) => p.id === "atlas").map((p) => p.name),
  someGroup: groups.find((g) => g.id === "someGroup"),
  display: display.map((g) => ({ id: g.id, label: g.label, presetNames: g.presets.map((p) => p.name) })),
}))
"##;

#[test]
fn preset_registry_is_last_wins_and_display_dedups_with_a_fallback_group() {
    if !node_available() {
        return;
    }
    let dir = tempfile::tempdir().unwrap();
    let Some(data) = driver_json(
        dir.path(),
        REGISTRY_DRIVER,
        &common::bundled_template().join("theme/preset-registry.ts"),
    ) else {
        return;
    };
    assert_eq!(
        data["atlasEntries"],
        serde_json::json!(["Customized Atlas"])
    );
    assert_eq!(data["someGroup"]["label"], "Some Group");
    assert_eq!(
        data["someGroup"]["presetIds"],
        serde_json::json!(["ext-preset"])
    );
    let display = data["display"].as_array().unwrap();
    let by_id = |id: &str| {
        display
            .iter()
            .find(|g| g["id"] == id)
            .map(|g| g["presetNames"].clone())
    };
    let atlas: Vec<(String, String)> = display
        .iter()
        .flat_map(|g| {
            g["presetNames"].as_array().unwrap().iter().map(move |n| {
                (
                    g["id"].as_str().unwrap().to_string(),
                    n.as_str().unwrap().to_string(),
                )
            })
        })
        .filter(|(_, name)| name.ends_with("Atlas"))
        .collect();
    assert_eq!(
        atlas,
        [("project".to_string(), "Customized Atlas".to_string())]
    );
    assert_eq!(by_id("reference"), Some(serde_json::json!(["Beacon"])));
    assert_eq!(by_id("someGroup"), Some(serde_json::json!(["Extension"])));
    assert_eq!(by_id("other"), Some(serde_json::json!(["Loose"])));
    assert_eq!(by_id("empty"), None);
}

const BOOTSTRAP_DRIVER: &str = r##"
import { pathToFileURL } from "node:url"
const [typesPath] = process.argv.slice(2)
const { buildBootstrapPresets, countPresetOptionCombinations, MAX_BOOTSTRAP_COMBINATIONS } = await import(pathToFileURL(typesPath).href)
const theme = { preview: { light: "", dark: "" }, radius: "0", style: {}, light: {}, dark: {} }
const makeControl = (id, count) => ({ id, label: id, options: Array.from({ length: count }, (_, i) => ({ label: `${id}${i}`, value: `${id}${i}` })) })
const makePreset = (id, controls, counter) => ({
  id, name: id, description: "", scene: "", preview: { light: "", dark: "" },
  defaultOptions: Object.fromEntries(controls.map((control) => [control.id, control.options[0].value])),
  controls,
  resolve: () => { counter.count += 1; return theme },
})
const smallCounter = { count: 0 }
const small = makePreset("small", [makeControl("a", 2), makeControl("b", 2)], smallCounter)
const boundaryCounter = { count: 0 }
const boundary = makePreset("boundary", Array.from({ length: 9 }, (_, i) => makeControl(`b${i}`, 2)), boundaryCounter)
const overCounter = { count: 0 }
const over = makePreset("over", [makeControl("a", 8), makeControl("b", 8), makeControl("c", 9)], overCounter)
const hugeCounter = { count: 0 }
const huge = makePreset("huge", Array.from({ length: 10 }, (_, i) => makeControl(`h${i}`, 10)), hugeCounter)
const bootstrap = buildBootstrapPresets([small, boundary, over, huge])
const byId = Object.fromEntries(bootstrap.map((preset) => [preset.id, preset]))
console.log(JSON.stringify({
  max: MAX_BOOTSTRAP_COMBINATIONS,
  smallThemeKeyCount: Object.keys(byId.small.themes).length,
  boundaryThemeKeyCount: Object.keys(byId.boundary.themes).length,
  overThemeKeys: Object.keys(byId.over.themes),
  overDefaultKey: byId.over.defaultKey,
  hugeThemeKeys: Object.keys(byId.huge.themes),
  hugeDefaultKey: byId.huge.defaultKey,
  hugeResolveCalls: hugeCounter.count,
  overCombinationCount: countPresetOptionCombinations(over),
  hugeCombinationCount: countPresetOptionCombinations(huge),
}))
"##;

#[test]
fn bootstrap_presets_cap_combinations_without_enumerating_them() {
    if !node_available() {
        return;
    }
    let dir = tempfile::tempdir().unwrap();
    let Some(data) = driver_json(
        dir.path(),
        BOOTSTRAP_DRIVER,
        &common::bundled_template().join("theme/preset-types.ts"),
    ) else {
        return;
    };
    assert_eq!(data["max"], 512);
    assert_eq!(data["smallThemeKeyCount"], 4);
    assert_eq!(data["boundaryThemeKeyCount"], 512);
    assert_eq!(data["overCombinationCount"], 576);
    assert_eq!(
        data["overThemeKeys"],
        serde_json::json!([data["overDefaultKey"]])
    );
    assert_eq!(data["hugeCombinationCount"], 10_000_000_000u64);
    assert_eq!(
        data["hugeThemeKeys"],
        serde_json::json!([data["hugeDefaultKey"]])
    );
    assert_eq!(data["hugeResolveCalls"], 1);
}
