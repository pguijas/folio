use super::*;

fn config(yaml: &str) -> DocsConfig {
    let mapping: serde_yaml_ng::Mapping = serde_yaml_ng::from_str(yaml).unwrap();
    folio_config::parse_docs_config_with(&mapping, Path::new("/proj"), "", &mut Vec::new()).unwrap()
}

fn env<'a>(pairs: &'a [(&'a str, &'a str)]) -> impl Fn(&str) -> Option<String> + 'a {
    move |key| {
        pairs
            .iter()
            .find(|(k, _)| *k == key)
            .map(|(_, v)| v.to_string())
    }
}

#[test]
fn base_path_priority_and_github_pages_inference() {
    let site_url = config("project:\n  name: T\n  url: https://example.com/docs/v1/\n");
    assert_eq!(resolve_base_path(&site_url, &env(&[])), "");
    let deploy = config("project:\n  name: T\n  url: https://example.com/docs/v1/\ndeploy:\n  base_path: /published/docs\n");
    assert_eq!(resolve_base_path(&deploy, &env(&[])), "/published/docs");
    let configured = config("project:\n  name: T\ndeploy:\n  base_path: /configured\n");
    assert_eq!(
        resolve_base_path(&configured, &env(&[("FOLIO_BASE_PATH", "env-prefix")])),
        "/env-prefix"
    );
    assert_eq!(
        resolve_base_path(&configured, &env(&[("FOLIO_BASE_PATH", "")])),
        ""
    );
    let pages = config("project:\n  name: T\ndeploy:\n  provider: github-pages\n");
    let actions = [
        ("GITHUB_ACTIONS", "true"),
        ("GITHUB_REPOSITORY", "octocat/project-docs"),
    ];
    assert_eq!(resolve_base_path(&pages, &env(&actions)), "/project-docs");
    assert_eq!(
        resolve_base_path(
            &pages,
            &env(&[
                ("GITHUB_ACTIONS", "true"),
                ("GITHUB_REPOSITORY", "octocat/octocat.github.io")
            ])
        ),
        ""
    );
    assert_eq!(
        resolve_base_path(
            &pages,
            &env(&[("GITHUB_REPOSITORY", "octocat/project-docs")])
        ),
        ""
    );
    let plain = config("project:\n  name: T\n");
    assert_eq!(
        resolve_base_path(
            &plain,
            &env(&[
                ("FOLIO_DEPLOY_PROVIDER", "GitHub-Pages"),
                ("GITHUB_ACTIONS", "TRUE"),
                ("GITHUB_REPOSITORY", "o/r")
            ])
        ),
        "/r"
    );
    assert_eq!(
        resolve_base_path(
            &plain,
            &env(&[
                ("FOLIO_DEPLOY_PROVIDER", "github-pages"),
                ("GITHUB_ACTIONS", "true"),
                ("GITHUB_REPOSITORY", "nope")
            ])
        ),
        ""
    );
    assert_eq!(normalize_base_path(" /a/b/ "), "/a/b");
    assert_eq!(normalize_base_path("/"), "");
}

#[test]
fn root_ownership_check_survives_garbage_and_spelling() {
    let mut base = config("project:\n  name: X\n");
    assert!(!plugin_view_owns_root(&base));
    for (section, expected) in [
        (serde_json::json!("not a dict"), false),
        (serde_json::json!({"routes": true}), false),
        (serde_json::json!({"routes": {"public": true}}), false),
        (serde_json::json!({"routes": {"public": ""}}), false),
        (serde_json::json!({"routes": {"public": "/gallery"}}), false),
        (serde_json::json!({"routes": {"public": "/"}}), true),
        (serde_json::json!({"routes": {"public": " / "}}), true),
    ] {
        base.extra.insert("surface".to_string(), section.clone());
        assert_eq!(plugin_view_owns_root(&base), expected, "{section}");
    }
}

#[test]
fn markers_are_escaped_for_where_they_land() {
    let hostile = r#"A "q" {b} <c> \ `t` ${x}"#;
    let json = r#""A \"q\" {b} <c> \\ `t` ${x}""#;
    // A whole string literal becomes a JSON string.
    assert_eq!(
        substitute(r#"const n = "__N__""#, "__N__", hostile),
        format!("const n = {json}")
    );
    assert_eq!(
        substitute("const n = '__N__'", "__N__", hostile),
        format!("const n = {json}")
    );
    // A whole attribute value becomes a JSX expression.
    assert_eq!(
        substitute(r#"<a href="__N__">"#, "__N__", hostile),
        format!("<a href={{{json}}}>")
    );
    // Part of a JS string takes JSON escapes; part of an attribute, entities.
    assert_eq!(
        substitute(r#"alt: "__N__ docs","#, "__N__", hostile),
        r#"alt: "A \"q\" {b} <c> \\ `t` ${x} docs","#
    );
    assert_eq!(
        substitute(r#"<img alt="__N__ docs" />"#, "__N__", hostile),
        r#"<img alt="A &quot;q&quot; {b} &lt;c&gt; \ `t` ${x} docs" />"#
    );
    // Inside a template literal.
    assert_eq!(
        substitute("`${a}/__N__/`", "__N__", hostile),
        r#"`${a}/A "q" {b} <c> \\ \`t\` \${x}/`"#
    );
    // JSX text, several times, after a string that holds a quote.
    assert_eq!(
        substitute(
            "<span title=\"say \\\"hi\\\"\">\n  __N__ and __N__\n</span>",
            "__N__",
            hostile
        ),
        format!("<span title=\"say \\\"hi\\\"\">\n  {{{json}}} and {{{json}}}\n</span>")
    );
    assert_eq!(substitute("no marker", "__N__", hostile), "no marker");
}
