use serde_json::json;

use crate::docs::testing::{parse_err, parse_ok, parse_yaml};

#[test]
fn template_path_and_params_parse_without_warnings() {
    let config = parse_ok("project: {name: T}\ntemplate:\n  path: docs-template\n  params:\n    navbarVariant: dense\n    productName: Acme SDK\n    showBetaBadge: true\n");
    assert_eq!(config.template.path, "docs-template");
    assert_eq!(config.template.overlay_path, "");
    assert_eq!(
        serde_json::Value::Object(config.template.params.clone()),
        json!({"navbarVariant": "dense", "productName": "Acme SDK", "showBetaBadge": true})
    );
    let resolved = config.resolve_paths(std::path::Path::new("/proj")).unwrap();
    assert_eq!(resolved.template.path, "/proj/docs-template");
    assert_eq!(resolved.template.params, config.template.params);
}

#[test]
fn overlay_path_is_dropped_when_path_is_set() {
    let config = parse_ok("project: {name: T}\ntemplate:\n  overlay_path: overlay\n");
    assert_eq!(config.template.overlay_path, "overlay");
    let (config, warnings) = parse_yaml(
        "project: {name: T}\ntemplate:\n  path: docs-template\n  overlay_path: overlay\n",
    )
    .unwrap();
    assert_eq!(config.template.path, "docs-template");
    assert_eq!(config.template.overlay_path, "");
    assert_eq!(warnings, ["template.overlay_path is ignored when template.path is set; template.path is a full replacement"]);
    assert_eq!(
        parse_ok("project: {name: T}\ntemplate:\n  path: 3\n  overlay_path: 3\n")
            .template
            .path,
        ""
    );
    assert_eq!(
        parse_ok("project: {name: T}\ntemplate: nope\n")
            .template
            .docs_route_base,
        "/docs"
    );
}

#[test]
fn params_defaults_warnings_and_errors() {
    assert!(parse_ok("project: {name: T}\ntemplate:\n  path: t\n")
        .template
        .params
        .is_empty());
    assert!(parse_ok("project: {name: T}\ntemplate:\n  params: null\n")
        .template
        .params
        .is_empty());
    let (config, warnings) =
        parse_yaml("project: {name: T}\ntemplate:\n  params:\n    - dense\n    - compact\n")
            .unwrap();
    assert!(config.template.params.is_empty());
    assert_eq!(warnings, ["template.params must be a mapping; ignoring it"]);
    assert_eq!(
        parse_err("project: {name: T}\ntemplate:\n  params:\n    ok: 1\n    ? [a]\n    : x\n"),
        "template.params must be JSON-serializable"
    );
}

#[test]
fn docs_route_base_is_normalised_at_load() {
    assert_eq!(
        parse_ok("project: {name: T}\ntemplate:\n  docs_route_base: \"/reference/docs/\"\n")
            .template
            .docs_route_base,
        "/reference/docs"
    );
    assert_eq!(
        parse_err("project: {name: T}\ntemplate:\n  docs_route_base: \"/a/../b\"\n"),
        "template.docs_route_base cannot contain '.' or '..' segments"
    );
}
