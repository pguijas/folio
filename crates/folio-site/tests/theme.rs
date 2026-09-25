//! `theme/project-theme.ts` rendered from a full project theme config.

mod common;

use folio_site::theme::render_project_theme_module;
use serde_json::json;

const THEME_YAML: &str = r#"
theme:
  preset: p2pfl
  name: P2PFL
  description: Operational docs theme
  scene: Maintainers inspect experiments, nodes, and APIs in one compact surface.
  preview:
    light: oklch(0.490 0.130 285)
    dark: oklch(0.720 0.100 285)
  radius: 0.5rem
  tune:
    fontId: geist
    contentWidthId: wide
    rhythmId: compact
    codeTreatmentId: terminal
  style:
    --folio-content-max-width: 74rem
    --folio-body-line-height: "1.58"
  tokens:
    light:
      --background: oklch(0.985 0.008 80)
      --foreground: oklch(0.175 0.008 75)
      --brand-accent: oklch(0.680 0.110 160)
    dark:
      --background: oklch(0.155 0.010 75)
      --foreground: oklch(0.950 0.008 80)
  variants:
    palette:
      label: Palette
      default: default
      options:
        default:
          label: Default
          swatch: oklch(0.490 0.130 285)
        midnight:
          label: Midnight
          swatch: oklch(0.680 0.180 200)
          tokens:
            light:
              --background: oklch(0.985 0.008 250)
              --primary: oklch(0.480 0.160 200)
            dark:
              --background: oklch(0.095 0.020 250)
              --primary: oklch(0.680 0.180 200)
        ocean:
          label: Ocean
          preview:
            light: oklch(0.480 0.140 245)
"#;

#[test]
fn project_theme_module_carries_preset_variants_and_overrides() {
    let dir = tempfile::tempdir().unwrap();
    let config = common::config(dir.path(), THEME_YAML);
    let mut warnings = Vec::new();
    let module = render_project_theme_module(&config, &mut warnings);
    assert!(warnings.is_empty());

    let preset = common::extract_ts_object(
        &module,
        "const projectPresetConfig: Omit<ThemePreset, \"resolve\"> =",
    );
    assert_eq!(preset["id"], "p2pfl");
    assert_eq!(preset["name"], "P2PFL");
    assert_eq!(preset["defaultOptions"], json!({"palette": "default"}));
    assert_eq!(preset["defaultRadiusIndex"], 2);
    assert_eq!(
        preset["preview"],
        json!({"light": "oklch(0.490 0.130 285)", "dark": "oklch(0.720 0.100 285)"})
    );
    let keys: Vec<&str> = preset
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        keys,
        [
            "id",
            "name",
            "description",
            "scene",
            "preview",
            "defaultOptions",
            "defaultRadiusIndex",
            "defaultCustomization",
            "controls"
        ]
    );
    let control = &preset["controls"][0];
    assert_eq!(control["id"], "palette");
    assert_eq!(control["label"], "Palette");
    let options: Vec<&str> = control["options"]
        .as_array()
        .unwrap()
        .iter()
        .map(|o| o["value"].as_str().unwrap())
        .collect();
    assert_eq!(options, ["default", "midnight", "ocean"]);
    assert_eq!(control["options"][1]["swatch"], "oklch(0.680 0.180 200)");
    assert!(control["options"][2].get("swatch").is_none());

    let variants = common::extract_ts_object(&module, "}>> = ");
    assert_eq!(variants["palette"]["ocean"], json!({}));
    assert_eq!(
        variants["palette"]["midnight"]["preview"],
        json!({"light": "oklch(0.680 0.180 200)", "dark": "oklch(0.680 0.180 200)"})
    );
    assert_eq!(
        variants["palette"]["midnight"]["light"]["--primary"],
        "oklch(0.480 0.160 200)"
    );

    let style = common::extract_ts_object(
        &module,
        "const projectStyleOverrides: Record<string, string> = ",
    );
    assert_eq!(style["--font-sans"], "var(--font-geist-sans)");
    assert_eq!(style["--font-mono"], "var(--font-geist-mono)");
    assert!(style["--folio-code-font-family"]
        .as_str()
        .unwrap()
        .starts_with("var(--font-geist-mono),"));
    assert_eq!(style["--folio-content-max-width"], "74rem");
    let light = common::extract_ts_object(&module, "const projectLightOverrides: ThemeVars = ");
    assert_eq!(light["--brand-accent"], "oklch(0.680 0.110 160)");

    let default_config = common::extract_ts_object(&module, "} = ");
    assert_eq!(default_config["presetId"], "p2pfl");
    assert_eq!(default_config["radiusIndex"], 2);
    assert_eq!(
        default_config["optionsByPreset"]["p2pfl"],
        json!({"palette": "default"})
    );
    assert_eq!(default_config["customization"]["fontId"], "geist");
    assert_eq!(
        default_config["customization"]["codeTreatmentId"],
        "terminal"
    );
    let keys: Vec<&str> = default_config
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        keys,
        [
            "presetId",
            "radiusIndex",
            "customization",
            "optionsByPreset"
        ]
    );

    for needle in [
        "import type { ThemePreset, ThemeStyle, ThemeVars } from \"./preset-types\"\n\n",
        "export const projectThemePreset: ThemePreset | null = {",
        "const selectedValue = options[control.id] ?? projectPresetConfig.defaultOptions[control.id]",
        "resolve(options) {",
        "projectBaseStyle",
        "projectBaseLight",
        "projectBaseDark",
        "  preview: {\"light\": \"oklch(0.490 0.130 285)\", \"dark\": \"oklch(0.720 0.100 285)\"},\n  radius: \"0.5rem\",\n",
    ] {
        assert!(module.contains(needle), "missing {needle:?}");
    }
    assert!(!module.contains("satisfies Omit<ThemePreset"));
    assert!(module.ends_with("}\n") && !module.ends_with("\n\n"));
}

#[test]
fn customised_builtin_preset_keeps_the_builtin_id() {
    let dir = tempfile::tempdir().unwrap();
    let config = common::config(dir.path(), "theme:\n  preset: atlas\n  tokens:\n    light:\n      --primary: oklch(0.51 0.14 170)\n    dark:\n      --primary: oklch(0.72 0.17 170)\n");
    let module = render_project_theme_module(&config, &mut Vec::new());
    let preset = common::extract_ts_object(
        &module,
        "const projectPresetConfig: Omit<ThemePreset, \"resolve\"> =",
    );
    assert_eq!(preset["id"], "atlas");
    assert_eq!(preset["name"], "TestProject");
    assert_eq!(preset["description"], "TestProject project theme");
    assert_eq!(
        preset["scene"],
        "TestProject documentation uses a project-owned visual system."
    );
    assert_eq!(
        preset["preview"],
        json!({"light": "oklch(0.51 0.14 170)", "dark": "oklch(0.72 0.17 170)"})
    );
    assert_eq!(
        common::extract_ts_object(&module, "} = ")["presetId"],
        "atlas"
    );
}

#[test]
fn bare_builtin_preset_renders_a_null_preset() {
    let dir = tempfile::tempdir().unwrap();
    let config = common::config(dir.path(), "theme:\n  preset: beacon\n");
    let module = render_project_theme_module(&config, &mut Vec::new());
    assert_eq!(
        module,
        "import type { ThemePreset, ThemeStyle, ThemeVars } from \"./preset-types\"\n\nexport const projectThemePreset: ThemePreset | null = null\n\nexport const projectThemeDefaultConfig: {\n  presetId?: string\n  radiusIndex?: number\n  optionsByPreset?: Record<string, Record<string, string>>\n  customization?: Record<string, string>\n} = {\n  \"presetId\": \"beacon\"\n}\n"
    );
}

#[test]
fn variant_option_style_keys_are_namespaced() {
    let dir = tempfile::tempdir().unwrap();
    let config = common::config(
        dir.path(),
        "theme:\n  preset: custom\n  name: Custom\n  variants:\n    density:\n      label: Density\n      default: cozy\n      options:\n        cozy:\n          label: Cozy\n          style:\n            --content-max-width: 70rem\n            --folio-body-line-height: \"1.7\"\n",
    );
    let module = render_project_theme_module(&config, &mut Vec::new());
    let variants = common::extract_ts_object(&module, "}>> = ");
    assert_eq!(
        variants["density"]["cozy"]["style"],
        json!({"--folio-content-max-width": "70rem", "--folio-body-line-height": "1.7"})
    );
}
