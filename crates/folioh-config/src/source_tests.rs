use super::*;

#[test]
fn language_ids_and_labels() {
    assert_eq!(LANGUAGE_IDS, ["python", "javascript", "rust"]);
    assert_eq!(language_label("python"), "Python");
    assert_eq!(language_label("javascript"), "JavaScript");
    assert_eq!(language_label("rust"), "Rust");
    assert_eq!(language_label("cobol"), "Cobol");
    assert_eq!(language_label("objective-c"), "Objective-C");
    assert_eq!(DOCSTRING_STYLES, ["auto", "google", "numpy"]);
    assert_eq!(DEFAULT_DOCSTRING_STYLE, "auto");
}

#[test]
fn default_route_namespaces_non_python_languages() {
    assert_eq!(
        default_route("python", "mylib.core"),
        "api-reference/mylib/core"
    );
    assert_eq!(
        default_route("javascript", "lib.util"),
        "api-reference/javascript/lib/util"
    );
    assert_eq!(default_route("rust", "geo"), "api-reference/rust/geo");
}
