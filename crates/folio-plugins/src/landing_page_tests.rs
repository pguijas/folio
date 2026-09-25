use super::*;
use crate::landing::normalize_landing;
use crate::testing::docs_config;

#[test]
fn page_data_derives_defaults_without_python_copy() {
    let dir = tempfile::tempdir().unwrap();
    let config = docs_config(
        "project: {name: \"My Lib\", repo: \"https://github.com/me/lib\"}\nlanding: true\n",
        dir.path(),
    );
    let landing = normalize_landing(&json!(true), &mut Vec::new());
    let page = LandingPageData::derive(&landing, &config);
    assert_eq!(page.name, "My Lib");
    assert_eq!(page.monogram, "my");
    assert_eq!(page.tagline, "");
    assert_eq!(page.headline, json!("Documentation for My Lib"));
    assert_eq!(
        page.description,
        json!("Beautiful, modern docs. Zero configuration.")
    );
    assert_eq!(page.cta_primary_text, json!("Get Started"));
    assert_eq!(page.cta_primary_link, json!("/docs"));
    assert_eq!(page.cta_secondary_text, json!("GitHub"));
    assert_eq!(
        page.cta_secondary_link,
        Some("https://github.com/me/lib".to_string())
    );
    // An omitted install emits no install block; no default names pip.
    assert_eq!(page.install_commands, json!([]));
    assert_eq!(page.features.as_array().unwrap().len(), 6);
    let copy = serde_json::to_string(&page.features).unwrap();
    assert!(
        !copy.contains("Python") && !copy.contains("pip") && !copy.contains("conf.py"),
        "{copy}"
    );
    assert_eq!(page.features[0]["title"], json!("Automatic API Reference"));
    assert_eq!(page.features[0]["wide"], json!(true));
    let types: Vec<&str> = page
        .sections
        .iter()
        .map(|s| s["type"].as_str().unwrap())
        .collect();
    assert_eq!(types, ["features", "routes", "output", "cta"]);
    assert_eq!(page.hero_variant, "docs-map");
}

#[test]
fn page_data_keeps_configured_values_and_the_docs_route_base() {
    let dir = tempfile::tempdir().unwrap();
    let config = docs_config("project: {name: Demo, repo: \"https://github.com/me/demo\"}\ntemplate: {docs_route_base: /handbook}\nlanding: true\n", dir.path());
    let landing = normalize_landing(
        &json!({"hero": {"variant": "source-pipeline", "tagline": ""}, "cta": {"secondary": {"text": "Source", "link": "https://x.y"}}, "install": ["folio init"], "comparison": {"caption": "C", "tools": ["A", "B"], "rows": [{"feature": "F", "values": [true, "~"]}]}}),
        &mut Vec::new(),
    );
    let page = LandingPageData::derive(&landing, &config);
    assert_eq!(page.tagline, "");
    assert_eq!(page.cta_primary_link, json!("/handbook"));
    assert_eq!(page.cta_secondary_text, json!("Source"));
    assert_eq!(page.cta_secondary_link, Some("https://x.y".to_string()));
    assert_eq!(page.install_commands, json!(["folio init"]));
    let types: Vec<&str> = page
        .sections
        .iter()
        .map(|s| s["type"].as_str().unwrap())
        .collect();
    assert_eq!(types, ["features", "comparison", "output", "cta"]);
    assert_eq!(page.sections[1]["tools"], json!(["A", "B"]));
    assert_eq!(page.sections[1]["caption"], json!("C"));
    // The legacy `true` yields a bare comparison section; `false` yields none.
    let legacy = normalize_landing(
        &json!({"hero": {"variant": "source-pipeline"}, "comparison": true}),
        &mut Vec::new(),
    );
    let page = LandingPageData::derive(&legacy, &config);
    assert_eq!(
        page.sections[1],
        json!({"type": "comparison"}).as_object().unwrap().clone()
    );
    let off = normalize_landing(
        &json!({"hero": {"variant": "source-pipeline"}, "comparison": false}),
        &mut Vec::new(),
    );
    let types: Vec<String> = LandingPageData::derive(&off, &config)
        .sections
        .iter()
        .map(|s| s["type"].as_str().unwrap().to_string())
        .collect();
    assert_eq!(types, ["features", "output", "cta"]);
    // Configured sections replace the defaults; a project without a repo has no secondary CTA.
    let configured = normalize_landing(&json!({"sections": [{"type": "stats"}]}), &mut Vec::new());
    let bare = docs_config("project: {name: Demo}\nlanding: true\n", dir.path());
    let page = LandingPageData::derive(&configured, &bare);
    assert_eq!(page.sections.len(), 1);
    assert_eq!(page.cta_secondary_link, None);
    assert_eq!(page.cta_secondary_text, json!(""));
}
