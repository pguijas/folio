//! Loading `docs.yaml` from disk: the fixtures, the file-level errors and
//! `resolve_paths` against a real project directory.

use std::fs;
use std::path::{Path, PathBuf};

use folio_config::{
    load_docs_config, load_docs_config_in, load_docs_config_with_keys, ConfigError, DocsConfig,
    LanguageSource,
};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

/// The checked-in config this crate loads; its directory is the project
/// directory the loader must resolve against.
fn fixtures() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures")
        .canonicalize()
        .unwrap()
}

fn project(docs_yaml: &str) -> (tempfile::TempDir, PathBuf) {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    fs::write(root.join("docs.yaml"), docs_yaml).unwrap();
    (dir, root)
}

fn load(root: &Path) -> DocsConfig {
    let loaded = load_docs_config(&root.join("docs.yaml")).unwrap();
    assert_eq!(loaded.warnings, Vec::<String>::new());
    loaded.config
}

#[test]
fn the_config_fixture_loads_with_the_documented_values() {
    let loaded = load_docs_config(&fixtures().join("docs.yaml")).unwrap();
    assert_eq!(loaded.warnings, Vec::<String>::new());
    let config = loaded.config;
    assert_eq!(config.project.name, "TestProject");
    assert_eq!(config.project.version, "1.0.0");
    assert_eq!(config.project.repo, "https://github.com/test/test");
    assert_eq!(config.project.repo_ref, "main");
    assert_eq!(
        config.language_source("python"),
        LanguageSource {
            paths: vec!["src/".into()],
            excludes: vec!["src/tests/".into()]
        }
    );
    assert_eq!(config.source.docs, ["docs/"]);
    assert_eq!(config.output_dir, "_site");
    assert!(config.theme.dark_mode);
    assert_eq!(config.theme.preset, "organic-editorial");
    assert_eq!(config.nav, ["Introduction", "API Reference"]);
    assert!(config.llm.generate_llms_txt && config.llm.generate_llms_full_txt);
    assert_eq!(
        config.source.languages.keys().collect::<Vec<_>>(),
        ["python"]
    );
    assert_eq!(
        config.language_source("javascript"),
        LanguageSource::default()
    );
    assert_eq!(config.project_dir, fixtures());
    assert_eq!(loaded.raw["project"]["name"], "TestProject");
    assert_eq!(
        loaded.raw.keys().collect::<Vec<_>>(),
        ["project", "source", "output", "theme", "nav", "llm"]
    );
}

#[test]
fn folios_own_docs_yaml_loads_without_config_warnings() {
    let loaded = load_docs_config(&repo_root().join("docs.yaml")).unwrap();
    assert_eq!(loaded.warnings, Vec::<String>::new());
    let config = loaded.config;
    assert_eq!(config.project.version, "0.3.0-a1");
    assert_eq!(config.theme.package_path, "theme/folio-site");
    assert_eq!(config.components.specs.len(), 1);
    assert_eq!(
        config.components.specs[0].from.as_deref(),
        Some("./docs/components/benchmark-chart.tsx")
    );
    assert!(config.landing_enabled);
    assert!(loaded.raw.contains_key("roadmap"));
    let resolved = config.resolve_paths(&repo_root()).unwrap();
    assert_eq!(
        resolved.theme.package_path,
        repo_root().join("theme/folio-site").to_string_lossy()
    );
}

#[test]
fn every_bundled_example_loads_without_config_warnings() {
    for example in ["generated-site", "javascript", "landing-page", "rust"] {
        let path = repo_root()
            .join("docs/examples")
            .join(example)
            .join("docs.yaml");
        let loaded = load_docs_config(&path).unwrap();
        assert_eq!(loaded.warnings, Vec::<String>::new(), "{example}");
    }
}

#[test]
fn file_level_errors() {
    let err = load_docs_config(Path::new("/nonexistent/docs.yaml")).unwrap_err();
    assert_eq!(
        err,
        ConfigError::NotFound(PathBuf::from("/nonexistent/docs.yaml"))
    );
    assert_eq!(
        err.to_string(),
        "Config file not found: /nonexistent/docs.yaml"
    );

    let (_dir, root) = project("- not\n- a mapping\n");
    let path = root.join("docs.yaml");
    let err = load_docs_config(&path).unwrap_err();
    assert_eq!(
        err,
        ConfigError::Yaml(format!(
            "Config file must contain a mapping: {}",
            path.display()
        ))
    );

    fs::write(&path, "project:\n  name: A\nproject:\n  name: B\n").unwrap();
    let err = load_docs_config(&path).unwrap_err();
    assert!(
        matches!(err, ConfigError::Yaml(ref m) if m.contains("duplicate")),
        "{err}"
    );

    fs::write(&path, "project: [unclosed\n").unwrap();
    assert!(matches!(
        load_docs_config(&path).unwrap_err(),
        ConfigError::Yaml(_)
    ));

    fs::write(&path, "").unwrap();
    let loaded = load_docs_config(&path).unwrap();
    assert_eq!(loaded.config.project.name, "Untitled");
    assert_eq!(loaded.warnings.len(), 1);
    assert!(loaded.raw.is_empty());
}

#[test]
fn project_dir_is_canonical_before_resolve_and_resolve_is_idempotent() {
    let (dir, root) = project("project:\n  name: P\n");
    // The raw temp path may go through a symlink (macOS /tmp); the config
    // carries the canonical directory from the start.
    let loaded = load_docs_config(&dir.path().join("docs.yaml")).unwrap();
    assert_eq!(loaded.config.project_dir, root);
    let resolved = loaded.config.resolve_paths(dir.path()).unwrap();
    assert_eq!(resolved.project_dir, root);

    let elsewhere = root.join("elsewhere");
    fs::create_dir(&elsewhere).unwrap();
    let loaded = load_docs_config_in(&root.join("docs.yaml"), &elsewhere).unwrap();
    assert_eq!(loaded.config.project_dir, elsewhere);
}

#[test]
fn resolve_paths_makes_sources_and_output_absolute() {
    let (_dir, root) = project("project:\n  name: Test\nsource:\n  python:\n    paths: [\"src/\"]\n  docs: [\"docs/\"]\noutput: out\n");
    let resolved = load(&root).resolve_paths(&root).unwrap();
    assert_eq!(
        resolved.language_source("python").paths,
        [root.join("src").to_string_lossy()]
    );
    assert_eq!(resolved.source.docs, [root.join("docs").to_string_lossy()]);
    assert_eq!(resolved.output_dir, root.join("out").to_string_lossy());
}

#[test]
fn resolve_paths_rejects_unsafe_output() {
    let (_dir, root) = project("");
    let absolute = root.join("outside").to_string_lossy().into_owned();
    for output in ["../outside", ".", "", absolute.as_str()] {
        fs::write(
            root.join("docs.yaml"),
            format!("project:\n  name: Test\noutput: \"{output}\"\n"),
        )
        .unwrap();
        let config = load_docs_config(&root.join("docs.yaml")).unwrap().config;
        let err = config.resolve_paths(&root).unwrap_err();
        assert!(
            err.to_string().starts_with("Output directory"),
            "{output}: {err}"
        );
    }
}

#[test]
fn resolve_paths_rejects_an_output_that_would_delete_sources() {
    let (_dir, root) = project("");
    for (output, expected) in [
        ("docs", "source directory"),
        ("src", "source directory"),
        (".", "Output directory"),
        (".git", "must not"),
    ] {
        fs::write(
            root.join("docs.yaml"),
            format!("project:\n  name: Test\nsource:\n  python:\n    paths:\n      - \"src/\"\n  docs:\n    - \"docs/\"\noutput: \"{output}\"\n"),
        )
        .unwrap();
        let config = load_docs_config(&root.join("docs.yaml")).unwrap().config;
        let err = config.resolve_paths(&root).unwrap_err().to_string();
        assert!(err.contains(expected), "{output}: {err}");
    }
    fs::write(root.join("docs.yaml"), "project:\n  name: Test\nsource:\n  python:\n    paths: [\"src/\"]\n  docs: [\"docs/\"]\noutput: \"_site\"\n").unwrap();
    fs::create_dir(root.join("_site")).unwrap();
    let resolved = load(&root).resolve_paths(&root).unwrap();
    assert_eq!(resolved.output_dir, root.join("_site").to_string_lossy());
}

#[test]
fn resolve_paths_guards_the_theme_package() {
    let (_dir, root) = project("");
    let outside = root
        .parent()
        .unwrap()
        .join("evil-theme")
        .to_string_lossy()
        .into_owned();
    for package in [
        "../outside",
        ".build",
        ".build/theme",
        "_site",
        "_site/theme",
        outside.as_str(),
    ] {
        fs::write(
            root.join("docs.yaml"),
            format!("project:\n  name: T\ntheme:\n  package: \"{package}\"\n"),
        )
        .unwrap();
        let config = load_docs_config(&root.join("docs.yaml")).unwrap().config;
        let err = config.resolve_paths(&root).unwrap_err();
        assert!(
            err.to_string().starts_with("theme.package "),
            "{package}: {err}"
        );
    }
    fs::write(
        root.join("docs.yaml"),
        "project:\n  name: T\ntheme:\n  package: \"docs/theme/p2pfl\"\n",
    )
    .unwrap();
    let config = load_docs_config(&root.join("docs.yaml")).unwrap().config;
    assert_eq!(config.theme.package_path, "docs/theme/p2pfl");
    let resolved = config.resolve_paths(&root).unwrap();
    assert_eq!(
        resolved.theme.package_path,
        root.join("docs/theme/p2pfl").to_string_lossy()
    );
}

/// A `components:` entry is trusted frontend code like a theme package, so it
/// is held to the same containment rule: nothing outside the project.
#[test]
fn resolve_paths_guards_component_sources() {
    let (_dir, root) = project("");
    let outside = root
        .parent()
        .unwrap()
        .join("evil")
        .to_string_lossy()
        .into_owned();
    for body in [
        "components:\n  - ../outside\n".to_string(),
        format!("components:\n  - \"{outside}\"\n"),
        format!(
            "components:\n  - name: Evil\n    from: \"{outside}/evil.tsx\"\n    export: Evil\n"
        ),
        "components:\n  - name: Evil\n    from: ../outside/evil.tsx\n    export: Evil\n"
            .to_string(),
        // The legacy `path:` spelling of the same field.
        "components:\n  - name: Evil\n    path: ../outside/evil.tsx\n    export: Evil\n"
            .to_string(),
        format!(
            "components:\n  - name: Evil\n    path: \"{outside}/evil.tsx\"\n    export: Evil\n"
        ),
    ] {
        fs::write(
            root.join("docs.yaml"),
            format!("project:\n  name: T\n{body}"),
        )
        .unwrap();
        let config = load_docs_config(&root.join("docs.yaml")).unwrap().config;
        let error = config
            .resolve_paths(&root)
            .expect_err("a component outside the project is refused")
            .to_string();
        assert!(
            error.contains("must stay within the project directory"),
            "{body}: {error}"
        );
    }

    // Inside the project, it still loads.
    fs::create_dir_all(root.join("ui")).unwrap();
    fs::write(
        root.join("ui/thing.tsx"),
        "export const Thing = () => null\n",
    )
    .unwrap();
    fs::write(
        root.join("docs.yaml"),
        "project:\n  name: T\ncomponents:\n  - ui\n",
    )
    .unwrap();
    let config = load_docs_config(&root.join("docs.yaml")).unwrap().config;
    config
        .resolve_paths(&root)
        .expect("a component inside the project loads");
}

#[test]
fn resolve_paths_joins_template_components_and_language_roots() {
    let (_dir, root) = project(
        "project:\n  name: T\nsource:\n  javascript:\n    paths: [\"web/src\"]\n    exclude: [\"web/src/vendor\"]\n  rust:\n    paths: [\"crates/core\"]\ntemplate:\n  overlay_path: overlay\ncomponents:\n  - \"docs/components\"\n  - {name: Hero, from: \"docs/components/hero.tsx\", export: Hero, expose: {mdx: true}}\n",
    );
    let config = load(&root);
    let resolved = config.resolve_paths(&root).unwrap();
    assert_eq!(
        resolved.template.overlay_path,
        root.join("overlay").to_string_lossy()
    );
    assert_eq!(
        resolved.components.dirs,
        [root.join("docs/components").to_string_lossy()]
    );
    assert_eq!(
        resolved.components.specs[0].from.as_deref(),
        Some(
            root.join("docs/components/hero.tsx")
                .to_string_lossy()
                .as_ref()
        )
    );
    assert_eq!(
        resolved.language_source("javascript"),
        LanguageSource {
            paths: vec![root.join("web/src").to_string_lossy().into_owned()],
            excludes: vec![root.join("web/src/vendor").to_string_lossy().into_owned()],
        }
    );
    assert_eq!(
        resolved.language_source("rust").paths,
        [root.join("crates/core").to_string_lossy()]
    );
}

#[test]
fn only_registered_extension_keys_suppress_unknown_key_warnings() {
    let (_dir, root) = project("project: {name: Test}\nexample_plugin: {}\nzeta: true\n");
    let path = root.join("docs.yaml");
    let standalone = load_docs_config(&path).unwrap();
    assert_eq!(
        standalone.warnings,
        ["Unknown config keys in docs.yaml: example_plugin, zeta"]
    );
    let extended = load_docs_config_with_keys(&path, &root, &["example_plugin"]).unwrap();
    assert_eq!(
        extended.warnings,
        ["Unknown config keys in docs.yaml: zeta"]
    );
    assert_eq!(extended.raw["example_plugin"], serde_json::json!({}));
}
