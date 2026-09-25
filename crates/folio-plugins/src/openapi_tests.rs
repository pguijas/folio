use super::*;
use crate::hook::Plugin;
use crate::registry::ExtensionRegistry;
use crate::testing::{docs_config, MemoryBuilder};
use folio_config::DocsConfig;
use serde_json::{json, Map, Value};
use std::path::Path;

const COOKIE_SPEC: &str = r#"{
  "openapi": "3.1.0",
  "info": {"title": "Cookie Caper API", "version": "0.1.0", "description": "Coordinate snack retrieval without waking the baker."},
  "servers": [{"url": "https://api.cookie-caper.test"}, "junk", {"url": 3}],
  "paths": {
    "/cookies": {"get": {"summary": "List cookies", "operationId": "listCookies", "tags": ["Cookies", 4], "responses": {"200": {"description": "Cookie ledger"}}}},
    "/heists": {"post": {"summary": "Schedule a heist", "operationId": "scheduleHeist", "tags": ["Heists"], "responses": {"201": {"description": "Heist scheduled"}}}, "get": "junk"},
    "/junk": "not a path item"
  },
  "components": {"schemas": {"Cookie": {"type": "object"}, "HeistPlan": {"type": "object"}}}
}"#;

fn cookie_config(dir: &Path) -> DocsConfig {
    std::fs::write(dir.join("openapi.json"), COOKIE_SPEC).unwrap();
    let mut config = docs_config("project: {name: Cookie Caper}\n", dir);
    let raw: Map<String, Value> = serde_json::from_value(json!({"openapi": {"sources": [{"title": "Cookie Caper API", "path": "openapi.json", "route": "api-reference/http"}]}})).unwrap();
    OpenApiPlugin
        .configure(&mut config, &raw, &mut Vec::new())
        .unwrap();
    config
}

#[test]
fn plugin_is_inert_without_the_key() {
    let dir = tempfile::tempdir().unwrap();
    let mut config = docs_config("project: {name: Demo}\n", dir.path());
    assert_eq!(OpenApiPlugin.name(), "openapi");
    assert_eq!(OpenApiPlugin.config_keys(), ["openapi"]);
    OpenApiPlugin
        .configure(&mut config, &Map::new(), &mut Vec::new())
        .unwrap();
    assert!(config.extra.is_empty());
    let mut registry = ExtensionRegistry::default();
    OpenApiPlugin
        .register_extensions(&mut registry, &config, &mut Vec::new())
        .unwrap();
    assert!(registry.components.is_empty() && registry.data_modules.is_empty());
    let mut builder = MemoryBuilder::default();
    OpenApiPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert!(builder.pages.is_empty());
}

#[test]
fn configure_register_and_emit_the_cookie_caper_source() {
    let dir = tempfile::tempdir().unwrap();
    let config = cookie_config(dir.path());
    let sources = active_sources(&config).unwrap();
    assert_eq!(sources.len(), 1);
    let source = &sources[0];
    assert_eq!(source.title, "Cookie Caper API");
    assert_eq!(source.version, "0.1.0");
    assert_eq!(
        source.description,
        "Coordinate snack retrieval without waking the baker."
    );
    assert_eq!(source.route, "api-reference/http");
    assert_eq!(source.servers, ["https://api.cookie-caper.test"]);
    assert_eq!(source.spec["info"]["title"], json!("Cookie Caper API"));
    assert_eq!(
        serde_json::to_value(&source.operations).unwrap(),
        json!([
            {"method": "GET", "path": "/cookies", "summary": "List cookies", "description": "", "operationId": "listCookies", "tags": ["Cookies"]},
            {"method": "POST", "path": "/heists", "summary": "Schedule a heist", "description": "", "operationId": "scheduleHeist", "tags": ["Heists"]}
        ])
    );
    assert_eq!(source.schemas, ["Cookie", "HeistPlan"]);
    let keys: Vec<&str> = config.extra["openapi"]["sources"][0]
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        keys,
        [
            "title",
            "version",
            "description",
            "route",
            "servers",
            "operations",
            "schemas",
            "spec"
        ]
    );

    let mut registry = ExtensionRegistry::default();
    OpenApiPlugin
        .register_extensions(&mut registry, &config, &mut Vec::new())
        .unwrap();
    let component = &registry.components["OpenApiReference"];
    assert_eq!(component.import_path, "@/components/openapi-reference");
    assert!(component.expose_mdx && !component.contract && component.props.is_empty());
    let data = &registry.data_modules["openapi"];
    assert_eq!(data.export_name, "openApiSources");
    assert_eq!(data.module_path, "openapi-data");
    assert_eq!(data.type_annotation, "OpenApiSource[]");
    assert_eq!(data.type_source, OPENAPI_TYPES);
    assert!(data.data[0].get("spec").is_none());
    let keys: Vec<&str> = data.data[0]
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        keys,
        [
            "title",
            "version",
            "description",
            "route",
            "servers",
            "operations",
            "schemas"
        ]
    );

    let mut builder = MemoryBuilder::with_meta([(
            "api-reference",
            "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"cookie_caper_api\": \"Cookie Caper Api\",\n}",
        )]);
    OpenApiPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert_eq!(
            builder.pages["api-reference/http"],
            "import { OpenApiReference } from \"@/components/openapi-reference\"\n\n# Cookie Caper API\n\n<OpenApiReference sourceTitle=\"Cookie Caper API\" />\n"
        );
    let meta = &builder.meta["api-reference"];
    assert!(meta.contains("\"cookie_caper_api\": \"Cookie Caper Api\""));
    assert!(meta.contains("\"http\": \"Cookie Caper API\""));
    assert_eq!(meta.matches("\"display\": \"hidden\"").count(), 1);
    assert_eq!(
        builder.meta[""],
        "export default {\n  \"api-reference\": \"API Reference\",\n}"
    );
    assert!(builder.routes.contains("api-reference/http"));
}

#[test]
fn emit_rewrites_a_stale_page_and_leaves_a_current_one() {
    let dir = tempfile::tempdir().unwrap();
    let config = cookie_config(dir.path());
    let desired = docs_page_mdx("Cookie Caper API");
    let mut builder = MemoryBuilder::with_pages([("api-reference/http", "# Existing HTTP API\n")]);
    builder.meta.insert(
        "api-reference".into(),
        "export default {\n  \"index\": {\"display\": \"hidden\"},\n}".into(),
    );
    OpenApiPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert_eq!(builder.written_pages, ["api-reference/http"]);
    assert_eq!(builder.pages["api-reference/http"], desired);
    assert!(builder.meta["api-reference"].contains("\"http\": \"Cookie Caper API\""));

    let mut builder = MemoryBuilder::with_pages([("api-reference/http", desired.as_str())]);
    OpenApiPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert!(builder.written_pages.is_empty());
    assert!(builder.routes.contains("api-reference/http"));
}

#[test]
fn normalize_openapi_accepts_a_mapping_or_list_of_sources() {
    let dir = tempfile::tempdir().unwrap();
    let inline = json!({"openapi": "3.0.0", "info": {"title": "Inline"}, "paths": "junk"});
    let sources = normalize_openapi(
        &json!({"sources": {"content": inline}}),
        dir.path(),
        &mut Vec::new(),
    )
    .unwrap();
    assert_eq!(sources.len(), 1);
    assert_eq!(sources[0].title, "Inline");
    assert_eq!(sources[0].route, "api-reference/inline");
    assert!(
        sources[0].operations.is_empty()
            && sources[0].servers.is_empty()
            && sources[0].schemas.is_empty()
    );
    assert!(
        normalize_openapi(&json!("nope"), dir.path(), &mut Vec::new())
            .unwrap()
            .is_empty()
    );
    assert!(
        normalize_openapi(&json!({"sources": "nope"}), dir.path(), &mut Vec::new())
            .unwrap()
            .is_empty()
    );
    // Text content parses as YAML (JSON included); a non-mapping entry is dropped.
    let sources = normalize_openapi(
            &json!({"sources": ["junk", {"spec": "info:\n  title: Text API\n  version: 2\npaths:\n  /ok:\n    get: {summary: S}\n  42:\n    get: {summary: dropped}\n", "description": "Configured wins"}]}),
            dir.path(),
            &mut Vec::new(),
        )
        .unwrap();
    assert_eq!(sources.len(), 1);
    assert_eq!(sources[0].title, "Text API");
    assert_eq!(sources[0].version, "2");
    assert_eq!(sources[0].description, "Configured wins");
    // A numeric path key is not a path: dropped, never stringified.
    assert_eq!(
        sources[0]
            .operations
            .iter()
            .map(|o| o.path.as_str())
            .collect::<Vec<_>>(),
        ["/ok"]
    );
    // No title anywhere: `OpenAPI` and its slug route; the info description is the fallback.
    let sources = normalize_openapi(
        &json!({"sources": [{"content": {"info": {"description": "From info"}}}]}),
        dir.path(),
        &mut Vec::new(),
    )
    .unwrap();
    assert_eq!(sources[0].title, "OpenAPI");
    assert_eq!(sources[0].route, "api-reference/openapi");
    assert_eq!(sources[0].description, "From info");
    // No spec at all (blank path) is a non-mapping spec: warned and dropped.
    let mut diag = Vec::new();
    let sources =
        normalize_openapi(&json!({"sources": [{"path": "  "}]}), dir.path(), &mut diag).unwrap();
    assert!(sources.is_empty());
    assert_eq!(diag, ["openapi: ignoring source <inline content>: the spec did not parse to a mapping (got null)"]);
}

#[test]
fn missing_spec_file_names_the_source_and_the_resolved_paths() {
    let dir = tempfile::tempdir().unwrap();
    let err = normalize_source(
        &json!({"title": "Ghost API", "path": "missing/spec.yaml"}),
        dir.path(),
        &mut Vec::new(),
    )
    .unwrap_err();
    let message = err.to_string();
    let resolved = folio_config::canonicalize_lenient(&dir.path().join("missing/spec.yaml"));
    assert_eq!(
            message,
            format!(
                "openapi source 'Ghost API': spec file not found at '{}' (path 'missing/spec.yaml' resolved against project directory '{}')",
                resolved.display(),
                folio_config::canonicalize_lenient(dir.path()).display()
            )
        );
}

#[test]
fn a_spec_that_is_not_a_mapping_warns_and_is_dropped() {
    let dir = tempfile::tempdir().unwrap();
    std::fs::write(dir.path().join("broken.yaml"), "- just\n- a\n- list\n").unwrap();
    let mut diag = Vec::new();
    let result = normalize_source(&json!({"path": "broken.yaml"}), dir.path(), &mut diag).unwrap();
    assert_eq!(result, None);
    assert_eq!(diag, ["openapi: ignoring source 'broken.yaml': the spec did not parse to a mapping (got sequence)"]);
    let mut diag = Vec::new();
    assert_eq!(
        normalize_source(
            &json!({"title": " T ", "content": "just text"}),
            dir.path(),
            &mut diag
        )
        .unwrap(),
        None
    );
    assert_eq!(
        diag,
        ["openapi: ignoring source 'T': the spec did not parse to a mapping (got string)"]
    );
    assert_eq!(
        normalize_source(&json!("junk"), dir.path(), &mut Vec::new()).unwrap(),
        None
    );
    let err = normalize_source(
        &json!({"title": "Bad", "content": "a: [unclosed"}),
        dir.path(),
        &mut Vec::new(),
    )
    .unwrap_err();
    assert!(
        err.to_string().starts_with("openapi source 'Bad': "),
        "{err}"
    );
}

#[test]
fn docs_page_escapes_the_heading_and_the_attribute() {
    let page = docs_page_mdx("Payments <v2> {beta} `raw` & \"quoted\"");
    assert!(page.contains("# Payments \\<v2\\> \\{beta\\} \\`raw\\` & \"quoted\"\n"));
    assert!(page.contains("sourceTitle=\"Payments <v2> {beta} `raw` &amp; &quot;quoted&quot;\""));
    assert_eq!(
        escape_mdx_text("[x](y)\\"),
        "\\[x\\]\\(y\\)\\\\".replace("\\(", "(").replace("\\)", ")")
    );
}

#[test]
fn default_route_uses_the_slug_rules() {
    let route =
        |raw: Option<Value>, title: &str| normalize_route(raw.as_ref(), title, "'T'").unwrap();
    assert_eq!(route(None, "Cookie's API"), "api-reference/cookies-api");
    assert_eq!(route(None, "!!!"), "api-reference/openapi");
    assert_eq!(route(Some(json!("  /custom/route/ ")), "x"), "custom/route");
    assert_eq!(route(Some(json!("   ")), "Title"), "api-reference/title");
    assert_eq!(route(Some(json!(3)), "Title"), "api-reference/title");
    // A configured route is slugged segment by segment; empty segments drop.
    assert_eq!(
        route(Some(json!("API Reference//HTTP v1.2/")), "x"),
        "api-reference/http-v1-2"
    );
    assert_eq!(route(Some(json!("Payments <v2>")), "x"), "payments-v2");
    // A route with nothing left to slug takes the default, never no page.
    assert_eq!(route(Some(json!("/")), "Title"), "api-reference/title");
    assert_eq!(route(Some(json!("***")), "Title"), "api-reference/title");
}

#[test]
fn a_route_that_climbs_out_of_the_docs_fails() {
    for raw in ["../outside", "api/../../etc", "./here", "api\\..\\x"] {
        let err = normalize_route(Some(&json!(raw)), "x", "'Cookie Caper API'").unwrap_err();
        assert_eq!(
            err.to_string(),
            format!("openapi source 'Cookie Caper API': route '{raw}' must not contain '.' or '..' segments")
        );
    }
    let dir = tempfile::tempdir().unwrap();
    let err = normalize_source(
        &json!({"title": "Escape", "content": {"info": {"title": "E"}}, "route": "../../x"}),
        dir.path(),
        &mut Vec::new(),
    )
    .unwrap_err();
    assert!(
        err.to_string()
            .starts_with("openapi source 'Escape': route "),
        "{err}"
    );
}

#[test]
fn a_spec_path_outside_the_project_is_refused() {
    let outer = tempfile::tempdir().unwrap();
    let project = outer.path().join("project");
    std::fs::create_dir(&project).unwrap();
    std::fs::write(outer.path().join("spec.json"), COOKIE_SPEC).unwrap();
    let root = folio_config::canonicalize_lenient(&project);
    let absolute = outer.path().join("spec.json").display().to_string();
    for raw in ["../spec.json", absolute.as_str()] {
        let err = normalize_source(
            &json!({"title": "Outside", "path": raw}),
            &project,
            &mut Vec::new(),
        )
        .unwrap_err();
        assert_eq!(
            err.to_string(),
            format!(
                "openapi source 'Outside': spec path '{raw}' must stay within the project directory '{}'",
                root.display()
            )
        );
    }
    // An absolute path inside the project still loads.
    std::fs::write(project.join("spec.json"), COOKIE_SPEC).unwrap();
    let inside = project.join("spec.json").display().to_string();
    let source = normalize_source(&json!({"path": inside}), &project, &mut Vec::new())
        .unwrap()
        .unwrap();
    assert_eq!(source.title, "Cookie Caper API");
}
