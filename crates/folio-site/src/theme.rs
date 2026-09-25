//! The project theme contract: the base style/token tables, the generated
//! `theme/project-theme.ts` and `theme/theme-contract.generated.ts`, and the
//! `theme.package` validator.

use std::path::Path;

use folio_config::{DocsConfig, ThemeVariantOption};
pub use folio_config::{THEME_RADIUS_OPTIONS, THEME_TUNE_KEYS};
use serde_json::{Map, Value};

use crate::json;
use crate::SiteError;

/// Builtin ThemeConfigurator preset ids.
pub const BUILTIN_THEME_PRESETS: [&str; 11] = [
    "aperture",
    "atlas",
    "beacon",
    "canopy",
    "carbon",
    "draftline",
    "ledger",
    "organic-editorial",
    "proof",
    "stacks",
    "workshop",
];

/// Former preset ids the bundled configurator maps onto a current preset
/// (`LEGACY_PRESET_IDS` in `components/theme-configurator.tsx`).
pub const LEGACY_THEME_PRESETS: [&str; 14] = [
    "archive",
    "atelier",
    "carbon",
    "depth",
    "draft",
    "flora",
    "folio",
    "ledger",
    "openai",
    "oxide",
    "press",
    "promptix",
    "reference",
    "signal",
];

/// Preset ids a theme package or overlay declares: every `id: "…"` (or
/// `'…'`) in the TypeScript under its `theme/` directory, except a control's,
/// which `label:` follows. Generous on purpose: it only ever accepts more.
pub fn declared_preset_ids(package_dir: &Path) -> Vec<String> {
    let pattern = crate::re(r#"\bid:\s*["']([^"'\n]+)["']\s*,?\s*(\w+)?"#);
    let mut ids: Vec<String> = crate::fs::files_under(&package_dir.join("theme"))
        .into_iter()
        .filter(|path| {
            path.extension()
                .is_some_and(|ext| ext == "ts" || ext == "tsx")
        })
        .filter_map(|path| std::fs::read_to_string(path).ok())
        .flat_map(|text| {
            pattern
                .captures_iter(&text)
                .filter(|caps| caps.get(2).is_none_or(|next| next.as_str() != "label"))
                .map(|caps| caps[1].to_string())
                .collect::<Vec<_>>()
        })
        .collect();
    ids.sort();
    ids.dedup();
    ids
}

/// `theme.preset` names a preset the bundled configurator will show: a
/// built-in, a renamed built-in, the project preset `docs.yaml` defines, or
/// one of `declared` (a theme package's). Anything else would fall back to
/// the default preset without a word.
pub fn check_theme_preset(config: &DocsConfig, declared: &[String]) -> Result<(), SiteError> {
    let preset = config.theme.preset.as_str();
    if BUILTIN_THEME_PRESETS.contains(&preset)
        || LEGACY_THEME_PRESETS.contains(&preset)
        || declared.iter().any(|id| id == preset)
        || has_project_preset(config)
    {
        return Ok(());
    }
    let known: Vec<&str> = BUILTIN_THEME_PRESETS
        .iter()
        .copied()
        .chain(
            declared
                .iter()
                .map(String::as_str)
                .filter(|id| !BUILTIN_THEME_PRESETS.contains(id)),
        )
        .collect();
    let listed: Vec<String> = known.iter().map(|id| format!("'{id}'")).collect();
    Err(SiteError::Value(format!(
        "theme.preset must be one of {}; got '{preset}'{}. A new preset id also needs theme.name, theme.tokens or theme.style to define it",
        listed.join(", "),
        folio_config::did_you_mean(preset, known.iter().copied())
    )))
}

/// Base style properties, in `ThemeStyle` member order.
pub const PROJECT_THEME_BASE_STYLE: [(&str, &str); 35] = [
    ("--folio-heading-font-family", "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"),
    ("--folio-body-font-family", "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"),
    ("--folio-code-font-family", "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace"),
    ("--folio-heading-letter-spacing", "0"),
    ("--folio-heading-weight", "700"),
    ("--folio-body-line-height", "1.62"),
    ("--folio-font-size-base", "1rem"),
    ("--folio-card-shadow", "var(--shadow-sm, none)"),
    ("--folio-card-border-width", "1px"),
    ("--folio-card-padding", "1.25rem"),
    ("--folio-card-hover-shadow", "var(--shadow-md, none)"),
    ("--folio-card-backdrop", "none"),
    ("--folio-card-opacity", "1"),
    ("--folio-code-border-radius", "0.5rem"),
    ("--folio-code-border", "1px solid var(--border)"),
    ("--folio-code-bg", "color-mix(in oklch, var(--card) 84%, var(--background))"),
    ("--folio-code-foreground", "inherit"),
    ("--folio-code-shadow", "var(--shadow-sm, none)"),
    ("--folio-h2-border", "1px solid var(--border)"),
    ("--folio-h2-transform", "none"),
    ("--folio-h2-letter-spacing", "0"),
    ("--folio-h2-weight", "700"),
    ("--folio-h2-padding-left", "0"),
    ("--folio-h2-border-left", "none"),
    ("--folio-link-decoration", "none"),
    ("--folio-section-gap", "2.35rem"),
    ("--folio-content-max-width", "62rem"),
    ("--folio-workspace-shell-padding", "0px"),
    ("--folio-workspace-shell-border", "0 solid transparent"),
    ("--folio-workspace-shell-shadow", "none"),
    ("--folio-workspace-shell-background", "var(--background)"),
    ("--folio-workspace-shell-surface", "transparent"),
    ("--folio-workspace-shell-topbar", "var(--background)"),
    ("--folio-workspace-shell-topbar-blur", "none"),
    ("--folio-workspace-shell-topbar-border", "1px solid var(--border)"),
];

/// Style overrides `theme.tune.fontId: geist` adds.
pub const THEME_TUNE_STYLE_OVERRIDES_GEIST: [(&str, &str); 5] = [
    ("--font-sans", "var(--font-geist-sans)"),
    ("--font-mono", "var(--font-geist-mono)"),
    ("--folio-heading-font-family", "var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"),
    ("--folio-body-font-family", "var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif"),
    ("--folio-code-font-family", "var(--font-geist-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace"),
];

/// Light base tokens.
pub const PROJECT_THEME_BASE_LIGHT: [(&str, &str); 34] = [
    ("--background", "oklch(0.985 0.008 80)"),
    ("--foreground", "oklch(0.175 0.008 75)"),
    ("--card", "oklch(0.995 0.004 80)"),
    ("--card-foreground", "oklch(0.175 0.008 75)"),
    ("--popover", "oklch(0.995 0.004 80)"),
    ("--popover-foreground", "oklch(0.175 0.008 75)"),
    ("--primary", "oklch(0.490 0.130 285)"),
    ("--primary-foreground", "oklch(0.985 0.008 285)"),
    ("--secondary", "oklch(0.945 0.012 285)"),
    ("--secondary-foreground", "oklch(0.250 0.020 285)"),
    ("--muted", "oklch(0.955 0.008 80)"),
    ("--muted-foreground", "oklch(0.510 0.012 75)"),
    ("--accent", "oklch(0.490 0.130 285)"),
    ("--accent-foreground", "oklch(0.985 0.008 285)"),
    ("--destructive", "oklch(0.570 0.180 25)"),
    ("--border", "oklch(0.900 0.008 80)"),
    ("--input", "oklch(0.880 0.010 80)"),
    ("--ring", "oklch(0.650 0.040 285)"),
    ("--chart-1", "oklch(0.680 0.120 285)"),
    ("--chart-2", "oklch(0.680 0.110 200)"),
    ("--chart-3", "oklch(0.680 0.110 145)"),
    ("--chart-4", "oklch(0.700 0.110 70)"),
    ("--chart-5", "oklch(0.680 0.110 340)"),
    ("--chart-6", "oklch(0.680 0.110 240)"),
    ("--chart-7", "oklch(0.700 0.100 110)"),
    ("--chart-8", "oklch(0.680 0.110 315)"),
    ("--sidebar", "oklch(0.975 0.010 80)"),
    ("--sidebar-foreground", "oklch(0.175 0.008 75)"),
    ("--sidebar-primary", "oklch(0.490 0.130 285)"),
    ("--sidebar-primary-foreground", "oklch(0.985 0.008 285)"),
    ("--sidebar-accent", "oklch(0.945 0.012 285)"),
    ("--sidebar-accent-foreground", "oklch(0.250 0.020 285)"),
    ("--sidebar-border", "oklch(0.910 0.008 80)"),
    ("--sidebar-ring", "oklch(0.650 0.040 285)"),
];

/// Dark base tokens, same key order as the light table.
pub const PROJECT_THEME_BASE_DARK: [(&str, &str); 34] = [
    ("--background", "oklch(0.155 0.010 75)"),
    ("--foreground", "oklch(0.950 0.008 80)"),
    ("--card", "oklch(0.195 0.010 75)"),
    ("--card-foreground", "oklch(0.950 0.008 80)"),
    ("--popover", "oklch(0.195 0.010 75)"),
    ("--popover-foreground", "oklch(0.950 0.008 80)"),
    ("--primary", "oklch(0.720 0.100 285)"),
    ("--primary-foreground", "oklch(0.155 0.010 75)"),
    ("--secondary", "oklch(0.250 0.015 285)"),
    ("--secondary-foreground", "oklch(0.920 0.008 80)"),
    ("--muted", "oklch(0.235 0.010 75)"),
    ("--muted-foreground", "oklch(0.650 0.012 80)"),
    ("--accent", "oklch(0.720 0.100 285)"),
    ("--accent-foreground", "oklch(0.155 0.010 75)"),
    ("--destructive", "oklch(0.680 0.160 25)"),
    ("--border", "oklch(1 0.005 80 / 10%)"),
    ("--input", "oklch(1 0.005 80 / 14%)"),
    ("--ring", "oklch(0.600 0.050 285)"),
    ("--chart-1", "oklch(0.720 0.100 285)"),
    ("--chart-2", "oklch(0.720 0.100 200)"),
    ("--chart-3", "oklch(0.720 0.100 145)"),
    ("--chart-4", "oklch(0.740 0.100 70)"),
    ("--chart-5", "oklch(0.720 0.100 340)"),
    ("--chart-6", "oklch(0.720 0.100 240)"),
    ("--chart-7", "oklch(0.740 0.090 110)"),
    ("--chart-8", "oklch(0.720 0.100 315)"),
    ("--sidebar", "oklch(0.145 0.012 75)"),
    ("--sidebar-foreground", "oklch(0.950 0.008 80)"),
    ("--sidebar-primary", "oklch(0.720 0.100 285)"),
    ("--sidebar-primary-foreground", "oklch(0.155 0.010 75)"),
    ("--sidebar-accent", "oklch(0.220 0.015 285)"),
    ("--sidebar-accent-foreground", "oklch(0.950 0.008 80)"),
    ("--sidebar-border", "oklch(1 0.005 80 / 8%)"),
    ("--sidebar-ring", "oklch(0.600 0.050 285)"),
];

/// Paths a theme package may never ship; a trailing `/` marks a directory.
/// The three manifest files are reserved because the frontend build installs
/// with `--frozen-lockfile` against Folio's own lockfile: a package that
/// shipped its own would either be ignored or would re-enable the dependency
/// lifecycle scripts the pinned lockfile exists to control.
pub const RESERVED_PATHS: [&str; 9] = [
    "content/",
    "lib/folio-template.ts",
    "lib/folio-mdx-contract.ts",
    "theme/theme-contract.generated.ts",
    ".next/",
    "node_modules/",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
];

/// Reserved on top of `RESERVED_PATHS` for a package fetched from elsewhere.
/// A local package owning the Next config is a project deciding about its own
/// build; a stranger's package owning it is the shortest path from a one-line
/// config diff to arbitrary code in the build, so provenance decides.
pub const REMOTE_RESERVED_PATHS: [&str; 1] = ["next.config.mjs"];

const DEFAULT_RADIUS: &str = "0.5rem";

fn table(entries: &[(&str, &str)]) -> Map<String, Value> {
    entries
        .iter()
        .map(|(k, v)| (k.to_string(), Value::String(v.to_string())))
        .collect()
}

fn string_map<'a>(
    entries: impl IntoIterator<Item = (&'a String, &'a String)>,
) -> Map<String, Value> {
    entries
        .into_iter()
        .map(|(k, v)| (k.clone(), Value::String(v.clone())))
        .collect()
}

/// `--x` becomes `--folio-x` when that is a base style property.
pub fn namespace_style_key(key: &str) -> String {
    let namespaced = key.strip_prefix("--").map(|rest| format!("--folio-{rest}"));
    match namespaced {
        Some(candidate)
            if PROJECT_THEME_BASE_STYLE
                .iter()
                .any(|(k, _)| *k == candidate) =>
        {
            candidate
        }
        _ => key.to_string(),
    }
}

fn quoted_value(text: &str) -> String {
    if text.contains('\'') && !text.contains('"') {
        format!("\"{text}\"")
    } else {
        format!("'{}'", text.replace('\\', "\\\\").replace('\'', "\\'"))
    }
}

/// Index of `radius` on the shared scale; off-scale values warn and fall back
/// to `0.5rem`.
pub fn theme_radius_index(radius: &str, warnings: &mut Vec<String>) -> usize {
    if let Some(index) = THEME_RADIUS_OPTIONS.iter().position(|r| *r == radius) {
        return index;
    }
    warnings.push(format!(
        "theme radius {} is not on the shared radius scale; falling back to {DEFAULT_RADIUS}",
        quoted_value(radius)
    ));
    THEME_RADIUS_OPTIONS
        .iter()
        .position(|r| *r == DEFAULT_RADIUS)
        .expect("default on scale")
}

fn has_project_preset(config: &DocsConfig) -> bool {
    let theme = &config.theme;
    let customised = !theme.name.is_empty()
        || !theme.description.is_empty()
        || !theme.scene.is_empty()
        || !theme.preview.is_empty()
        || !theme.tokens.is_empty()
        || !theme.style.is_empty()
        || !theme.variants.is_empty();
    if BUILTIN_THEME_PRESETS.contains(&theme.preset.as_str()) {
        customised
    } else {
        customised || !theme.radius.is_empty()
    }
}

fn default_options(config: &DocsConfig) -> Map<String, Value> {
    config
        .theme
        .variants
        .iter()
        .map(|(id, control)| (id.clone(), Value::String(control.default.clone())))
        .collect()
}

fn controls(config: &DocsConfig) -> Value {
    Value::Array(
        config
            .theme
            .variants
            .iter()
            .map(|(id, control)| {
                let options: Vec<Value> = control
                    .options
                    .iter()
                    .map(|(option_id, option)| {
                        let mut entry = Map::new();
                        entry.insert("label".into(), Value::String(option.label.clone()));
                        entry.insert("value".into(), Value::String(option_id.clone()));
                        if !option.swatch.is_empty() {
                            entry.insert("swatch".into(), Value::String(option.swatch.clone()));
                        }
                        if !option.description.is_empty() {
                            entry.insert(
                                "description".into(),
                                Value::String(option.description.clone()),
                            );
                        }
                        Value::Object(entry)
                    })
                    .collect();
                let mut entry = Map::new();
                entry.insert("id".into(), Value::String(id.clone()));
                entry.insert("label".into(), Value::String(control.label.clone()));
                entry.insert(
                    "description".into(),
                    Value::String(control.description.clone()),
                );
                entry.insert("options".into(), Value::Array(options));
                Value::Object(entry)
            })
            .collect(),
    )
}

fn option_preview(option: &ThemeVariantOption) -> Map<String, Value> {
    let mut preview = string_map(option.preview.iter());
    if !option.swatch.is_empty() {
        for side in ["light", "dark"] {
            preview
                .entry(side)
                .or_insert_with(|| Value::String(option.swatch.clone()));
        }
    }
    preview
}

fn variant_themes(config: &DocsConfig) -> Map<String, Value> {
    config
        .theme
        .variants
        .iter()
        .map(|(control_id, control)| {
            let options: Map<String, Value> = control
                .options
                .iter()
                .map(|(option_id, option)| {
                    let mut theme = Map::new();
                    let preview = option_preview(option);
                    if preview.contains_key("light") && preview.contains_key("dark") {
                        theme.insert("preview".into(), Value::Object(preview));
                    }
                    if !option.style.is_empty() {
                        theme.insert(
                            "style".into(),
                            Value::Object(
                                option
                                    .style
                                    .iter()
                                    .map(|(k, v)| {
                                        (namespace_style_key(k), Value::String(v.clone()))
                                    })
                                    .collect(),
                            ),
                        );
                    }
                    for side in ["light", "dark"] {
                        if let Some(tokens) = option.tokens.get(side).filter(|t| !t.is_empty()) {
                            theme.insert(side.into(), Value::Object(string_map(tokens.iter())));
                        }
                    }
                    (option_id.clone(), Value::Object(theme))
                })
                .collect();
            (control_id.clone(), Value::Object(options))
        })
        .collect()
}

fn style_overrides(config: &DocsConfig) -> Map<String, Value> {
    let mut style = Map::new();
    if config.theme.tune.get("fontId").map(String::as_str) == Some("geist") {
        style.extend(table(&THEME_TUNE_STYLE_OVERRIDES_GEIST));
    }
    for (key, value) in &config.theme.style {
        style.insert(namespace_style_key(key), Value::String(value.clone()));
    }
    style
}

/// The `theme/project-theme.ts` module for this config.
pub fn render_project_theme_module(config: &DocsConfig, warnings: &mut Vec<String>) -> String {
    let theme = &config.theme;
    let mut default_config = Map::new();
    default_config.insert("presetId".into(), Value::String(theme.preset.clone()));
    if !theme.radius.is_empty() {
        default_config.insert(
            "radiusIndex".into(),
            Value::from(theme_radius_index(&theme.radius, warnings)),
        );
    }
    if !theme.tune.is_empty() {
        default_config.insert(
            "customization".into(),
            Value::Object(string_map(theme.tune.iter())),
        );
    }
    let project_preset = has_project_preset(config);
    if project_preset {
        let mut by_preset = Map::new();
        by_preset.insert(theme.preset.clone(), Value::Object(default_options(config)));
        default_config.insert("optionsByPreset".into(), Value::Object(by_preset));
    }

    let mut lines: Vec<String> = vec![
        "import type { ThemePreset, ThemeStyle, ThemeVars } from \"./preset-types\"".into(),
        String::new(),
    ];
    if project_preset {
        let empty = indexmap::IndexMap::new();
        let light_tokens = theme.tokens.get("light").unwrap_or(&empty);
        let dark_tokens = theme.tokens.get("dark").unwrap_or(&empty);
        let side =
            |name: &str, tokens: &indexmap::IndexMap<String, String>, base: &[(&str, &str)]| {
                theme
                    .preview
                    .get(name)
                    .cloned()
                    .or_else(|| tokens.get("--primary").cloned())
                    .unwrap_or_else(|| {
                        base.iter()
                            .find(|(k, _)| *k == "--primary")
                            .map(|(_, v)| v.to_string())
                            .unwrap_or_default()
                    })
            };
        let mut preview = Map::new();
        preview.insert(
            "light".into(),
            Value::String(side("light", light_tokens, &PROJECT_THEME_BASE_LIGHT)),
        );
        preview.insert(
            "dark".into(),
            Value::String(side("dark", dark_tokens, &PROJECT_THEME_BASE_DARK)),
        );
        let radius = if theme.radius.is_empty() {
            DEFAULT_RADIUS.to_string()
        } else {
            theme.radius.clone()
        };
        let mut preset = Map::new();
        preset.insert("id".into(), Value::String(theme.preset.clone()));
        preset.insert(
            "name".into(),
            Value::String(if theme.name.is_empty() {
                config.project.name.clone()
            } else {
                theme.name.clone()
            }),
        );
        preset.insert(
            "description".into(),
            Value::String(if theme.description.is_empty() {
                format!("{} project theme", config.project.name)
            } else {
                theme.description.clone()
            }),
        );
        preset.insert(
            "scene".into(),
            Value::String(if theme.scene.is_empty() {
                format!(
                    "{} documentation uses a project-owned visual system.",
                    config.project.name
                )
            } else {
                theme.scene.clone()
            }),
        );
        preset.insert("preview".into(), Value::Object(preview.clone()));
        preset.insert(
            "defaultOptions".into(),
            Value::Object(default_options(config)),
        );
        preset.insert(
            "defaultRadiusIndex".into(),
            Value::from(theme_radius_index(&radius, warnings)),
        );
        preset.insert(
            "defaultCustomization".into(),
            Value::Object(string_map(theme.tune.iter())),
        );
        preset.insert("controls".into(), controls(config));
        lines.extend(
            [
                format!("const projectBaseStyle: ThemeStyle = {}", json::pretty(&table(&PROJECT_THEME_BASE_STYLE))),
                String::new(),
                format!("const projectBaseLight: ThemeVars = {}", json::pretty(&table(&PROJECT_THEME_BASE_LIGHT))),
                String::new(),
                format!("const projectBaseDark: ThemeVars = {}", json::pretty(&table(&PROJECT_THEME_BASE_DARK))),
                String::new(),
                format!("const projectStyleOverrides: Record<string, string> = {}", json::pretty(&style_overrides(config))),
                String::new(),
                format!("const projectLightOverrides: ThemeVars = {}", json::pretty(&string_map(light_tokens.iter()))),
                String::new(),
                format!("const projectDarkOverrides: ThemeVars = {}", json::pretty(&string_map(dark_tokens.iter()))),
                String::new(),
                "const projectVariantThemes: Record<string, Record<string, {".into(),
                "  preview?: { light: string; dark: string }".into(),
                "  style?: Record<string, string>".into(),
                "  light?: ThemeVars".into(),
                "  dark?: ThemeVars".into(),
                format!("}}>> = {}", json::pretty(&variant_themes(config))),
                String::new(),
                format!("const projectPresetConfig: Omit<ThemePreset, \"resolve\"> = {}", json::pretty(&preset)),
                String::new(),
                "const projectResolvedTheme = {".into(),
                format!("  preview: {},", json::compact(&preview)),
                format!("  radius: {},", json::string(&radius)),
                "  style: { ...projectBaseStyle, ...projectStyleOverrides },".into(),
                "  light: { ...projectBaseLight, ...projectLightOverrides },".into(),
                "  dark: { ...projectBaseDark, ...projectDarkOverrides },".into(),
                "}".into(),
                String::new(),
                "function resolveProjectTheme(options: Record<string, string>) {".into(),
                "  let preview = projectResolvedTheme.preview".into(),
                "  let style = projectResolvedTheme.style".into(),
                "  let light = projectResolvedTheme.light".into(),
                "  let dark = projectResolvedTheme.dark".into(),
                String::new(),
                "  for (const control of projectPresetConfig.controls) {".into(),
                "    const selectedValue = options[control.id] ?? projectPresetConfig.defaultOptions[control.id]".into(),
                "    const variant = projectVariantThemes[control.id]?.[selectedValue]".into(),
                "    if (!variant) continue".into(),
                "    preview = variant.preview ?? preview".into(),
                "    style = { ...style, ...(variant.style ?? {}) }".into(),
                "    light = { ...light, ...(variant.light ?? {}) }".into(),
                "    dark = { ...dark, ...(variant.dark ?? {}) }".into(),
                "  }".into(),
                String::new(),
                "  return { preview, radius: projectResolvedTheme.radius, style, light, dark }".into(),
                "}".into(),
                String::new(),
                "export const projectThemePreset: ThemePreset | null = {".into(),
                "  ...projectPresetConfig,".into(),
                "  resolve(options) {".into(),
                "    return resolveProjectTheme(options)".into(),
                "  },".into(),
                "}".into(),
                String::new(),
            ],
        );
    } else {
        lines.push("export const projectThemePreset: ThemePreset | null = null".into());
        lines.push(String::new());
    }
    lines.extend([
        "export const projectThemeDefaultConfig: {".into(),
        "  presetId?: string".into(),
        "  radiusIndex?: number".into(),
        "  optionsByPreset?: Record<string, Record<string, string>>".into(),
        "  customization?: Record<string, string>".into(),
        format!("}} = {}", json::pretty(&default_config)),
        String::new(),
    ]);
    lines.join("\n")
}

/// `theme/theme-contract.generated.ts`, byte-identical to the committed template file.
pub fn generate_typescript_contract() -> String {
    let mut lines = vec![
        "// GENERATED FILE - DO NOT EDIT".to_string(),
        "// Source: crates/folio-site/src/theme.rs".to_string(),
        String::new(),
        "export interface ThemeStyle {".to_string(),
    ];
    lines.extend(
        PROJECT_THEME_BASE_STYLE
            .iter()
            .map(|(prop, _)| format!("  \"{prop}\"?: string")),
    );
    lines.push("}".to_string());
    lines.push(String::new());
    lines.push("export type ThemeTuneKey =".to_string());
    let mut keys = THEME_TUNE_KEYS.to_vec();
    keys.sort();
    lines.extend(keys.iter().map(|key| format!("  | \"{key}\"")));
    lines.push(String::new());
    lines.push("export type ThemeVars = Record<string, string>".to_string());
    lines.push(String::new());
    let radii: Vec<String> = THEME_RADIUS_OPTIONS
        .iter()
        .map(|r| json::string(r))
        .collect();
    lines.push(format!(
        "export const themeRadiusScale = [{}] as const",
        radii.join(", ")
    ));
    lines.push(String::new());
    lines.join("\n")
}

fn exports_name(text: &str, name: &str) -> bool {
    let word = crate::re(&format!(r"\b{}\b", regex::escape(name)));
    let export = crate::re(r"\bexport\b");
    let source_alias = crate::re(r"^\s+as\b");
    let found = export.find_iter(text).any(|m| {
        let segment_end = text[m.end()..]
            .find(';')
            .map(|i| m.end() + i)
            .unwrap_or(text.len());
        let segment = &text[m.end()..segment_end];
        word.find_iter(segment)
            .any(|hit| !source_alias.is_match(&segment[hit.end()..]))
    });
    found
}

/// Every problem with a theme package; empty means valid.
pub fn validate_theme_package(path: &Path, remote: bool) -> Vec<String> {
    let shown = path.display();
    if !path.exists() {
        return vec![format!("Theme package path '{shown}' not found.")];
    }
    if !path.is_dir() {
        return vec![format!("Theme package path '{shown}' is not a directory.")];
    }
    let mut errors = Vec::new();
    let remote_only: &[&str] = if remote { &REMOTE_RESERVED_PATHS } else { &[] };
    for reserved in RESERVED_PATHS.iter().chain(remote_only) {
        let reserved = *reserved;
        if path.join(reserved.trim_end_matches('/')).exists() {
            errors.push(if reserved.ends_with('/') {
                format!("Theme package must not contain reserved path '{reserved}'. Folio generates this at build time.")
            } else {
                format!("Theme package must not contain reserved file '{reserved}'. This is a Folio internal file.")
            });
        }
    }
    let project_theme = "theme/project-theme.ts";
    if let Ok(text) = std::fs::read_to_string(path.join(project_theme)) {
        for name in ["projectThemePreset", "projectThemeDefaultConfig"] {
            if !exports_name(&text, name) {
                errors.push(format!(
                    "{project_theme} must export '{name}'. Expected: export const {name} = ..."
                ));
            }
        }
    }
    errors
}

/// `validate_theme_package`, raised as one error.
pub fn validate_and_raise(path: &Path, remote: bool) -> crate::Result<()> {
    let errors = validate_theme_package(path, remote);
    if errors.is_empty() {
        return Ok(());
    }
    let list: String = errors.iter().map(|e| format!("\n  - {e}")).collect();
    Err(SiteError::Value(format!(
        "Theme package validation failed:{list}"
    )))
}

#[cfg(test)]
#[path = "theme_tests.rs"]
mod tests;
