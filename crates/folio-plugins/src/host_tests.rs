use super::*;
use crate::builder::AssetBuilder;
use crate::hook::{ChangeKind, Plugin, PluginDocument};
use crate::registry::{ComponentDefinition, ExtensionRegistry};
use crate::testing::{docs_config, MemoryBuilder};
use folio_config::DocsConfig;
use serde_json::Map;
use std::cell::RefCell;
use std::path::{Path, PathBuf};
use std::rc::Rc;

fn config(dir: &Path) -> DocsConfig {
    docs_config("project: {name: Demo}\n", dir)
}

/// Overrides every hook: the hook list, in call order.
#[derive(Default)]
struct Recorder {
    calls: Rc<RefCell<Vec<String>>>,
}

impl Plugin for Recorder {
    fn name(&self) -> String {
        "recorder".to_string()
    }
    fn config_keys(&self) -> Vec<String> {
        vec!["zeta".to_string(), "alpha".to_string()]
    }
    fn configure(
        &self,
        config: &mut DocsConfig,
        raw: &Map<String, Value>,
        _diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        config
            .extra
            .insert("recorder".into(), Value::Bool(raw.contains_key("project")));
        self.calls.borrow_mut().push("configure".into());
        Ok(())
    }
    fn collect_docs(&self, _config: &DocsConfig) -> Result<Vec<PluginDocument>, PluginError> {
        self.calls.borrow_mut().push("collect_docs".into());
        Ok(vec![])
    }
    fn register_extensions(
        &self,
        registry: &mut ExtensionRegistry,
        _config: &DocsConfig,
        _diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        registry.register_component(
            ComponentDefinition::new("Recorded", "@/components/recorded"),
            &mut Vec::new(),
        )?;
        self.calls.borrow_mut().push("register_extensions".into());
        Ok(())
    }
    fn emit_assets(
        &self,
        builder: &mut dyn AssetBuilder,
        _config: &DocsConfig,
        _diag: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        builder.register_route("recorded");
        self.calls.borrow_mut().push("emit_assets".into());
        Ok(())
    }
    fn watch_paths(&self, config: &DocsConfig) -> Vec<PathBuf> {
        vec![
            config.project_dir.clone(),
            config.project_dir.join("missing"),
        ]
    }
    fn on_watched_change(
        &self,
        _builder: &mut dyn AssetBuilder,
        _config: &DocsConfig,
        path: &Path,
        change: ChangeKind,
        _diag: &mut Diagnostics,
    ) -> Result<bool, PluginError> {
        self.calls
            .borrow_mut()
            .push(format!("change:{}:{change:?}", path.display()));
        Ok(true)
    }
    fn post_build(&self, site_dir: &Path, _diag: &mut Diagnostics) -> Result<(), PluginError> {
        self.calls
            .borrow_mut()
            .push(format!("built:{}", site_dir.display()));
        Ok(())
    }
}

/// Fails in every hook it implements.
struct Boom;

impl Plugin for Boom {
    fn name(&self) -> String {
        "boom-plugin".to_string()
    }
    fn config_keys(&self) -> Vec<String> {
        vec!["alpha".to_string(), "beta".to_string()]
    }
    fn configure(
        &self,
        _: &mut DocsConfig,
        _: &Map<String, Value>,
        _: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        Err("kaboom".into())
    }
    fn collect_docs(&self, _: &DocsConfig) -> Result<Vec<PluginDocument>, PluginError> {
        Err("no docs".into())
    }
    fn register_extensions(
        &self,
        _: &mut ExtensionRegistry,
        _: &DocsConfig,
        _: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        Err("kaboom".into())
    }
    fn emit_assets(
        &self,
        builder: &mut dyn AssetBuilder,
        _: &DocsConfig,
        _: &mut Diagnostics,
    ) -> Result<(), PluginError> {
        builder.register_route("boom-partial");
        builder.write_page("boom-partial", "partial")?;
        Err("nope".into())
    }
    fn on_watched_change(
        &self,
        _: &mut dyn AssetBuilder,
        _: &DocsConfig,
        _: &Path,
        _: ChangeKind,
        _: &mut Diagnostics,
    ) -> Result<bool, PluginError> {
        Err("watch failed".into())
    }
    fn post_build(&self, _: &Path, _: &mut Diagnostics) -> Result<(), PluginError> {
        Err("post failed".into())
    }
}

fn host_of(plugins: Vec<Box<dyn Plugin>>) -> PluginHost {
    let mut host = PluginHost::default();
    for plugin in plugins {
        host.push(plugin);
    }
    host
}

#[test]
fn the_builtin_host_is_landing_roadmap_openapi_in_order() {
    let host = PluginHost::builtin();
    let names: Vec<String> = host.plugins().iter().map(|p| p.name()).collect();
    assert_eq!(names, ["landing", "roadmap", "openapi"]);
    assert_eq!(
        host.config_keys().into_iter().collect::<Vec<_>>(),
        ["landing", "openapi", "roadmap"]
    );
    // Every built-in section key is one the loader already knows.
    for key in host.config_keys() {
        assert!(
            folio_config::BUILTIN_SECTION_KEYS.contains(&key.as_str()),
            "{key}"
        );
    }
}

#[test]
fn a_roadmap_section_activates_through_the_loader_without_warnings() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("docs.yaml");
    std::fs::write(&path, "project:\n  name: DefaultPluginProject\n\nroadmap:\n  phases:\n    - id: foundation\n      version: \"0.1\"\n      title: Foundation\n      status: shipped\n      layer: Core\n      summary: The first release.\n").unwrap();
    let loaded = folio_config::load_docs_config(&path).unwrap();
    assert_eq!(loaded.warnings, Vec::<String>::new());
    let mut config = loaded.config;
    let mut diag = Vec::new();
    PluginHost::builtin()
        .configure(&mut config, &loaded.raw, &mut diag)
        .unwrap();
    assert!(diag.is_empty());
    assert_eq!(
        config.extra["roadmap"]["phases"][0]["id"],
        Value::String("foundation".into())
    );
    assert_eq!(
        config.extra["roadmap"]["routes"],
        serde_json::json!({"docs": true, "public": false})
    );
    // Claimed keys stay inert without their section: nothing is written.
    assert!(!config.extra.contains_key("landing") && !config.extra.contains_key("openapi"));
    assert!(!config.landing_enabled);

    std::fs::write(&path, "project:\n  name: NoRoadmapProject\n").unwrap();
    let loaded = folio_config::load_docs_config(&path).unwrap();
    let mut config = loaded.config;
    PluginHost::builtin()
        .configure(&mut config, &loaded.raw, &mut diag)
        .unwrap();
    assert!(config.extra.is_empty());
    assert!(PluginHost::builtin().config_keys().contains("roadmap"));
}

#[test]
fn config_keys_are_the_sorted_deduplicated_union() {
    let host = host_of(vec![Box::new(Recorder::default()), Box::new(Boom)]);
    assert_eq!(
        host.config_keys().into_iter().collect::<Vec<_>>(),
        ["alpha", "beta", "zeta"]
    );
    assert_eq!(host.plugins().len(), 2);
}

#[test]
fn fail_fast_hooks_wrap_the_first_failure_with_plugin_and_hook() {
    let dir = tempfile::tempdir().unwrap();
    let mut config = config(dir.path());
    let raw =
        serde_json::from_str::<Map<String, Value>>(r#"{"project": {"name": "Demo"}}"#).unwrap();
    let host = host_of(vec![Box::new(Recorder::default()), Box::new(Boom)]);
    let err = host
        .configure(&mut config, &raw, &mut Vec::new())
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Plugin 'boom-plugin' failed in hook 'configure': kaboom"
    );
    assert!(matches!(
        err,
        PluginsError::Hook {
            hook_name: "configure",
            ..
        }
    ));
    // The recorder ran first (host order) and wrote its section.
    assert_eq!(config.extra["recorder"], Value::Bool(true));

    let err = host
        .register_extensions(&mut ExtensionRegistry::default(), &config, &mut Vec::new())
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Plugin 'boom-plugin' failed in hook 'register_extensions': kaboom"
    );
    let err = host.collect_docs(&config).unwrap_err();
    assert_eq!(
        err.to_string(),
        "Plugin 'boom-plugin' failed in hook 'collect_docs': no docs"
    );
}

#[test]
fn warn_skip_hooks_continue_attribute_and_roll_back_routes() {
    let dir = tempfile::tempdir().unwrap();
    let config = config(dir.path());
    let recorder = Recorder::default();
    let calls = Rc::clone(&recorder.calls);
    let host = host_of(vec![Box::new(Boom), Box::new(recorder)]);
    let mut builder = MemoryBuilder::default();
    let mut diag = Vec::new();
    host.emit_assets(&mut builder, &config, &mut diag);
    assert_eq!(
        diag,
        ["Plugin 'boom-plugin' failed in hook 'emit_assets': nope (skipped)"]
    );
    // Boom's route was rolled back, the good plugin's survived; the page stays on disk.
    assert_eq!(
        builder.emitted_routes().into_iter().collect::<Vec<_>>(),
        ["recorded"]
    );
    assert_eq!(builder.read_page("boom-partial").unwrap(), "partial");

    let mut diag = Vec::new();
    host.post_build(Path::new("/tmp/site"), &mut diag);
    assert_eq!(
        diag,
        ["Plugin 'boom-plugin' failed in hook 'post_build': post failed (skipped)"]
    );
    assert_eq!(*calls.borrow(), ["emit_assets", "built:/tmp/site"]);

    let mut diag = Vec::new();
    let handled = host.dispatch_change(
        &mut builder,
        &config,
        Path::new("/x/y.md"),
        ChangeKind::Modified,
        &mut diag,
    );
    assert!(handled);
    assert_eq!(
        diag,
        ["Plugin 'boom-plugin' failed in hook 'on_watched_change': watch failed (skipped)"]
    );
    assert_eq!(calls.borrow().last().unwrap(), "change:/x/y.md:Modified");

    let dirs = host.watch_dirs(&config);
    assert_eq!(dirs, std::slice::from_ref(&config.project_dir));
}

#[test]
fn collected_documents_are_validated_parsed_and_marked() {
    let dir = tempfile::tempdir().unwrap();
    let config = config(dir.path());
    let source = dir.path().join("report.md");
    std::fs::write(&source, "# Quality\n\nAll good.\n").unwrap();
    struct Docs(Vec<PluginDocument>);
    impl Plugin for Docs {
        fn name(&self) -> String {
            "docs".to_string()
        }
        fn collect_docs(&self, _: &DocsConfig) -> Result<Vec<PluginDocument>, PluginError> {
            Ok(self.0.clone())
        }
    }
    let doc = |route: &str, source: &Path| PluginDocument {
        source: source.to_path_buf(),
        route: route.into(),
        unlisted: true,
    };
    let pages = host_of(vec![Box::new(Docs(vec![doc("reports/quality", &source)]))])
        .collect_docs(&config)
        .unwrap();
    assert_eq!(pages.len(), 1);
    assert_eq!(pages[0].route, "reports/quality");
    assert!(pages[0].unlisted);
    assert_eq!(pages[0].content, "# Quality\n\nAll good.");

    for (route, expected) in [
        ("", "Plugin document route must be a clean relative URL: ''"),
        (
            "/abs",
            "Plugin document route must be a clean relative URL: '/abs'",
        ),
        (
            "a\\b",
            "Plugin document route must be a clean relative URL: 'a\\\\b'",
        ),
        (
            "a//b",
            "Plugin document route must be a clean relative URL: 'a//b'",
        ),
        (
            "a/../b",
            "Plugin document route must be a clean relative URL: 'a/../b'",
        ),
        (
            "a/./b",
            "Plugin document route must be a clean relative URL: 'a/./b'",
        ),
    ] {
        let err = host_of(vec![Box::new(Docs(vec![doc(route, &source)]))])
            .collect_docs(&config)
            .unwrap_err();
        assert_eq!(err.to_string(), expected, "{route}");
    }
    let err = host_of(vec![Box::new(Docs(vec![doc(
        "ok",
        &dir.path().join("x.txt"),
    )]))])
    .collect_docs(&config)
    .unwrap_err();
    assert_eq!(
        err.to_string(),
        "PluginDocument.source must be a path ending in .md or .mdx"
    );
    let missing = dir.path().join("gone.MDX");
    let err = host_of(vec![Box::new(Docs(vec![doc("ok", &missing)]))])
        .collect_docs(&config)
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        format!("Plugin document source not found: {}", missing.display())
    );
}

#[test]
fn route_collisions_fail_on_the_canonical_public_route() {
    let page = |route: &str, source: &str| folio_mdx::MarkdownPage {
        content: String::new(),
        frontmatter: Default::default(),
        route: route.to_string(),
        source_file: source.to_string(),
        unlisted: false,
    };
    assert_eq!(canonical_route("guide/index/"), "guide");
    assert_eq!(canonical_route("common_errors"), "common-errors");
    assert_eq!(
        canonical_route("api-reference/pkg_mod/index"),
        "api-reference/pkg_mod"
    );
    check_route_collisions(&[page("guide/a", "/d/a.md"), page("guide/b", "/d/b.md")]).unwrap();
    let err = check_route_collisions(&[
        page("guide/common_errors", "/d/common_errors.md"),
        page("guide/common-errors/index", ""),
    ])
    .unwrap_err();
    assert_eq!(
            err.to_string(),
            "Documentation route collision at public route 'guide/common-errors': 'guide/common_errors' (/d/common_errors.md) and 'guide/common-errors/index' (<generated document>)"
        );
}

#[test]
fn build_registry_assembles_layout_builtins_config_then_plugins() {
    let dir = tempfile::tempdir().unwrap();
    let components_dir = dir.path().join("c");
    std::fs::create_dir_all(&components_dir).unwrap();
    std::fs::write(
        components_dir.join("hero.tsx"),
        "export function Hero() {}\n",
    )
    .unwrap();
    let config = docs_config("project: {name: Demo}\ncomponents:\n  - c\n", dir.path());
    let host = host_of(vec![Box::new(Recorder::default())]);
    let registry = build_registry(&host, &config, &mut Vec::new()).unwrap();
    assert!(registry
        .layouts
        .contains_key(crate::builtins::PUBLIC_LAYOUT));
    let names: Vec<&str> = registry.components.keys().map(String::as_str).collect();
    assert_eq!(names.len(), 42);
    assert_eq!(names[0], "ParamTable");
    assert_eq!(names[40], "Hero");
    assert_eq!(names[41], "Recorded");
    let err = build_registry(&host_of(vec![Box::new(Boom)]), &config, &mut Vec::new()).unwrap_err();
    assert_eq!(
        err.to_string(),
        "Plugin 'boom-plugin' failed in hook 'register_extensions': kaboom"
    );
}
