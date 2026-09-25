//! Shared helpers for the folio-site integration tests.
#![allow(dead_code)]

use std::path::Path;

use folio_config::DocsConfig;

/// A `DocsConfig` parsed from YAML against `project_dir` (`project.name`
/// defaults to `TestProject`, `output` to `output`), paths resolved.
pub fn config(project_dir: &Path, yaml: &str) -> DocsConfig {
    let mut text = yaml.to_string();
    if !text.contains("project:") {
        text.push_str("\nproject:\n  name: TestProject\n");
    }
    if !text.contains("output:") {
        text.push_str("\noutput: output\n");
    }
    let mapping: serde_yaml_ng::Mapping = serde_yaml_ng::from_str(&text).expect("test yaml");
    let mut warnings = Vec::new();
    let mut parsed = folio_config::parse_docs_config_with(&mapping, project_dir, "", &mut warnings)
        .expect("test config parses");
    let raw = match serde_json::to_value(&mapping).expect("yaml is json") {
        serde_json::Value::Object(map) => map,
        _ => unreachable!("mapping"),
    };
    folio_plugins::Plugin::configure(
        &folio_plugins::LandingPlugin,
        &mut parsed,
        &raw,
        &mut warnings,
    )
    .expect("landing configures");
    parsed
        .resolve_paths(project_dir)
        .expect("test config resolves")
}

/// Write `text` at `dir/rel`, creating parents.
pub fn write(dir: &Path, rel: &str, text: &str) -> std::path::PathBuf {
    let path = dir.join(rel);
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    std::fs::write(&path, text).unwrap();
    path
}

pub fn read(path: &Path) -> String {
    std::fs::read_to_string(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()))
}

/// The JSON literal that follows `marker` in generated TypeScript.
pub fn extract_ts_object(source: &str, marker: &str) -> serde_json::Value {
    let start = source
        .find(marker)
        .unwrap_or_else(|| panic!("marker {marker:?} missing in:\n{source}"))
        + marker.len();
    let bytes = source.as_bytes();
    let mut idx = start;
    while bytes[idx] != b'{' && bytes[idx] != b'[' {
        idx += 1;
    }
    let open = bytes[idx];
    let close = if open == b'{' { b'}' } else { b']' };
    let (mut depth, mut in_string, mut escaped) = (0, false, false);
    let mut end = idx;
    for (pos, &ch) in bytes.iter().enumerate().skip(idx) {
        if in_string {
            if escaped {
                escaped = false;
            } else if ch == b'\\' {
                escaped = true;
            } else if ch == b'"' {
                in_string = false;
            }
            continue;
        }
        if ch == b'"' {
            in_string = true;
        } else if ch == open {
            depth += 1;
        } else if ch == close {
            depth -= 1;
            if depth == 0 {
                end = pos + 1;
                break;
            }
        }
    }
    serde_json::from_str(&source[idx..end]).expect("ts literal is json")
}

/// A minimal template with the markers the injector consumes.
pub fn make_template(root: &Path) -> std::path::PathBuf {
    let template = root.join("template");
    write(&template, "package.json", "{\"name\": \"test\"}");
    write(
        &template,
        "app/layout.tsx",
        "export const metadata = {\n  title: {\n    default: \"__PROJECT_NAME__\",\n    template: \"%s - __PROJECT_NAME__\",\n  },\n  description: \"__PROJECT_DESCRIPTION__\",\n}\n",
    );
    write(
        &template,
        "app/docs/layout.tsx",
        "import { getPageMap } from \"nextra/page-map\"\n<span>__PROJECT_MONOGRAM__</span>\n<span>__PROJECT_NAME__</span>\n{/* __PROJECT_REPO_LINK_START__ */}\n<a href=\"__PROJECT_REPO__\" aria-label=\"GitHub repository\">GitHub</a>\n{/* __PROJECT_REPO_LINK_END__ */}\npageMap={await getPageMap(\"/docs\")}\nfooter={<Footer />}\n",
    );
    write(&template, "app/page.tsx", "Built with __PROJECT_NAME__\n");
    write(
        &template,
        "app/previews/layout.tsx",
        "import { getPageMap } from \"nextra/page-map\"\n<span>__PROJECT_MONOGRAM__</span>\n<span>__PROJECT_NAME__</span>\n{/* __PROJECT_REPO_LINK_START__ */}\n<a href=\"__PROJECT_REPO__\" aria-label=\"GitHub repository\">GitHub</a>\n{/* __PROJECT_REPO_LINK_END__ */}\npageMap={await getPageMap(\"/docs\")}\n",
    );
    write(
        &template,
        "components/landing-navbar.tsx",
        "<span>__PROJECT_MONOGRAM__</span>\n<span>__PROJECT_NAME__</span>\n",
    );
    write(
        &template,
        "next.config.mjs",
        "const configuredBasePath = '' // __FOLIO_BASE_PATH__\nconst nextConfig = {\n  images: { unoptimized: true },\n  __I18N_CONFIG__\n}\n",
    );
    template
}

/// The bundled template checked out in the repository.
pub fn bundled_template() -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../template")
        .canonicalize()
        .unwrap()
}

/// Workspace copy plus injection, what `SiteBuilder::prepare` runs.
pub fn prepare(
    config: &DocsConfig,
    template: &Path,
    build: &Path,
) -> folio_site::inject::Injection {
    folio_site::template::TemplateWorkspace::new(template, build, None)
        .prepare(false)
        .unwrap();
    folio_site::inject::TemplateConfigInjector::new(config, build, template)
        .inject()
        .unwrap()
}

/// `prepare` on a fresh `build-<label>` dir under `root`; returns the build dir.
pub fn prepared(
    root: &Path,
    config: &DocsConfig,
    template: &Path,
    label: &str,
) -> std::path::PathBuf {
    let build = root.join(format!("build-{label}"));
    prepare(config, template, &build);
    build
}

/// A nested preview build sets `FOLIO_BASE_PATH` while it runs, and a builder
/// reads it when it is made. A test that runs nested builds holds this lock
/// around them, and `builder` takes it, so no builder is made mid-build.
pub fn env_lock() -> std::sync::MutexGuard<'static, ()> {
    static LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());
    LOCK.lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner)
}

/// A `SiteBuilder` over the no-op runtime.
pub fn builder<'a>(
    config: &'a DocsConfig,
    template: &Path,
    build: &Path,
) -> folio_site::builder::SiteBuilder<'a> {
    let _env = env_lock();
    folio_site::builder::SiteBuilder::new(
        config,
        template,
        build,
        Box::new(folio_site::runtime::NoopRuntime),
    )
}

pub fn mtime_ns(path: &Path) -> u128 {
    std::fs::metadata(path)
        .unwrap()
        .modified()
        .unwrap()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos()
}

/// Set a stable mtime so a later write is detectable.
pub fn pin_mtime(path: &Path) -> u128 {
    let stable = std::fs::FileTimes::new()
        .set_modified(std::time::UNIX_EPOCH + std::time::Duration::from_secs(1_700_000_000));
    std::fs::File::options()
        .write(true)
        .open(path)
        .unwrap()
        .set_times(stable)
        .unwrap();
    mtime_ns(path)
}
