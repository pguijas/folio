use super::*;

#[test]
fn embedded_template_lists_the_files_the_workspace_needs() {
    let names: Vec<&str> = TEMPLATE_FILES.iter().map(|(rel, _)| *rel).collect();
    for needed in REQUIRED_TEMPLATE_FILES.iter().filter(|n| **n != "app") {
        assert!(
            names.contains(needed),
            "{needed} missing from the embedded template"
        );
    }
    assert!(names.contains(&"content/_meta.json") && names.contains(&"public/.gitkeep"));
    assert!(!names.iter().any(|n| n.starts_with("node_modules/")
        || n.starts_with(".next/")
        || n.starts_with("out/")));
    let mut sorted = names.clone();
    sorted.sort();
    assert_eq!(names, sorted);
}

#[test]
fn materialise_is_idempotent_and_the_workspace_copies_only_template_files() {
    let dir = tempfile::tempdir().unwrap();
    let dest = dir.path().join("cache").join("0.3.0-abc");
    materialise_template(&dest).unwrap();
    assert!(is_materialised_bundle(&dest));
    assert_eq!(
        std::fs::read_to_string(dest.join(BUNDLED_MARKER)).unwrap(),
        TEMPLATE_HASH
    );
    assert_eq!(TEMPLATE_HASH.len(), 64);
    assert!(validate_template_marker_contract(&dest).is_empty());
    let lock = dest.join("pnpm-lock.yaml");
    let before = std::fs::metadata(&lock).unwrap().modified().unwrap();
    std::fs::write(dest.join("foreign.txt"), "planted").unwrap();
    materialise_template(&dest).unwrap();
    assert_eq!(
        std::fs::metadata(&lock).unwrap().modified().unwrap(),
        before
    );
    assert!(
        dest.join("foreign.txt").exists(),
        "a materialised dir is never pruned"
    );
    let siblings: Vec<_> = std::fs::read_dir(dir.path().join("cache"))
        .unwrap()
        .map(|e| e.unwrap().file_name())
        .collect();
    assert_eq!(
        siblings,
        vec![std::ffi::OsString::from("0.3.0-abc")],
        "no tmp dir left behind"
    );

    let build = dir.path().join("build");
    TemplateWorkspace::new(&dest, &build, None)
        .prepare(false)
        .unwrap();
    assert!(build.join("app/layout.tsx").exists() && build.join("mdx-components.tsx").exists());
    assert!(
        !build.join("foreign.txt").exists(),
        "foreign files never reach the workspace"
    );
    assert!(
        !build.join("next.config.mjs").exists()
            && !build.join("content").join("_meta.json").exists()
    );
    assert!(!build.join(BUNDLED_MARKER).exists());

    assert_eq!(
        find_bundled_template_dir_with(Some(dest.to_str().unwrap())).unwrap(),
        dest
    );
    let missing = dir.path().join("nowhere");
    assert_eq!(
        find_bundled_template_dir_with(Some(missing.to_str().unwrap()))
            .unwrap_err()
            .to_string(),
        format!("FOLIO_TEMPLATE_DIR does not exist: {}", missing.display())
    );
}

#[test]
fn build_context_and_generator_fingerprint() {
    let dir = tempfile::tempdir().unwrap();
    let config_path = dir.path().join("docs.yaml");
    std::fs::write(&config_path, "project:\n  name: T\n").unwrap();
    let ctx = build_manifest_context(&config_path, dir.path(), "main", "", "/docs", "gen");
    assert_eq!(ctx.config, sha256_hex(b"project:\n  name: T\n"));
    assert_eq!(ctx.experimental_features, "disabled");
    let text = serde_json::to_string(&ctx).unwrap();
    assert!(
        text.starts_with("{\"config\":")
            && text.contains("\"generator\":\"gen\"")
            && !text.contains("backend")
    );
    assert_eq!(generator_fingerprint().len(), 64);
}

#[test]
fn docs_route_base_defaults_to_docs() {
    let dir = tempfile::tempdir().unwrap();
    let mapping: serde_yaml_ng::Mapping = serde_yaml_ng::from_str(
        "project:\n  name: T\ntemplate:\n  docs_route_base: /reference/docs/\n",
    )
    .unwrap();
    let config =
        folio_config::parse_docs_config_with(&mapping, dir.path(), "", &mut Vec::new()).unwrap();
    assert_eq!(docs_route_base(&config), "/reference/docs");
}

/// A remote package is already pinned, so the build context takes the digest
/// and needs nothing on disk. That is what lets the context invalidate before
/// the package has been fetched.
#[test]
fn a_remote_theme_package_signs_the_build_context_with_its_pin() {
    let dir = tempfile::tempdir().unwrap();
    let mapping: serde_yaml_ng::Mapping =
        serde_yaml_ng::from_str("project:\n  name: T\noutput: output\n").unwrap();
    let mut config =
        folio_config::parse_docs_config_with(&mapping, dir.path(), "", &mut Vec::new()).unwrap();
    let pin = |digest: &str| folio_config::RemoteThemePackage {
        git: "https://example.test/theme".to_string(),
        rev: "v1".to_string(),
        digest: digest.to_string(),
        path: String::new(),
    };

    let first = format!("sha256:{}", "a".repeat(64));
    config.theme.package_remote = Some(pin(&first));
    assert_eq!(theme_package_signature(&config).unwrap(), first);

    let second = format!("sha256:{}", "b".repeat(64));
    config.theme.package_remote = Some(pin(&second));
    assert_eq!(theme_package_signature(&config).unwrap(), second);

    // A local package with no directory on disk still signs as nothing.
    config.theme.package_remote = None;
    config.theme.package_path = dir.path().join("nope").to_string_lossy().into_owned();
    assert_eq!(theme_package_signature(&config).unwrap(), "");
}
