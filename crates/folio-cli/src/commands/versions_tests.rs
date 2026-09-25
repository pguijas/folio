use super::*;

#[test]
fn version_output_paths_stay_inside_the_output_dir() {
    let dir = tempfile::tempdir().unwrap();
    let base = dir.path().canonicalize().unwrap().join("_site");
    assert_eq!(
        resolve_version_output_dir(&base, " v1 ").unwrap(),
        base.join("v1")
    );
    assert_eq!(
        resolve_version_output_dir(&base, "").unwrap_err(),
        "Version output path must be a non-empty relative path"
    );
    assert_eq!(
        resolve_version_output_dir(&base, "/abs").unwrap_err(),
        "Version output path must be relative to the output directory"
    );
    for escape in ["../x", ".", "v1/.."] {
        assert_eq!(
            resolve_version_output_dir(&base, escape).unwrap_err(),
            "Version output path must stay within the output directory",
            "{escape}"
        );
    }
}

#[test]
fn redirect_manifest_and_hash_shapes() {
    let dir = tempfile::tempdir().unwrap();
    write_default_version_redirect(dir.path(), "/latest/").unwrap();
    let html = fs::read_to_string(dir.path().join("index.html")).unwrap();
    assert!(html.contains("content=\"0; url=latest/\""));
    assert!(html.starts_with("<!doctype html>\n") && html.ends_with("</html>\n"));
    write_default_version_redirect(dir.path(), "a\"b").unwrap();
    assert!(fs::read_to_string(dir.path().join("index.html"))
        .unwrap()
        .contains("url=a&quot;b/"));

    let versions = vec![json!({"label": "latest", "path": "latest"})];
    let synced = json!({"roadmap": {"phases": []}});
    let manifest = version_build_manifest(&versions[0], "abc", &versions, &synced);
    let keys: Vec<&String> = manifest.as_object().unwrap().keys().collect();
    assert_eq!(
        keys,
        [
            "commit",
            "folio_version",
            "label",
            "path",
            "ref",
            "schema",
            "synced_config_hash",
            "versions_hash"
        ]
    );
    assert_eq!(manifest["folio_version"], env!("CARGO_PKG_VERSION"));
    assert_eq!(manifest["ref"], "");
    assert_eq!(
        stable_hash(&json!({"b": 1, "a": [{"d": 1, "c": 2}]})),
        stable_hash(&json!({"a": [{"c": 2, "d": 1}], "b": 1}))
    );
    // A missing label falls back to the path.
    let unlabeled = version_build_manifest(&json!({"path": "v1"}), "", &versions, &synced);
    assert_eq!(unlabeled["label"], "v1");
}

#[test]
fn sync_version_matrix_replaces_versions_and_synced_keys_in_place() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("docs.yaml");
    fs::write(
            &path,
            "project:\n  name: Old\nversions:\n  - label: stale\nroadmap:\n  phases: []\ntheme:\n  dark_mode: true\n",
        )
        .unwrap();
    let versions = vec![json!({"label": "latest", "path": "latest"})];
    let mut synced = serde_json::Map::new();
    synced.insert("roadmap".into(), json!({"phases": [{"id": "x"}]}));
    sync_version_matrix(&path, &versions, &synced).unwrap();
    let loaded: serde_yaml_ng::Value =
        serde_yaml_ng::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
    let keys: Vec<&str> = loaded
        .as_mapping()
        .unwrap()
        .keys()
        .map(|k| k.as_str().unwrap())
        .collect();
    assert_eq!(keys, ["project", "versions", "roadmap", "theme"]);
    assert_eq!(loaded["versions"][0]["label"], "latest");
    assert_eq!(loaded["roadmap"]["phases"][0]["id"], "x");
    assert_eq!(loaded["project"]["name"], "Old");
}
