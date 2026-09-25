//! The bundled template embedded in the binary, template resolution and
//! validation (`template.path`, `template.overlay_path`), overlay staging,
//! the drift gate, the manifest build context, the warm-build prune and
//! `TemplateWorkspace`.

use std::path::{Path, PathBuf};

use folio_config::{canonicalize_lenient, experimental_feature_state, DocsConfig};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::fs::{
    collect_copyable_files, copy_tree, hash_file, hash_tree, reject_symlinks,
    remove_dir_all_if_exists, sha256_hex, COPY_IGNORED_DIRS, FOLIO_STAGING_MARKER,
    INJECTED_ROOT_FILES,
};
use crate::{Result, SiteError};
use folio_plugins::drift::check_template_drift;
use folio_plugins::{required_component_names, validate_template_mdx_contract, BUILTIN_COMPONENTS};

include!(concat!(env!("OUT_DIR"), "/template_files.rs"));

/// Environment variable naming a template checkout to use instead of the
/// embedded copy (template development).
pub const TEMPLATE_DIR_ENV: &str = "FOLIO_TEMPLATE_DIR";

/// Files a `template.path` or merged overlay must contain, in report order.
pub const REQUIRED_TEMPLATE_FILES: [&str; 7] = [
    "package.json",
    "pnpm-lock.yaml",
    "next.config.mjs",
    "mdx-components.tsx",
    "app",
    "app/docs/layout.tsx",
    "app/docs/[[...mdxPath]]/page.jsx",
];

/// Markers that must appear verbatim in their template file.
pub const REQUIRED_INJECTION_MARKERS: [(&str, &[&str]); 4] = [
    (
        "app/layout.tsx",
        &[
            "__PROJECT_NAME__",
            "__PROJECT_DESCRIPTION__",
            "__SITE_URL__",
        ],
    ),
    ("app/docs/layout.tsx", &["__PROJECT_NAME__"]),
    (
        "app/docs/[[...mdxPath]]/page.jsx",
        &[
            "__PROJECT_NAME__",
            "__PROJECT_DESCRIPTION__",
            "__SITE_URL__",
            "__DOCS_INDEX_CANONICAL_PATH__",
        ],
    ),
    (
        "next.config.mjs",
        &["const configuredBasePath = '' // __FOLIO_BASE_PATH__"],
    ),
];

/// Entries directly under `.build/` a scoped prune keeps.
pub const SCOPED_CLEAN_PRESERVE: [&str; 3] = ["node_modules", ".next", "content"];

fn io(path: &Path) -> impl Fn(std::io::Error) -> SiteError + '_ {
    move |e| SiteError::io(path, e)
}

/// Marker file a materialised bundled template carries: its `TEMPLATE_HASH`.
pub const BUNDLED_MARKER: &str = ".folio-bundled";

/// Write the embedded template into `dest` once: a missing `dest` is built in
/// a sibling `<dest>.tmp-<pid>` and renamed into place; an existing one is
/// immutable per content and never touched.
pub fn materialise_template(dest: &Path) -> std::io::Result<()> {
    if dest.exists() {
        return Ok(());
    }
    let parent = dest.parent().unwrap_or(Path::new("."));
    std::fs::create_dir_all(parent)?;
    let name = dest
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    let tmp = parent.join(format!("{name}.tmp-{}", std::process::id()));
    remove_dir_all_if_exists(&tmp)?;
    for (rel, bytes) in TEMPLATE_FILES {
        let path = tmp.join(rel);
        std::fs::create_dir_all(path.parent().unwrap_or(&tmp))?;
        std::fs::write(&path, bytes)?;
    }
    std::fs::write(tmp.join(BUNDLED_MARKER), TEMPLATE_HASH)?;
    match std::fs::rename(&tmp, dest) {
        Ok(()) => Ok(()),
        Err(_) if dest.exists() => remove_dir_all_if_exists(&tmp),
        Err(e) => {
            let _ = remove_dir_all_if_exists(&tmp);
            Err(e)
        }
    }
}

/// The user cache directory Folio writes under: `XDG_CACHE_HOME`, the Windows
/// equivalent, else `~/.cache`.
pub fn user_cache_dir() -> Result<PathBuf> {
    let base = std::env::var_os("XDG_CACHE_HOME")
        .filter(|v| !v.is_empty())
        .map(PathBuf::from)
        .or_else(|| {
            std::env::var_os("LOCALAPPDATA")
                .filter(|v| !v.is_empty())
                .map(PathBuf::from)
        })
        .or_else(|| {
            std::env::var_os("HOME")
                .filter(|v| !v.is_empty())
                .map(|h| PathBuf::from(h).join(".cache"))
        })
        .ok_or_else(|| {
            SiteError::Value(
                "set XDG_CACHE_HOME or HOME (or FOLIO_TEMPLATE_DIR) so the bundled template can be materialised".to_string(),
            )
        })?;
    Ok(base.join("folio"))
}

/// Where the embedded template is materialised: the user cache dir, keyed by
/// the Folio version and the template content hash.
pub fn bundled_template_cache_dir() -> Result<PathBuf> {
    Ok(user_cache_dir()?.join("template").join(format!(
        "{}-{}",
        env!("CARGO_PKG_VERSION"),
        &TEMPLATE_HASH[..12]
    )))
}

/// The bundled template directory: `FOLIO_TEMPLATE_DIR` when set, else the
/// embedded copy materialised into the cache dir.
pub fn find_bundled_template_dir() -> Result<PathBuf> {
    find_bundled_template_dir_with(
        std::env::var(TEMPLATE_DIR_ENV)
            .ok()
            .filter(|v| !v.trim().is_empty())
            .as_deref(),
    )
}

/// `find_bundled_template_dir` with an explicit override value.
pub fn find_bundled_template_dir_with(override_dir: Option<&str>) -> Result<PathBuf> {
    if let Some(dir) = override_dir {
        let path = PathBuf::from(dir);
        if !path.is_dir() {
            return Err(SiteError::NotFound(format!(
                "{TEMPLATE_DIR_ENV} does not exist: {}",
                path.display()
            )));
        }
        return Ok(path);
    }
    let dest = bundled_template_cache_dir()?;
    materialise_template(&dest).map_err(io(&dest))?;
    Ok(dest)
}

/// Whether `dir` is a materialised copy of this binary's embedded template.
pub fn is_materialised_bundle(dir: &Path) -> bool {
    std::fs::read_to_string(dir.join(BUNDLED_MARKER))
        .map(|hash| hash == TEMPLATE_HASH)
        .unwrap_or(false)
}

/// The workspace copy of the embedded template: every `TEMPLATE_FILES` entry
/// outside the ignored directories, minus the root `next.config.mjs`.
fn copy_embedded(build_dir: &Path) -> std::io::Result<()> {
    for (rel, bytes) in TEMPLATE_FILES {
        let parts: Vec<&str> = rel.split('/').collect();
        let ignored = parts
            .iter()
            .any(|p| COPY_IGNORED_DIRS.contains(p) || *p == FOLIO_STAGING_MARKER);
        if ignored || (parts.len() == 1 && INJECTED_ROOT_FILES.contains(&parts[0])) {
            continue;
        }
        let path = build_dir.join(rel);
        std::fs::create_dir_all(path.parent().unwrap_or(build_dir))?;
        std::fs::write(&path, bytes)?;
    }
    Ok(())
}

/// `(file, marker)` pairs whose load-bearing marker is missing; a missing
/// file reports every marker it owns.
pub fn validate_template_marker_contract(template_dir: &Path) -> Vec<(String, String)> {
    let mut missing = Vec::new();
    for (rel, markers) in REQUIRED_INJECTION_MARKERS {
        match std::fs::read_to_string(template_dir.join(rel)) {
            Ok(text) => missing.extend(
                markers
                    .iter()
                    .filter(|m| !text.contains(**m))
                    .map(|m| (rel.to_string(), m.to_string())),
            ),
            Err(_) => missing.extend(markers.iter().map(|m| (rel.to_string(), m.to_string()))),
        }
    }
    missing
}

/// Required files, then required MDX components, then injection markers.
pub fn validate_template_contract(template_dir: &Path, label: &str) -> Result<()> {
    let missing: Vec<&str> = REQUIRED_TEMPLATE_FILES
        .iter()
        .copied()
        .filter(|name| !template_dir.join(name).exists())
        .collect();
    if !missing.is_empty() {
        return Err(SiteError::Value(format!(
            "{label} is missing required Next/Nextra files: {}",
            missing.join(", ")
        )));
    }
    let components = validate_template_mdx_contract(
        template_dir,
        &required_component_names(&BUILTIN_COMPONENTS),
    );
    if !components.is_empty() {
        return Err(SiteError::Value(format!(
            "{label} mdx-components.tsx is missing Folio MDX contract components: {}",
            components.join(", ")
        )));
    }
    let markers = validate_template_marker_contract(template_dir);
    if !markers.is_empty() {
        let details: Vec<String> = markers
            .iter()
            .map(|(file, marker)| format!("{marker} in {file}"))
            .collect();
        return Err(SiteError::Value(format!(
            "{label} is missing required Folio injection markers: {}",
            details.join(", ")
        )));
    }
    Ok(())
}

/// Fail when the bundled `mdx-components.tsx` and the builtin manifest disagree.
pub fn check_bundled_template_drift(template_dir: &Path) -> Result<()> {
    let path = template_dir.join("mdx-components.tsx");
    let text = std::fs::read_to_string(&path).map_err(io(&path))?;
    let drift = check_template_drift(&text);
    if drift.is_empty() {
        return Ok(());
    }
    let lines: Vec<String> = drift.iter().map(|m| format!("  - {m}")).collect();
    Err(SiteError::Value(format!(
        "Bundled template drifted from the builtin component manifest:\n{}",
        lines.join("\n")
    )))
}

/// Bundled template plus the overlay's files on top, in `staging`.
pub fn materialize_overlay_template(
    bundled: &Path,
    overlay: &Path,
    staging: &Path,
) -> Result<PathBuf> {
    let resolved_overlay = canonicalize_lenient(overlay);
    let resolved_staging = canonicalize_lenient(staging);
    if resolved_overlay.starts_with(&resolved_staging) {
        return Err(SiteError::Value(format!(
            "template.overlay_path cannot point inside the template staging directory ({}/): it is recreated on every build",
            staging.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default()
        )));
    }
    reject_symlinks(overlay, "template.overlay_path")?;
    if staging.exists() {
        if !staging.join(FOLIO_STAGING_MARKER).exists() {
            return Err(SiteError::Value(format!(
                "Refusing to delete existing directory {}: it was not created by Folio (missing {FOLIO_STAGING_MARKER} marker). Remove or rename it manually and rerun the build.",
                staging.display()
            )));
        }
        remove_dir_all_if_exists(staging).map_err(io(staging))?;
    }
    std::fs::create_dir_all(staging).map_err(io(staging))?;
    let marker = staging.join(FOLIO_STAGING_MARKER);
    std::fs::write(
        &marker,
        "Folio overlay staging directory; safe to delete.\n",
    )
    .map_err(io(&marker))?;
    copy_tree(bundled, staging, &[]).map_err(io(staging))?;
    copy_tree(overlay, staging, &[]).map_err(io(staging))?;
    Ok(staging.to_path_buf())
}

/// Which template a build uses.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TemplateKind {
    /// The embedded template.
    Bundled,
    /// Bundled plus `template.overlay_path`, merged into the staging dir.
    Overlay,
    /// `template.path`.
    Custom,
}

/// The template directory a build copies from.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedTemplate {
    /// The directory the workspace copies from.
    pub dir: PathBuf,
    /// Which template it is.
    pub kind: TemplateKind,
}

fn contained_dir(raw: &str, config: &DocsConfig, label: &str) -> Result<PathBuf> {
    let resolved = folio_config::resolve_contained_dir(
        Path::new(raw),
        &config.project_dir,
        Path::new(&config.output_dir),
        label,
        false,
    )
    .map_err(|e| SiteError::Value(e.to_string()))?;
    if !resolved.is_dir() {
        return Err(SiteError::NotFound(format!(
            "{label} does not exist: {}",
            resolved.display()
        )));
    }
    Ok(resolved)
}

/// The staging dir for an overlay build: a sibling of `build_dir` named
/// `<build_dir name>-template`.
pub fn overlay_staging_dir(build_dir: &Path) -> PathBuf {
    let name = build_dir
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| ".build".to_string());
    build_dir
        .parent()
        .unwrap_or(Path::new("."))
        .join(format!("{name}-template"))
}

/// Resolve and validate the template directory for `config`.
pub fn resolve_template_dir(config: &DocsConfig, build_dir: &Path) -> Result<ResolvedTemplate> {
    if !config.template.overlay_path.is_empty() {
        let overlay = contained_dir(
            &config.template.overlay_path,
            config,
            "template.overlay_path",
        )?;
        let bundled = find_bundled_template_dir()?;
        check_bundled_template_drift(&bundled)?;
        let merged =
            materialize_overlay_template(&bundled, &overlay, &overlay_staging_dir(build_dir))?;
        validate_template_contract(&merged, "template.overlay_path")?;
        return Ok(ResolvedTemplate {
            dir: merged,
            kind: TemplateKind::Overlay,
        });
    }
    if config.template.path.is_empty() {
        let bundled = find_bundled_template_dir()?;
        check_bundled_template_drift(&bundled)?;
        return Ok(ResolvedTemplate {
            dir: bundled,
            kind: TemplateKind::Bundled,
        });
    }
    let resolved = contained_dir(&config.template.path, config, "template.path")?;
    validate_template_contract(&resolved, "template.path")?;
    Ok(ResolvedTemplate {
        dir: resolved,
        kind: TemplateKind::Custom,
    })
}

/// `config.template.docs_route_base` without a trailing `/`, `/docs` when empty.
pub fn docs_route_base(config: &DocsConfig) -> String {
    match config.template.docs_route_base.trim_end_matches('/') {
        "" => "/docs".to_string(),
        base => base.to_string(),
    }
}

/// The relative path as the bytes the digest hashes: the real bytes on Unix,
/// where a filename need not be UTF-8, and POSIX separators everywhere.
#[cfg(unix)]
fn digest_path_bytes(rel: &Path) -> Vec<u8> {
    use std::os::unix::ffi::OsStrExt;
    rel.as_os_str().as_bytes().to_vec()
}

#[cfg(not(unix))]
fn digest_path_bytes(rel: &Path) -> Vec<u8> {
    crate::fs::posix(rel).into_bytes()
}

/// SHA-256 over the copyable files of a theme package: every relative path and
/// every file's bytes, in the collector's sorted order, each field preceded by
/// its length. The lengths are what make the digest identify one tree and only
/// one: a separator byte would not, because a file's contents may contain any
/// byte, so a crafted blob could otherwise imitate the rest of the stream and
/// two different trees would pin the same. This is the digest a remote package
/// is pinned by, so it must not depend on where the directory sits, on the
/// machine, or on anything git records.
pub fn package_tree_digest(root: &Path) -> Result<String> {
    let files = collect_copyable_files(root, "theme.package")?;
    let mut digest = Sha256::new();
    digest.update(b"folio-theme-package-v1\0");
    digest.update((files.len() as u64).to_be_bytes());
    for rel in files {
        let name = digest_path_bytes(&rel);
        digest.update((name.len() as u64).to_be_bytes());
        digest.update(&name);
        let path = root.join(&rel);
        let bytes = std::fs::read(&path).map_err(io(&path))?;
        digest.update((bytes.len() as u64).to_be_bytes());
        digest.update(&bytes);
    }
    Ok(digest
        .finalize()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect())
}

/// The theme package's contribution to the build context. A local package is
/// hashed from disk; a remote one is already pinned, so its digest is the
/// signature and no directory has to exist yet.
pub fn theme_package_signature(config: &DocsConfig) -> Result<String> {
    if let Some(remote) = &config.theme.package_remote {
        return Ok(remote.digest.clone());
    }
    let package = &config.theme.package_path;
    if package.is_empty() {
        return Ok(String::new());
    }
    let root = Path::new(package);
    if !root.is_dir() {
        return Ok(String::new());
    }
    package_tree_digest(root)
}

/// SHA-256 of the running executable, falling back to the Cargo version.
pub fn generator_fingerprint() -> String {
    std::env::current_exe()
        .and_then(std::fs::read)
        .map(|bytes| sha256_hex(&bytes))
        .unwrap_or_else(|_| env!("CARGO_PKG_VERSION").to_string())
}

/// The manifest `build` context; a page regenerates when any field changed.
/// The empty default is the context of a manifest that has none: nothing matches it.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct BuildContext {
    /// SHA-256 of `docs.yaml`.
    pub config: String,
    /// Tree hash of the resolved template dir.
    pub template: String,
    /// Signature of `theme.package`; `""` when unset.
    pub theme_package: String,
    /// `template.docs_route_base`, `/docs` by default.
    pub docs_route_base: String,
    /// The running executable's fingerprint.
    pub generator: String,
    /// `project.repo_ref`, possibly overridden by the CLI.
    pub source_ref: String,
    /// `disabled` or the sorted `FOLIO_EXPERIMENTAL` names.
    pub experimental_features: String,
}

/// Assemble the build context.
pub fn build_manifest_context(
    config_path: &Path,
    template_dir: &Path,
    source_ref: &str,
    theme_package_signature: &str,
    docs_route_base: &str,
    generator: &str,
) -> BuildContext {
    BuildContext {
        config: hash_file(config_path),
        template: hash_tree(template_dir),
        theme_package: theme_package_signature.to_string(),
        docs_route_base: docs_route_base.to_string(),
        generator: generator.to_string(),
        source_ref: source_ref.to_string(),
        experimental_features: experimental_feature_state(),
    }
}

/// Remove `app/<old route base>` relocated by a previous build, plus parents
/// the relocation created that are now empty.
pub fn remove_relocated_docs_route(build_dir: &Path, route_base: &str) -> std::io::Result<()> {
    let segments: Vec<&str> = route_base
        .trim_matches('/')
        .split('/')
        .filter(|s| !s.is_empty())
        .collect();
    if segments.is_empty() || segments == ["docs"] {
        return Ok(());
    }
    let app_dir = build_dir.join("app");
    let old_dir = segments
        .iter()
        .fold(app_dir.clone(), |dir, seg| dir.join(seg));
    if !old_dir.is_dir() {
        return Ok(());
    }
    std::fs::remove_dir_all(&old_dir)?;
    let mut parent = old_dir.parent().map(Path::to_path_buf);
    while let Some(dir) = parent {
        if dir == app_dir || !dir.is_dir() || std::fs::read_dir(&dir)?.next().is_some() {
            break;
        }
        std::fs::remove_dir(&dir)?;
        parent = dir.parent().map(Path::to_path_buf);
    }
    Ok(())
}

/// A changed template, theme or executable clears the generated workspace.
/// An executable change also discards content from plugins it may no longer ship;
/// a changed route base unpublishes the old one.
pub fn prune_stale_build_overlay(
    prev: Option<&BuildContext>,
    build_dir: &Path,
    ctx: &BuildContext,
) -> std::io::Result<()> {
    if !build_dir.exists() {
        return Ok(());
    }
    let Some(prev) = prev else { return Ok(()) };
    let generator_changed = prev.generator != ctx.generator;
    if generator_changed
        || (&prev.template, &prev.theme_package) != (&ctx.template, &ctx.theme_package)
    {
        for entry in std::fs::read_dir(build_dir)? {
            let entry = entry?;
            let name = entry.file_name();
            let name = name.to_string_lossy();
            if SCOPED_CLEAN_PRESERVE.contains(&name.as_ref())
                && !(generator_changed && name == "content")
            {
                continue;
            }
            let path = entry.path();
            if entry.file_type()?.is_dir() {
                std::fs::remove_dir_all(&path)?;
            } else {
                std::fs::remove_file(&path)?;
            }
        }
        return Ok(());
    }
    if !prev.docs_route_base.is_empty() && prev.docs_route_base != ctx.docs_route_base {
        remove_relocated_docs_route(build_dir, &prev.docs_route_base)?;
    }
    Ok(())
}

/// Copies the template into `.build/` and clears its demo content.
pub struct TemplateWorkspace {
    /// The template to copy.
    pub template_dir: PathBuf,
    /// The workspace.
    pub build_dir: PathBuf,
    /// Where generated pages live (`build_dir/content`).
    pub content_dir: PathBuf,
}

impl TemplateWorkspace {
    /// `content_dir` defaults to `build_dir/content`.
    pub fn new(template_dir: &Path, build_dir: &Path, content_dir: Option<&Path>) -> Self {
        TemplateWorkspace {
            template_dir: template_dir.to_path_buf(),
            build_dir: build_dir.to_path_buf(),
            content_dir: content_dir
                .map(Path::to_path_buf)
                .unwrap_or_else(|| build_dir.join("content")),
        }
    }

    /// Copy the template over `.build/` (`--clean` wipes it first), skipping
    /// `next.config.mjs` at the root, then remove the template's demo content.
    pub fn prepare(&self, clean: bool) -> Result<()> {
        if clean && self.build_dir.exists() {
            // Everything but `node_modules`: a cache clear should not pay a
            // full pnpm install for a cache pnpm validates itself.
            for entry in std::fs::read_dir(&self.build_dir).map_err(io(&self.build_dir))? {
                let entry = entry.map_err(io(&self.build_dir))?;
                if entry.file_name() == "node_modules" {
                    continue;
                }
                let path = entry.path();
                let is_dir = entry
                    .file_type()
                    .map(|kind| kind.is_dir())
                    .map_err(io(&path))?;
                if is_dir {
                    remove_dir_all_if_exists(&path).map_err(io(&path))?;
                } else {
                    std::fs::remove_file(&path).map_err(io(&path))?;
                }
            }
        }
        reject_symlinks(&self.template_dir, "template.path")?;
        if is_materialised_bundle(&self.template_dir) {
            copy_embedded(&self.build_dir).map_err(io(&self.build_dir))?;
        } else {
            copy_tree(&self.template_dir, &self.build_dir, &INJECTED_ROOT_FILES)
                .map_err(io(&self.build_dir))?;
        }
        self.remove_template_content()?;
        std::fs::create_dir_all(&self.content_dir).map_err(io(&self.content_dir))?;
        Ok(())
    }

    fn remove_template_content(&self) -> Result<()> {
        let template_content = self.template_dir.join("content");
        if !template_content.exists() || !self.content_dir.exists() {
            return Ok(());
        }
        let mut entries = Vec::new();
        fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
            let Ok(read) = std::fs::read_dir(dir) else {
                return;
            };
            for entry in read.flatten() {
                let path = entry.path();
                if path.is_dir() && !path.is_symlink() {
                    walk(&path, out);
                }
                out.push(path);
            }
        }
        walk(&template_content, &mut entries);
        entries.sort_by_key(|p| std::cmp::Reverse(p.components().count()));
        for source in entries {
            let rel = source.strip_prefix(&template_content).unwrap_or(&source);
            let target = self.content_dir.join(rel);
            let source_is_file = source.is_symlink() || source.is_file();
            if source_is_file {
                if target.is_symlink() || target.is_file() {
                    std::fs::remove_file(&target).map_err(io(&target))?;
                }
            } else if source.is_dir() && target.is_dir() {
                let _ = std::fs::remove_dir(&target);
            }
        }
        Ok(())
    }
}

#[cfg(test)]
#[path = "template_tests.rs"]
mod tests;
