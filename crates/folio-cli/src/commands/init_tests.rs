use super::*;

fn info(python_path: Option<&str>) -> ProjectInfo {
    ProjectInfo {
        python_path: python_path.map(str::to_string),
        ..ProjectInfo::defaults("Demo")
    }
}

#[test]
fn dependency_names_drop_extras_markers_and_versions() {
    for (spec, name) in [
        ("Typer[all]>=0.9 ; python_version>\"3.8\"", "typer"),
        ("fastapi", "fastapi"),
        ("Django>=4", "django"),
        ("flask_sqlalchemy ~= 3.0", "flask-sqlalchemy"),
        ("click!=8.1", "click"),
        ("  Requests  ", "requests"),
    ] {
        assert_eq!(dependency_name(spec), name, "{spec}");
    }
}

#[test]
fn frameworks_come_from_every_dependency_list() {
    let table: toml::Table = r#"
[project]
name = "x"
dependencies = ["requests"]
[project.optional-dependencies]
web = ["FastAPI>=0.1"]
[dependency-groups]
dev = ["typer", 3]
"#
    .parse()
    .unwrap();
    let names = project_dependency_names(&table);
    assert_eq!(
        names,
        ["fastapi", "requests", "typer"]
            .map(str::to_string)
            .into_iter()
            .collect()
    );
    assert_eq!(detect_framework(Some(&table)), "Typer package");
    let plain: toml::Table = "[project]\nname = \"x\"\n".parse().unwrap();
    assert_eq!(detect_framework(Some(&plain)), "Python package");
    let empty: toml::Table = "".parse().unwrap();
    assert_eq!(detect_framework(Some(&empty)), "Python project");
    assert_eq!(detect_framework(None), "Python project");
    let click: toml::Table = "[project]\ndependencies = [\"Click\"]\n".parse().unwrap();
    assert_eq!(detect_framework(Some(&click)), "Click package");
}

#[test]
fn yaml_scalars_quote_hostile_values() {
    let hostile = "x\"\nplugins: [\"docs/evil.py\"]\ntrailing:\n  key: \"y";
    let raw = generate_docs_yaml(&ProjectInfo {
        name: hostile.to_string(),
        repo: hostile.to_string(),
        ..info(None)
    });
    let parsed: serde_yaml_ng::Value = serde_yaml_ng::from_str(&raw).unwrap();
    assert_eq!(parsed["project"]["name"].as_str(), Some(hostile));
    assert_eq!(parsed["project"]["repo"].as_str(), Some(hostile));
    assert!(parsed.get("plugins").is_none());
    assert!(parsed.get("trailing").is_none());
    assert_eq!(yaml_scalar("ünïcode"), "\"ünïcode\"");
}

#[test]
fn docstring_style_lands_under_source_python_only_when_not_auto() {
    let numpy = ProjectInfo {
        docstring_style: "numpy".to_string(),
        ..info(Some("src/demo"))
    };
    let raw = generate_docs_yaml(&numpy);
    let parsed: serde_yaml_ng::Value = serde_yaml_ng::from_str(&raw).unwrap();
    assert_eq!(
        parsed["source"]["python"]["docstring_style"].as_str(),
        Some("numpy")
    );
    assert!(parsed["project"].get("docstring_style").is_none());
    assert!(parsed.get("landing").is_none());
    assert!(raw.contains(
        "    paths:\n      - \"src/demo\"\n    docstring_style: \"numpy\"\n    # exclude:"
    ));
    assert!(!generate_docs_yaml(&info(Some("src/"))).contains("docstring_style"));
}

#[test]
fn generated_config_matches_the_empty_project_template() {
    let raw = generate_docs_yaml(&info(None));
    let expected = r#"# Folio configuration
# Full reference: https://pguijas.github.io/folio/docs/configuration

project:
  name: "Demo"
  version: "0.1.0"
  # repo: "https://github.com/owner/repo"

source:
  # No Python sources detected; uncomment to publish an API reference.
  # python:
  #   paths:
  #     - "src/"
  docs:
    - "docs/"

output: "_site"

theme:
  preset: "organic-editorial"
  dark_mode: true
  # logo: "docs/logo.png"
  # favicon: "docs/favicon.ico"

llm:
  generate_llms_txt: true
  generate_llms_full_txt: true
"#;
    assert_eq!(raw, expected);
    let with_repo = generate_docs_yaml(&ProjectInfo {
        repo: "https://github.com/o/r".into(),
        ..info(Some("src/"))
    });
    assert!(with_repo.contains("  repo: \"https://github.com/o/r\"\n"));
    assert!(with_repo.contains("nav:\n  - \"API Reference\"\n"));
}

#[test]
fn documentation_status_reads_the_scaffold() {
    let dir = tempfile::tempdir().unwrap();
    assert_eq!(
        documentation_status(dir.path()),
        "Documentation scaffold not found"
    );
    fs::create_dir(dir.path().join("docs")).unwrap();
    assert_eq!(
        documentation_status(dir.path()),
        "docs/ found, docs.yaml missing"
    );
    fs::write(dir.path().join("docs.yaml"), "").unwrap();
    assert_eq!(
        documentation_status(dir.path()),
        "Documentation scaffold found"
    );
}

#[test]
fn detected_sources_are_summarised_per_language() {
    assert_eq!(source_summary(&info(None)), "no sources detected");
    assert_eq!(source_summary(&info(Some("src/demo"))), "src/demo (Python)");
    let mixed = ProjectInfo {
        javascript_path: Some("web/".into()),
        rust_path: Some("./".into()),
        ..info(Some("demo/"))
    };
    assert_eq!(
        source_summary(&mixed),
        "demo/ (Python), web/ (JavaScript), ./ (Rust)"
    );
}

#[test]
fn generated_config_writes_every_detected_source() {
    let raw = generate_docs_yaml(&ProjectInfo {
        javascript_path: Some("src/".into()),
        rust_path: Some("./".into()),
        ..info(None)
    });
    assert!(raw.contains(
        "source:\n  javascript:\n    paths:\n      - \"src/\"\n  rust:\n    paths:\n      - \"./\"\n  docs:\n"
    ));
    assert!(!raw.contains("# python:"), "sources exist: no Python hint");
    assert!(raw.contains("nav:\n  - \"API Reference\"\n"));
    let parsed: serde_yaml_ng::Value = serde_yaml_ng::from_str(&raw).unwrap();
    assert!(parsed["source"].get("python").is_none());
}

#[test]
fn source_files_are_found_outside_dependency_and_build_dirs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fs::create_dir_all(root.join("node_modules/x")).unwrap();
    fs::write(root.join("node_modules/x/a.js"), "").unwrap();
    fs::create_dir_all(root.join("target/debug")).unwrap();
    fs::write(root.join("target/debug/b.py"), "").unwrap();
    fs::create_dir_all(root.join(".hidden")).unwrap();
    fs::write(root.join(".hidden/c.md"), "").unwrap();
    for ext in ["js", "py", "md"] {
        assert!(!contains_source(root, &[ext]), "{ext}");
    }
    fs::create_dir_all(root.join("lib/deep")).unwrap();
    fs::write(root.join("lib/deep/d.mjs"), "").unwrap();
    assert!(contains_source(root, &["js", "mjs"]));
    assert!(!contains_source(&root.join("missing"), &["mjs"]));
}
