use super::*;
use serde_json::json;

#[test]
fn the_seeded_cache_carries_the_manifest_hash_so_a_late_edit_is_stale() {
    let dir = tempfile::tempdir().unwrap();
    let source = dir.path().join("demo.py");
    std::fs::write(&source, "x = 1\n").unwrap();
    let recorded = hash_file(&source);
    let module = |name: &str, path: &Path| ModuleIR {
        name: name.to_string(),
        docstring: folio_ir::DocstringIR::default(),
        classes: vec![],
        functions: vec![],
        constants: vec![],
        source_file: path.to_string_lossy().into_owned(),
        language: folio_ir::Language::Python,
        types: vec![],
    };
    let unrecorded = dir.path().join("new.py");
    std::fs::write(&unrecorded, "y = 2\n").unwrap();
    let mut manifest = Manifest::default();
    manifest.sources.insert(
        key(&source),
        json!({"hash": recorded, "route": "api-reference/demo", "language": "python"}),
    );
    let modules = [module("demo", &source), module("new", &unrecorded)];
    let cache = seed_cache(&modules, &manifest);
    assert_eq!(cache.get(&source).unwrap().hash, recorded);
    assert_eq!(cache.get(&unrecorded).unwrap().hash, "");
    // Nothing moved for demo.py; new.py was never recorded, so it is re-parsed.
    assert_eq!(cache.stale(hash_file), vec![unrecorded.clone()]);
    // An edit that landed after the manifest was written is stale at once.
    std::fs::write(&source, "x = 2\n").unwrap();
    assert_eq!(cache.stale(hash_file), vec![source, unrecorded]);
}

#[test]
fn changed_since_names_the_first_key_whose_bytes_moved() {
    let dir = tempfile::tempdir().unwrap();
    let a = dir.path().join("a.md");
    let b = dir.path().join("b.md");
    std::fs::write(&a, "a").unwrap();
    std::fs::write(&b, "b").unwrap();
    let keys = vec![key(&a), key(&b), key(&dir.path().join("unknown.md"))];
    let hashes: HashMap<String, String> = keys
        .iter()
        .map(|k| (k.clone(), hash_file(Path::new(k))))
        .collect();
    assert_eq!(changed_since(&hashes, &keys), None);
    std::fs::write(&b, "changed").unwrap();
    assert_eq!(changed_since(&hashes, &keys), Some(&keys[1]));
    // A deleted file hashes to "" and counts as changed; an unknown key never does.
    std::fs::remove_file(&a).unwrap();
    assert_eq!(changed_since(&hashes, &keys), Some(&keys[0]));
    let mut fresh = hashes.clone();
    fresh.remove(&keys[0]);
    fresh.remove(&keys[1]);
    assert_eq!(changed_since(&fresh, &keys), None);
}
