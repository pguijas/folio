use super::*;
use folio_config::parse_docs_config_with;

fn config(yaml: &str) -> DocsConfig {
    let raw: serde_yaml_ng::Mapping = serde_yaml_ng::from_str(yaml).unwrap();
    parse_docs_config_with(&raw, Path::new("/proj"), "", &mut Vec::new()).unwrap()
}

#[test]
fn enabled_languages_follow_configured_paths_python_first() {
    assert_eq!(
        enabled_languages(&config("source:\n  python: [mylib]\n")),
        ["python"]
    );
    assert_eq!(
        enabled_languages(&config("source:\n  javascript:\n    paths: [web]\n")),
        ["javascript"]
    );
    assert_eq!(
        enabled_languages(&config(
            "source:\n  rust:\n    paths: [crates]\n  python: [mylib]\n"
        )),
        ["python", "rust"]
    );
    assert!(enabled_languages(&config("project:\n  name: Demo\n")).is_empty());
    assert!(has_parser("python"));
    assert!(has_parser("rust"));
    assert!(has_parser("javascript"));
    assert!(!has_parser("cobol"));
}
