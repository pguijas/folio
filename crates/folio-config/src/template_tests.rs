use super::*;
use serde_yaml_ng::Value;

fn s(text: &str) -> Value {
    Value::String(text.to_string())
}

#[test]
fn docs_route_base_rejects_traversal() {
    for value in ["/..", "/../../x", "/a/../b", "/docs/.", "/./docs"] {
        let err = normalize_docs_route_base(&s(value)).unwrap_err();
        assert_eq!(
            err.to_string(),
            "template.docs_route_base cannot contain '.' or '..' segments",
            "{value}"
        );
    }
}

#[test]
fn docs_route_base_rejects_root_and_query() {
    for value in ["/", "///"] {
        assert_eq!(
            normalize_docs_route_base(&s(value))
                .unwrap_err()
                .to_string(),
            "template.docs_route_base must be a non-root URL path"
        );
    }
    for value in ["/docs?x", "/docs#top"] {
        assert_eq!(
            normalize_docs_route_base(&s(value))
                .unwrap_err()
                .to_string(),
            "template.docs_route_base cannot include query or fragment"
        );
    }
}

#[test]
fn docs_route_base_segments_are_plain_url_words() {
    for value in [
        "/do\"cs",
        "/docs`",
        "/_private",
        "/(group)/docs",
        "/[slug]",
        "/@slot",
        "/a//b",
        "/docs v2",
    ] {
        let err = normalize_docs_route_base(&s(value))
            .unwrap_err()
            .to_string();
        assert!(
            err.starts_with("template.docs_route_base segments must start with a letter or digit"),
            "{value}: {err}"
        );
    }
    assert_eq!(
        normalize_docs_route_base(&s("/Docs/v1.2_beta~x-y")).unwrap(),
        "/Docs/v1.2_beta~x-y"
    );
}

#[test]
fn docs_route_base_happy_path_intact() {
    assert_eq!(
        normalize_docs_route_base(&s("/reference/docs/")).unwrap(),
        "/reference/docs"
    );
    assert_eq!(normalize_docs_route_base(&s("docs")).unwrap(), "/docs");
    assert_eq!(normalize_docs_route_base(&s("  ")).unwrap(), "/docs");
    assert_eq!(normalize_docs_route_base(&Value::Null).unwrap(), "/docs");
    assert_eq!(
        normalize_docs_route_base(&Value::Bool(true)).unwrap(),
        "/docs"
    );
}

#[test]
fn base_path_is_normalised_or_empty() {
    for (input, expected) in [
        (s("docs"), "/docs"),
        (s("/my-repo/"), "/my-repo"),
        (s(" / "), ""),
        (s(""), ""),
        (s("///"), ""),
        (Value::Null, ""),
        (Value::Number(3.into()), ""),
    ] {
        assert_eq!(normalize_base_path(&input), expected, "{input:?}");
    }
}
