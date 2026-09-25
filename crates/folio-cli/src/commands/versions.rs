//! `folio build-versions` (hidden, behind `FOLIO_EXPERIMENTAL=versions`): one
//! build per configured version, historical refs through `git worktree`, the
//! `.folio-version.json` reuse manifest and the root redirect.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use folio_config::{
    canonicalize_lenient, disabled_feature_message, is_feature_enabled, resolve_output_dir,
    DocsConfig,
};
use folio_plugins::PluginHost;
use folio_site::fs::sha256_hex;
use serde_json::{json, Value};

use crate::cli::BuildVersionsArgs;
use crate::error::CliError;
use crate::pipeline::{load_config, plugin_host, run_build, tracer_from_env, BuildOptions};
use crate::ui::text::{BOLD, DIM, GREEN, RED, YELLOW};
use crate::ui::Ui;
use crate::PluginFactory;

const VERSION_MANIFEST: &str = ".folio-version.json";

/// `Version output path` containment inside `output_base`.
pub fn resolve_version_output_dir(
    output_base: &Path,
    version_path: &str,
) -> Result<PathBuf, String> {
    let raw = version_path.trim();
    if raw.is_empty() {
        return Err("Version output path must be a non-empty relative path".to_string());
    }
    if Path::new(raw).is_absolute() {
        return Err("Version output path must be relative to the output directory".to_string());
    }
    let root = canonicalize_lenient(output_base);
    let resolved = canonicalize_lenient(&root.join(raw));
    if resolved == root || !resolved.starts_with(&root) {
        return Err("Version output path must stay within the output directory".to_string());
    }
    Ok(resolved)
}

fn html_escape(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#x27;")
}

/// `output_base/index.html`: a static redirect to the default version.
pub fn write_default_version_redirect(
    output_base: &Path,
    version_path: &str,
) -> std::io::Result<()> {
    let target = version_path.trim_matches('/');
    let href = html_escape(&format!(
        "{}/",
        if target.is_empty() { "latest" } else { target }
    ));
    fs::create_dir_all(output_base)?;
    fs::write(
        output_base.join("index.html"),
        format!(
            "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta http-equiv=\"refresh\" content=\"0; url={href}\">\n  <link rel=\"canonical\" href=\"{href}\">\n  <title>Redirecting...</title>\n</head>\n<body>\n  <p>Redirecting to <a href=\"{href}\">{href}</a>.</p>\n  <script>window.location.replace(\"{href}\");</script>\n</body>\n</html>\n"
        ),
    )
}

/// JSON with every object's keys sorted, recursively (Python `sort_keys=True`).
fn canonical(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let sorted: BTreeMap<&String, Value> =
                map.iter().map(|(k, v)| (k, canonical(v))).collect();
            serde_json::to_value(sorted).unwrap_or(Value::Null)
        }
        Value::Array(items) => Value::Array(items.iter().map(canonical).collect()),
        other => other.clone(),
    }
}

/// SHA-256 of the compact, sorted-key JSON of `value`.
pub fn stable_hash(value: &Value) -> String {
    let payload = serde_json::to_string(&canonical(value)).unwrap_or_default();
    sha256_hex(payload.as_bytes())
}

fn as_text(value: Option<&Value>) -> String {
    match value {
        None | Some(Value::Null) => String::new(),
        Some(Value::String(s)) => s.clone(),
        Some(other) => other.to_string(),
    }
}

fn version_build_manifest(
    version: &Value,
    commit: &str,
    versions: &[Value],
    synced: &Value,
) -> Value {
    let label = match version.get("label") {
        Some(label) => as_text(Some(label)),
        None => as_text(version.get("path")),
    };
    canonical(&json!({
        "schema": 1,
        "label": label,
        "path": as_text(version.get("path")),
        "ref": as_text(version.get("ref")),
        "commit": commit,
        "versions_hash": stable_hash(&Value::Array(versions.to_vec())),
        "synced_config_hash": stable_hash(synced),
        "folio_version": env!("CARGO_PKG_VERSION"),
    }))
}

fn manifest_matches(output_path: &Path, expected: &Value) -> bool {
    let has_content = fs::read_dir(output_path)
        .map(|entries| entries.flatten().any(|e| e.file_name() != VERSION_MANIFEST))
        .unwrap_or(false);
    let existing = fs::read_to_string(output_path.join(VERSION_MANIFEST))
        .ok()
        .and_then(|text| serde_json::from_str::<Value>(&text).ok());
    has_content && existing.as_ref() == Some(expected)
}

fn write_version_build_manifest(output_path: &Path, manifest: &Value) -> std::io::Result<()> {
    fs::create_dir_all(output_path)?;
    fs::write(
        output_path.join(VERSION_MANIFEST),
        format!(
            "{}\n",
            serde_json::to_string_pretty(manifest).unwrap_or_default()
        ),
    )
}

/// `versions:` replaced and every synced section overwritten in a
/// historical `docs.yaml`; other keys keep their order.
pub fn sync_version_matrix(
    config_path: &Path,
    versions: &[Value],
    synced: &serde_json::Map<String, Value>,
) -> Result<(), String> {
    let text = fs::read_to_string(config_path).map_err(|e| e.to_string())?;
    let document: serde_yaml_ng::Value =
        serde_yaml_ng::from_str(&text).map_err(|e| e.to_string())?;
    let mut mapping = match document {
        serde_yaml_ng::Value::Mapping(mapping) => mapping,
        _ => serde_yaml_ng::Mapping::new(),
    };
    let to_yaml = |value: &Value| serde_yaml_ng::to_value(value).map_err(|e| e.to_string());
    mapping.insert(
        serde_yaml_ng::Value::String("versions".into()),
        to_yaml(&Value::Array(versions.to_vec()))?,
    );
    for (key, value) in synced {
        mapping.insert(serde_yaml_ng::Value::String(key.clone()), to_yaml(value)?);
    }
    let dumped = serde_yaml_ng::to_string(&serde_yaml_ng::Value::Mapping(mapping))
        .map_err(|e| e.to_string())?;
    fs::write(config_path, dumped).map_err(|e| e.to_string())
}

fn git(project_dir: &Path, args: &[&str], inherit: bool) -> Result<String, String> {
    let mut command = Command::new("git");
    command
        .args(args)
        .current_dir(project_dir)
        .stdin(Stdio::null());
    if inherit {
        let status = command.status().map_err(|e| e.to_string())?;
        return if status.success() {
            Ok(String::new())
        } else {
            Err(format!("exit status {}", status.code().unwrap_or(-1)))
        };
    }
    let output = command.output().map_err(|e| e.to_string())?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        Err(if stderr.is_empty() {
            format!("exit status {}", output.status.code().unwrap_or(-1))
        } else {
            stderr
        })
    }
}

fn remove_version_worktree(project_dir: &Path, worktree_dir: &Path) {
    let _ = git(
        project_dir,
        &[
            "worktree",
            "remove",
            &worktree_dir.to_string_lossy(),
            "--force",
        ],
        false,
    );
    let _ = git(project_dir, &["worktree", "prune"], false);
}

fn synced_config(
    raw: &serde_json::Map<String, Value>,
    host: &PluginHost,
) -> serde_json::Map<String, Value> {
    host.config_keys()
        .into_iter()
        .filter_map(|key| raw.get(&key).map(|value| (key, value.clone())))
        .collect()
}

/// `folio build-versions`.
pub fn run(ui: &Ui, args: BuildVersionsArgs, plugins: &[PluginFactory]) -> Result<(), CliError> {
    let target = args.project.resolve()?;
    build_configured_versions(ui, &target, args.verbose, &args.config, args.clean, plugins)
}

/// Build every configured version into the output dir (`build-versions` and
/// `serve --versions`); the `versions` gate runs first.
pub fn build_configured_versions(
    ui: &Ui,
    target: &Path,
    verbose: bool,
    config_file: &str,
    clean: bool,
    plugins: &[PluginFactory],
) -> Result<(), CliError> {
    if !is_feature_enabled("versions") {
        ui.print_styled(YELLOW, &disabled_feature_message("versions"));
        return Err(CliError::Exit(1));
    }
    let target = target.to_path_buf();
    let host = plugin_host(plugins);
    let loaded =
        load_config(&target.join(config_file), &target, &host).map_err(CliError::message)?;
    let mut warnings = loaded.warnings;
    let mut cfg: DocsConfig = loaded.config;
    host.configure(&mut cfg, &loaded.raw, &mut warnings)
        .map_err(|e| CliError::Build(e.to_string()))?;
    let synced = synced_config(&loaded.raw, &host);
    let synced_value = Value::Object(synced.clone());
    if cfg.versions.is_empty() {
        ui.print_styled(
            YELLOW,
            "No versions configured in docs.yaml. Use 'folio build' instead.",
        );
        ui.print_styled(
            DIM,
            "Add a 'versions' section to docs.yaml to use multi-version builds.",
        );
        return Err(CliError::Exit(1));
    }
    let output_base = resolve_output_dir(&target, &cfg.output_dir, &cfg.source_roots())
        .map_err(|e| CliError::Build(e.to_string()))?;
    if clean && output_base.exists() {
        fs::remove_dir_all(&output_base)?;
    }
    fs::create_dir_all(&output_base)?;

    let tracer = tracer_from_env(ui);
    let mut failures: Vec<String> = Vec::new();
    for (i, version) in cfg.versions.iter().enumerate() {
        let label = version
            .get("label")
            .map(|v| as_text(Some(v)))
            .unwrap_or_else(|| format!("v{i}"));
        let vpath = version
            .get("path")
            .map(|v| as_text(Some(v)))
            .unwrap_or_else(|| format!("v{i}"));
        let reference = as_text(version.get("ref"));
        let output_path =
            resolve_version_output_dir(&output_base, &vpath).map_err(CliError::Build)?;
        let shown = output_path.display();
        let checkout_failed = |ui: &Ui, failures: &mut Vec<String>, error: &str| {
            failures.push(format!(
                "{label}: failed to checkout ref '{reference}' for output '{shown}'"
            ));
            ui.print_styled(
                RED,
                &format!("  Failed to checkout ref '{reference}' for {label} → {shown}: {error}"),
            );
            ui.print(&format!("  Version output: {shown}"));
        };
        let mut manifest = version_build_manifest(version, "", &cfg.versions, &synced_value);
        if !reference.is_empty() {
            let commit = match git(
                &target,
                &["rev-parse", &format!("{reference}^{{commit}}")],
                false,
            ) {
                Ok(commit) => commit,
                Err(error) => {
                    checkout_failed(ui, &mut failures, &error);
                    continue;
                }
            };
            manifest = version_build_manifest(version, &commit, &cfg.versions, &synced_value);
            if !clean && manifest_matches(&output_path, &manifest) {
                ui.blank();
                ui.print(&format!(
                    "  {} → {shown}",
                    ui.styled(DIM, &format!("Reusing version: {label}"))
                ));
                continue;
            }
        }
        ui.blank();
        ui.print(&format!(
            "  {} → {shown}",
            ui.styled(BOLD, &format!("Building version: {label}"))
        ));

        let mut worktree_dir = None;
        let source_dir = if reference.is_empty() {
            target.clone()
        } else {
            let dir = resolve_version_output_dir(&target.join(".build").join("worktrees"), &vpath)
                .map_err(CliError::Build)?;
            remove_version_worktree(&target, &dir);
            let added = git(
                &target,
                &["worktree", "add", &dir.to_string_lossy(), &reference],
                verbose,
            )
            .and_then(|_| sync_version_matrix(&dir.join(config_file), &cfg.versions, &synced));
            if let Err(error) = added {
                checkout_failed(ui, &mut failures, &error);
                remove_version_worktree(&target, &dir);
                continue;
            }
            worktree_dir = Some(dir.clone());
            dir
        };
        let opts = BuildOptions {
            verbose,
            clean,
            previews: true,
            output_override: Some(output_path.clone()),
            current_version_path: vpath.clone(),
            include_versions: true,
            source_ref_override: reference.clone(),
            plugins: plugins.to_vec(),
            ..BuildOptions::new(config_file)
        };
        let built = run_build(&source_dir, &opts, ui, tracer.clone())
            .map_err(|e| e.to_string())
            .and_then(|()| {
                write_version_build_manifest(&output_path, &manifest).map_err(|e| e.to_string())
            });
        if let Some(dir) = &worktree_dir {
            remove_version_worktree(&target, dir);
        }
        if let Err(error) = built {
            failures.push(format!(
                "{label}: build failed for output '{shown}': {error}"
            ));
            ui.print_styled(
                RED,
                &format!("  Build failed for {label} → {shown}: {error}"),
            );
            ui.print(&format!("  Version output: {shown}"));
        }
    }

    if !failures.is_empty() {
        ui.blank();
        ui.eprint_styled(RED, "  Version build failed:");
        for failure in &failures {
            ui.eprint_styled(RED, &format!("  - {failure}"));
        }
        return Err(CliError::Exit(1));
    }
    let default_path = cfg.versions[0]
        .get("path")
        .map(|v| as_text(Some(v)))
        .unwrap_or_else(|| "latest".to_string());
    write_default_version_redirect(&output_base, &default_path)?;
    ui.blank();
    ui.print_styled(
        GREEN,
        &format!("  All versions built to {}/", cfg.output_dir),
    );
    ui.blank();
    Ok(())
}

#[cfg(test)]
#[path = "versions_tests.rs"]
mod tests;
