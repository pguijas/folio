//! Source orchestration over real directory trees.

use std::fs;
use std::path::{Path, PathBuf};

use folio_config::{load_docs_config, DocsConfig};
use folio_docs::{
    discover_sources, parse_doc_sources, parse_language_sources, parse_python_sources, DocsError,
};

fn write(path: &Path, content: &str) {
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, content).unwrap();
}

/// A canonical temp project (excludes compare resolved paths) with the given docs.yaml.
fn project(yaml: &str) -> (tempfile::TempDir, PathBuf, DocsConfig) {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    write(&root.join("docs.yaml"), yaml);
    let config = load_docs_config(&root.join("docs.yaml"))
        .unwrap()
        .config
        .resolve_paths(&root)
        .unwrap();
    (dir, root, config)
}

const CORE_NUMPY: &str = "\"\"\"Core module.\"\"\"\n\ndef add(a, b):\n    \"\"\"Add values.\n\n    Parameters\n    ----------\n    a : int\n        First value.\n    b : int\n        Second value.\n    Returns\n    -------\n    int\n        Sum.\n    \"\"\"\n    return a + b\n";

#[test]
fn python_sources_follow_paths_excludes_style_and_report_missing_roots() {
    let (_guard, root, config) = project(
        "project:\n  name: Demo\nsource:\n  python:\n    paths: [src/demo, missing]\n    exclude: [src/demo/internal.py]\n    docstring_style: numpy\n",
    );
    write(
        &root.join("src/demo/__init__.py"),
        "\"\"\"Demo package.\"\"\"\n",
    );
    write(&root.join("src/demo/core.py"), CORE_NUMPY);
    write(
        &root.join("src/demo/internal.py"),
        "\"\"\"Internal.\"\"\"\n",
    );

    let parsed = parse_python_sources(&config).unwrap();
    let missing = root.join("missing");
    assert_eq!(
        parsed.missing_paths,
        [missing.to_string_lossy().to_string()]
    );
    assert_eq!(parsed.scanned_paths, [root.join("src/demo")]);
    assert_eq!(
        parsed.warnings,
        [format!(
            "Python source path not found: {}",
            missing.display()
        )]
    );
    let names: Vec<&str> = parsed.modules.iter().map(|m| m.name.as_str()).collect();
    assert_eq!(names, ["demo", "demo.core"]);
    let add = &parsed.modules[1].functions[0];
    assert_eq!(add.args[0].description, "First value.");
    assert_eq!(add.returns.as_ref().unwrap().description, "Sum.");

    // `src/` is an import root: its children publish under their import names.
    let (_guard, root, config) =
        project("project:\n  name: Demo\nsource:\n  python:\n    paths: [src]\n");
    write(
        &root.join("src/acme/__init__.py"),
        "\"\"\"Acme package.\"\"\"\n",
    );
    write(&root.join("src/acme/api.py"), "def ping(): pass\n");
    write(
        &root.join("src/extensions/payments/client.py"),
        "def charge(): pass\n",
    );
    write(&root.join("src/standalone.py"), "def run(): pass\n");
    let parsed = parse_python_sources(&config).unwrap();
    let names: Vec<&str> = parsed.modules.iter().map(|m| m.name.as_str()).collect();
    assert_eq!(
        names,
        [
            "standalone",
            "acme",
            "acme.api",
            "extensions.payments.client"
        ]
    );
}

#[test]
fn javascript_sources_run_after_python_and_report_the_files_they_pass_over() {
    let (_guard, root, config) = project(
        "project:\n  name: Demo\nsource:\n  python:\n    paths: [mylib, missing-py]\n    exclude: [mylib/skip.py]\n  javascript:\n    paths: [web, missing-js]\n    exclude: [web/lib/vendor.js]\n",
    );
    write(&root.join("mylib/__init__.py"), "\"\"\"My library.\"\"\"\n");
    write(
        &root.join("mylib/core.py"),
        "\"\"\"Core.\"\"\"\n\ndef run(x: int) -> int:\n    return x\n",
    );
    write(&root.join("mylib/skip.py"), "SKIPPED = 1\n");
    write(
        &root.join("web/index.js"),
        "export function greet(name) {}\n",
    );
    write(
        &root.join("web/lib/util.js"),
        "export function pad(value, width) {}\n",
    );
    write(
        &root.join("web/lib/vendor.js"),
        "export function vendor() {}\n",
    );
    write(
        &root.join("web/widget.jsx"),
        "export default function W() {}\n",
    );
    write(
        &root.join("web/node_modules/pkg/index.js"),
        "export function dep() {}\n",
    );

    let parsed = parse_language_sources(&config).unwrap();
    let modules: Vec<(&str, &str)> = parsed
        .modules
        .iter()
        .map(|m| (m.language.id(), m.name.as_str()))
        .collect();
    assert_eq!(
        modules,
        [
            ("python", "mylib"),
            ("python", "mylib.core"),
            ("javascript", "web"),
            ("javascript", "lib.util"),
        ]
    );
    assert_eq!(parsed.scanned_paths, [root.join("mylib"), root.join("web")]);
    assert_eq!(
        parsed.missing_paths,
        [
            root.join("missing-py").to_string_lossy().to_string(),
            root.join("missing-js").to_string_lossy().to_string(),
        ]
    );
    assert_eq!(
        parsed.warnings,
        [
            format!(
                "Python source path not found: {}",
                root.join("missing-py").display()
            ),
            format!(
                "JavaScript source path not found: {}",
                root.join("missing-js").display()
            ),
            format!(
                "JSX is not read in this release; skipping {}",
                root.join("web/widget.jsx").display()
            ),
        ]
    );
    let python_only = parse_python_sources(&config).unwrap();
    assert_eq!(python_only.modules, parsed.modules[..2]);
    assert_eq!(python_only.warnings.len(), 1);
}

#[test]
fn rust_sources_follow_the_module_tree_and_run_after_python() {
    let (_guard, root, config) = project(
        "project:\n  name: Demo\nsource:\n  rust:\n    paths: [crates]\n    exclude: [crates/demo/src/internal.rs]\n  python:\n    paths: [mylib]\n",
    );
    write(&root.join("mylib/__init__.py"), "\"\"\"My library.\"\"\"\n");
    write(
        &root.join("crates/demo/Cargo.toml"),
        "[package]\nname = \"demo-crate\"\n",
    );
    write(
        &root.join("crates/demo/src/lib.rs"),
        "//! The crate.\n\npub mod models;\npub mod internal;\nmod private;\n",
    );
    write(
        &root.join("crates/demo/src/models.rs"),
        "//! Models.\n\n/// A point.\npub struct Point;\n",
    );
    write(&root.join("crates/demo/src/internal.rs"), "//! Excluded.\n");
    write(&root.join("crates/demo/src/private.rs"), "//! Private.\n");
    write(
        &root.join("crates/demo/src/orphan.rs"),
        "//! Declared by nobody.\n",
    );

    let parsed = parse_language_sources(&config).unwrap();
    let modules: Vec<(&str, &str)> = parsed
        .modules
        .iter()
        .map(|m| (m.language.id(), m.name.as_str()))
        .collect();
    assert_eq!(
        modules,
        [
            ("python", "mylib"),
            ("rust", "demo_crate"),
            ("rust", "demo_crate::models"),
        ]
    );
    // The file as discovered, as Python reports it: source links strip the
    // project directory and the manifest hashes the path as written.
    assert_eq!(
        parsed.modules[2].source_file,
        root.join("crates/demo/src/models.rs").display().to_string()
    );
    assert_eq!(parsed.modules[2].types[0].name, "Point");
    assert_eq!(
        parsed.scanned_paths,
        [root.join("mylib"), root.join("crates")]
    );
    assert!(parsed.warnings.is_empty(), "{:?}", parsed.warnings);
}

#[test]
fn a_syntax_error_fails_naming_the_file() {
    let (_guard, root, config) =
        project("project:\n  name: Demo\nsource:\n  python:\n    paths: [pkg]\n");
    write(&root.join("pkg/__init__.py"), "");
    write(&root.join("pkg/broken.py"), "def broken(:\n    pass\n");
    let err = parse_language_sources(&config).unwrap_err();
    assert!(matches!(err, DocsError::Parse(_)));
    assert!(
        err.to_string().ends_with(&format!(
            "({}, line 1)",
            root.join("pkg/broken.py").display()
        )),
        "{err}"
    );
}

#[test]
fn a_rust_syntax_error_fails_naming_the_file() {
    let (_guard, root, config) =
        project("project:\n  name: Demo\nsource:\n  rust:\n    paths: [crates]\n");
    write(
        &root.join("crates/demo/Cargo.toml"),
        "[package]\nname = \"demo\"\n",
    );
    write(&root.join("crates/demo/src/lib.rs"), "pub fn broken( {}\n");
    let err = parse_language_sources(&config).unwrap_err();
    assert!(matches!(err, DocsError::ParseRust(_)));
    assert!(
        err.to_string().ends_with(&format!(
            "({}, line 1)",
            root.join("crates/demo/src/lib.rs").display()
        )),
        "{err}"
    );
}

#[test]
fn a_javascript_syntax_error_fails_naming_the_file() {
    let (_guard, root, config) =
        project("project:\n  name: Demo\nsource:\n  javascript:\n    paths: [web]\n");
    write(&root.join("web/index.js"), "export function broken( {\n");
    let err = parse_language_sources(&config).unwrap_err();
    assert!(matches!(err, DocsError::ParseJavaScript(_)));
    assert!(
        err.to_string().ends_with(&format!(
            "({}, line 1)",
            root.join("web/index.js").display()
        )),
        "{err}"
    );
}

#[test]
fn a_module_beside_a_package_of_the_same_name_is_a_route_collision() {
    let (_guard, root, config) =
        project("project:\n  name: Demo\nsource:\n  python:\n    paths: [pkg]\n");
    write(&root.join("pkg/__init__.py"), "");
    write(&root.join("pkg/foo.py"), "X = 1\n");
    write(&root.join("pkg/foo/__init__.py"), "Y = 2\n");
    let err = parse_language_sources(&config).unwrap_err();
    assert_eq!(
        err.to_string(),
        format!(
            "Documentation route collision at public route 'api-reference/pkg/foo': 'api-reference/pkg/foo' ({}) and 'api-reference/pkg/foo' ({})",
            root.join("pkg/foo/__init__.py").display(),
            root.join("pkg/foo.py").display()
        )
    );
    // `folio coverage` never wrote a page, so it keeps both modules.
    let parsed = parse_python_sources(&config).unwrap();
    let names: Vec<&str> = parsed.modules.iter().map(|m| m.name.as_str()).collect();
    assert_eq!(names, ["pkg", "pkg.foo", "pkg.foo"]);
}

#[test]
fn doc_sources_follow_paths_and_report_missing_roots_and_rst() {
    let (_guard, root, config) =
        project("project:\n  name: Demo\nsource:\n  docs: [docs, missing-docs, legacy]\n");
    write(&root.join("docs/index.md"), "# Home\n\nWelcome.\n");
    write(&root.join("docs/guide/README.md"), "# Guide\n");
    write(&root.join("legacy/old.rst"), "Old\n===\n");
    write(&root.join("legacy/new.md"), "# New\n");

    let parsed = parse_doc_sources(&config).unwrap();
    let routes: Vec<&str> = parsed.docs.iter().map(|d| d.route.as_str()).collect();
    assert_eq!(routes, ["guide/index", "index", "new"]);
    assert_eq!(
        parsed.scanned_paths,
        [root.join("docs"), root.join("legacy")]
    );
    let missing = root.join("missing-docs");
    assert_eq!(
        parsed.missing_paths,
        [missing.to_string_lossy().to_string()]
    );
    assert_eq!(
        parsed.warnings,
        [
            format!("Documentation source path not found: {}", missing.display()),
            folio_mdx::RST_WARNING.to_string(),
        ]
    );
    assert_eq!(
        parsed.docs[1].source_file,
        root.join("docs/index.md").to_string_lossy()
    );
}

#[test]
fn a_root_of_dot_never_reads_the_last_build() {
    let (_guard, root, config) =
        project("project:\n  name: Demo\noutput: out\nsource:\n  javascript:\n    paths: [.]\n");
    write(
        &root.join("app.js"),
        "/** App. */\nexport function app() {}\n",
    );
    write(
        &root.join("out/_next/static/chunk.js"),
        "export function chunk() {}\n",
    );
    let parsed = parse_language_sources(&config).unwrap();
    let names: Vec<&str> = parsed.modules.iter().map(|m| m.name.as_str()).collect();
    assert_eq!(names, ["app"]);
    let discovered: Vec<String> = discover_sources(&config)
        .iter()
        .map(|f| f.module_name.clone())
        .collect();
    assert_eq!(discovered, ["app"]);
}
