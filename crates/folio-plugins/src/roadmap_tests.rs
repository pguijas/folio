use super::*;
use crate::builtins::{register_builtin_extensions, PUBLIC_LAYOUT};
use crate::hook::Plugin;
use crate::registry::ExtensionRegistry;
use crate::testing::{docs_config, MemoryBuilder};
use folio_config::DocsConfig;
use serde_json::{json, Map, Value};

fn raw(json: Value) -> Map<String, Value> {
    serde_json::from_value(json).unwrap()
}

fn configured(dir: &std::path::Path, extra: Value) -> DocsConfig {
    let mut config = docs_config("project: {name: RoadmapProject}\n", dir);
    for (key, value) in extra.as_object().unwrap() {
        config.extra.insert(key.clone(), value.clone());
    }
    config
}

fn registered(config: &DocsConfig) -> ExtensionRegistry {
    let mut registry = ExtensionRegistry::default();
    register_builtin_extensions(&mut registry).unwrap();
    RoadmapPlugin
        .register_extensions(&mut registry, config, &mut Vec::new())
        .unwrap();
    registry
}

fn phase(id: &str, version: &str, project: Option<&str>) -> Value {
    let mut entry = json!({"id": id, "version": version, "title": id, "status": "shipped", "layer": "Layer", "summary": "Summary.", "features": ["One"]});
    if let Some(project) = project {
        entry["project"] = json!(project);
    }
    entry
}

fn project_roadmap(dir: &std::path::Path, extra: Value) -> DocsConfig {
    let mut value = json!({"roadmap": {
        "routes": {"public": true},
        "description": "Every project.",
        "projects": {
            "docs": {"slug": "folio-docs", "label": "Folio Docs", "title": "Folio Docs Roadmap", "description": "The site side."},
            "acme": {"slug": "acme-sdk", "label": "Acme SDK"}
        },
        "phases": [phase("foundation", "0.1", Some("docs")), phase("project-os", "0.4", Some("acme")), phase("platform", "0.3", None)]
    }});
    for (key, v) in extra.as_object().unwrap() {
        value[key] = v.clone();
    }
    configured(dir, value)
}

#[test]
fn hooks_are_inert_without_the_config_key() {
    let dir = tempfile::tempdir().unwrap();
    let mut config = docs_config("project: {name: Demo}\n", dir.path());
    let plugin = RoadmapPlugin;
    assert_eq!(plugin.name(), "roadmap");
    assert_eq!(plugin.config_keys(), ["roadmap"]);
    plugin
        .configure(&mut config, &raw(json!({})), &mut Vec::new())
        .unwrap();
    assert!(config.extra.is_empty());
    let mut registry = ExtensionRegistry::default();
    plugin
        .register_extensions(&mut registry, &config, &mut Vec::new())
        .unwrap();
    assert!(
        registry.components.is_empty()
            && registry.data_modules.is_empty()
            && registry.views.is_empty()
    );
    let mut builder = MemoryBuilder::default();
    plugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert!(builder.pages.is_empty() && builder.routes.is_empty());
    assert_eq!(active_roadmap(&config), None);
    assert_eq!(get_phases(&config), Vec::<Value>::new());
}

#[test]
fn configure_writes_the_four_key_normalized_shape() {
    let dir = tempfile::tempdir().unwrap();
    let mut config = docs_config("project: {name: Demo}\n", dir.path());
    RoadmapPlugin
        .configure(
            &mut config,
            &raw(json!({"roadmap": {"phases": []}})),
            &mut Vec::new(),
        )
        .unwrap();
    assert_eq!(
        config.extra["roadmap"],
        json!({"routes": {"docs": true, "public": false}, "phases": [], "description": "", "projects": {}})
    );
    RoadmapPlugin
        .configure(
            &mut config,
            &raw(json!({"roadmap": {"phases": [], "description": "  Page copy.  "}})),
            &mut Vec::new(),
        )
        .unwrap();
    assert_eq!(config.extra["roadmap"]["description"], json!("Page copy."));
}

#[test]
fn normalize_roadmap_coerces_routes_phases_description_and_projects() {
    let empty = serde_json::to_value(empty_roadmap()).unwrap();
    assert_eq!(
        empty,
        json!({"routes": {"docs": true, "public": false}, "phases": [], "description": "", "projects": {}})
    );
    for input in [
        json!("not a mapping"),
        json!(null),
        json!({"description": "Copy."}),
        json!({"phases": "nope"}),
    ] {
        let shape = serde_json::to_value(normalize_roadmap(&input)).unwrap();
        let keys: Vec<&str> = shape
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect();
        assert_eq!(
            keys,
            ["routes", "phases", "description", "projects"],
            "{input}"
        );
        assert!(shape["phases"].is_array());
    }
    let roadmap = normalize_roadmap(&json!({
        "routes": {"docs": "no", "public": 0},
        "phases": [{"id": "x", "features": ["a"]}],
        "description": 42,
        "projects": {"docs": {"slug": "s", "label": " Folio Docs ", "description": ""}, "acme": {"description": "The SDK side."}, "bad": "x", "empty": {}}
    }));
    assert!(roadmap.routes.docs);
    assert!(!roadmap.routes.public);
    assert_eq!(roadmap.phases, vec![json!({"id": "x", "features": ["a"]})]);
    assert_eq!(roadmap.description, "");
    assert_eq!(
        serde_json::to_value(&roadmap.projects).unwrap(),
        json!({"docs": {"label": "Folio Docs"}, "acme": {"description": "The SDK side."}, "empty": {}})
    );
    // `routes` that is not a mapping keeps the defaults; `public: []` is false, `public: "x"` true.
    assert_eq!(
        normalize_roadmap(&json!({"routes": "x"})).routes,
        Routes {
            docs: true,
            public: false
        }
    );
    assert!(
        normalize_roadmap(&json!({"routes": {"public": "x"}}))
            .routes
            .public
    );
    assert!(
        !normalize_roadmap(&json!({"routes": {"public": []}}))
            .routes
            .public
    );
}

#[test]
fn active_roadmap_reads_extra_and_get_phases_tolerates_junk() {
    let dir = tempfile::tempdir().unwrap();
    let config = configured(dir.path(), json!({"roadmap": "nonsense"}));
    assert_eq!(active_roadmap(&config), None);
    assert_eq!(get_phases(&config), Vec::<Value>::new());
    let config = configured(dir.path(), json!({"roadmap": {}}));
    assert_eq!(active_roadmap(&config), Some(empty_roadmap()));
    let config = configured(dir.path(), json!({"roadmap": {"phases": [{"id": "a"}]}}));
    assert_eq!(get_phases(&config), vec![json!({"id": "a"})]);
}

#[test]
fn register_extensions_adds_components_data_module_and_view() {
    let dir = tempfile::tempdir().unwrap();
    let config = project_roadmap(dir.path(), json!({}));
    let registry = registered(&config);
    let roadmap = &registry.components["Roadmap"];
    assert_eq!(roadmap.import_path, "@/components/roadmap");
    assert!(roadmap.expose_mdx && !roadmap.contract);
    assert_eq!(
        roadmap.props.keys().collect::<Vec<_>>(),
        [
            "phases",
            "project",
            "compact",
            "maxPhases",
            "moreLink",
            "title",
            "links"
        ]
    );
    assert_eq!(
        roadmap.props["links"],
        "{ label: string; href: string }[] | undefined"
    );
    let page = &registry.components["RoadmapPage"];
    assert_eq!(page.import_path, "@/components/roadmap-page");
    assert!(!page.expose_mdx);
    assert_eq!(
        page.props["projects"],
        "Record<string, { label?: string; description?: string }> | undefined"
    );
    let data = &registry.data_modules["roadmap"];
    assert_eq!(data.export_name, "roadmapPhases");
    assert_eq!(data.type_source, ROADMAP_TYPES);
    assert!(ROADMAP_TYPES.ends_with("}\n"));
    assert_eq!(data.type_annotation, "RoadmapPhase[]");
    assert_eq!(data.module_path, "roadmap-data");
    assert_eq!(data.data.as_array().unwrap().len(), 3);
    assert_eq!(data.data[0]["project"], json!("docs"));

    // The project labels travel on their own for a card drawn outside the view.
    let projects = &registry.data_modules["roadmap-projects"];
    assert_eq!(projects.export_name, "roadmapProjects");
    assert_eq!(projects.module_path, "roadmap-projects");
    assert_eq!(projects.type_source, ROADMAP_PROJECTS_TYPES);
    assert_eq!(projects.type_annotation, "Record<string, RoadmapProject>");
    assert_eq!(
        projects.data,
        json!({"docs": {"label": "Folio Docs", "description": "The site side."}, "acme": {"label": "Acme SDK"}})
    );

    // One /roadmap view that draws its own header: `dense`, title "Roadmap".
    assert_eq!(registry.views.keys().collect::<Vec<_>>(), ["/roadmap"]);
    let view = &registry.views["/roadmap"];
    assert_eq!(view.layout, PUBLIC_LAYOUT);
    assert_eq!(view.title, "Roadmap");
    assert_eq!(
        serde_json::to_value(&view.props).unwrap(),
        json!({"dense": true})
    );
    let block = &view.slots["main"][0];
    assert_eq!(block.component, "RoadmapPage");
    assert_eq!(
        serde_json::to_value(&block.props).unwrap(),
        json!({
            "title": "RoadmapProject Roadmap",
            "description": "Every project.",
            "projects": {"docs": {"label": "Folio Docs", "description": "The site side."}, "acme": {"label": "Acme SDK"}}
        })
    );
}

#[test]
fn the_public_view_is_registered_only_when_routes_public() {
    let dir = tempfile::tempdir().unwrap();
    let config = configured(
        dir.path(),
        json!({"roadmap": {"phases": [], "routes": {"public": false}}}),
    );
    let registry = registered(&config);
    assert!(registry.views.is_empty());
    assert!(registry.components.contains_key("Roadmap"));
    assert_eq!(registry.data_modules["roadmap"].data, json!([]));
    assert_eq!(registry.data_modules["roadmap-projects"].data, json!({}));
    // No description, no projects: only the title travels.
    let config = configured(
        dir.path(),
        json!({"roadmap": {"phases": [], "routes": {"public": true}}}),
    );
    let registry = registered(&config);
    assert_eq!(
        serde_json::to_value(&registry.views["/roadmap"].slots["main"][0].props).unwrap(),
        json!({"title": "RoadmapProject Roadmap"})
    );
}

#[test]
fn a_phases_shape_the_renderer_cannot_read_fails_configure() {
    let dir = tempfile::tempdir().unwrap();
    let with = |key: &str, value: Value| {
        let mut entry = phase("a", "0.1", None);
        entry[key] = value;
        json!({ "phases": [entry] })
    };
    let without = |key: &str| {
        let mut entry = phase("a", "0.1", None);
        entry.as_object_mut().unwrap().remove(key);
        json!({ "phases": [entry] })
    };
    let listed =
        "a phase takes id, version, project, title, status, layer, summary, command and features";
    for (section, message) in [
        (
            json!({"phases": "nope"}),
            "roadmap.phases must be a list of phases (got string)".to_string(),
        ),
        (
            json!({"phases": {"id": "x"}}),
            "roadmap.phases must be a list of phases (got mapping)".to_string(),
        ),
        (
            json!({"phases": [phase("a", "0.1", None), "junk"]}),
            "roadmap.phases[1] must be a mapping with id, version, title, status, layer and summary (got string)".to_string(),
        ),
        (
            with("features", json!("one line")),
            "roadmap.phases[0].features must be a list (got string)".to_string(),
        ),
        // A key `RoadmapPhase` does not declare, `milestone` among them.
        (
            with("milestone", json!("M1")),
            format!("roadmap.phases[0].milestone is not a phase key; {listed}"),
        ),
        (
            with("sumary", json!("Typo.")),
            format!("roadmap.phases[0].sumary is not a phase key (did you mean 'summary'?); {listed}"),
        ),
        (
            without("layer"),
            "roadmap.phases[0].layer is missing; every phase needs id, version, title, status, layer and summary".to_string(),
        ),
        (
            with("version", json!(0.3)),
            "roadmap.phases[0].version must be a quoted string, such as \"0.1\" (got number)".to_string(),
        ),
        (
            with("title", json!(null)),
            "roadmap.phases[0].title must be a string (got null)".to_string(),
        ),
        (
            with("command", json!(["folio", "build"])),
            "roadmap.phases[0].command must be a string (got sequence)".to_string(),
        ),
        (
            with("status", json!("planned")),
            "roadmap.phases[0].status must be one of 'shipped', 'active', 'next', 'later'; got 'planned'".to_string(),
        ),
        (
            with("status", json!("activ")),
            "roadmap.phases[0].status must be one of 'shipped', 'active', 'next', 'later'; got 'activ' (did you mean 'active'?)".to_string(),
        ),
        (
            with("features", json!(["One", 2])),
            "roadmap.phases[0].features[1] must be a string or a mapping with text (got number)".to_string(),
        ),
        (
            with("features", json!([{"done": true}])),
            "roadmap.phases[0].features[0].text is missing; a feature mapping needs its text".to_string(),
        ),
        (
            with("features", json!([{"text": "One", "done": "yes"}])),
            "roadmap.phases[0].features[0].done must be true or false (got string)".to_string(),
        ),
        (
            with("features", json!([{"text": "One", "don": true}])),
            "roadmap.phases[0].features[0].don is not a feature key (did you mean 'done'?); a feature takes text and done".to_string(),
        ),
    ] {
        let mut config = docs_config("project: {name: Demo}\n", dir.path());
        let err = RoadmapPlugin
            .configure(
                &mut config,
                &raw(json!({ "roadmap": section })),
                &mut Vec::new(),
            )
            .unwrap_err();
        assert_eq!(err.to_string(), message);
        assert!(config.extra.is_empty());
    }
    // Absent, empty and null `phases`, a phase without `features` or with a
    // null one, and the optional `project` and `command`, are fine.
    let mut bare = phase("a", "0.1", None);
    bare.as_object_mut().unwrap().remove("features");
    let mut full = phase("b", "0.2", Some("docs"));
    full["command"] = json!("folio build");
    full["features"] = json!(["One", {"text": "Two"}, {"text": "Three", "done": false}]);
    for section in [
        json!({}),
        json!({"phases": null}),
        json!({"phases": []}),
        json!({"phases": [bare, with("features", json!(null))["phases"][0].clone(), full]}),
    ] {
        assert!(check_phases(&section).is_ok(), "{section}");
    }
    assert!(check_phases(&json!("not a mapping")).is_ok());
}

#[test]
fn the_phase_check_follows_the_declared_types() {
    let interface = ROADMAP_TYPES
        .split("export interface RoadmapPhase {\n")
        .nth(1)
        .unwrap();
    let fields: Vec<&str> = interface
        .lines()
        .take_while(|line| *line != "}")
        .map(str::trim)
        .collect();
    let name = |field: &&str| field.split(['?', ':']).next().unwrap().to_string();
    assert_eq!(fields.iter().map(name).collect::<Vec<_>>(), PHASE_KEYS);
    assert_eq!(
        fields
            .iter()
            .filter(|field| !field.contains("?:") && !field.starts_with("features"))
            .map(name)
            .collect::<Vec<_>>(),
        REQUIRED_PHASE_KEYS
    );
    let statuses = PHASE_STATUSES.map(|status| format!("\"{status}\""));
    assert!(ROADMAP_TYPES.contains(&format!("RoadmapStatus = {}\n", statuses.join(" | "))));
    assert!(ROADMAP_TYPES.contains("{ text: string; done?: boolean }"));
    assert_eq!(FEATURE_KEYS, ["text", "done"]);
}

#[test]
fn the_data_module_gives_every_phase_a_features_list() {
    let dir = tempfile::tempdir().unwrap();
    let config = configured(
        dir.path(),
        json!({"roadmap": {"phases": [{"id": "a"}, {"id": "b", "features": null}, {"id": "c", "features": ["x"]}]}}),
    );
    // The config keeps what was written; only the rendered data is filled in.
    assert_eq!(get_phases(&config)[0], json!({"id": "a"}));
    assert_eq!(
        registered(&config).data_modules["roadmap"].data,
        json!([{"id": "a", "features": []}, {"id": "b", "features": []}, {"id": "c", "features": ["x"]}])
    );
}

#[test]
fn project_ordering_and_block() {
    let phases = vec![
        json!({"id": "a", "project": " docs "}),
        json!({"id": "b"}),
        json!({"id": "c", "project": "acme"}),
        json!({"id": "d", "project": "docs"}),
        json!("junk"),
    ];
    assert_eq!(project_keys(&phases), ["docs", "shared", "acme"]);
    let roadmap = normalize_roadmap(&json!({
        "projects": {"acme": {"description": "The SDK side."}, "docs": {"label": "Folio Docs"}, "unused": {"label": "No phases"}},
        "phases": [{"id": "docs-0.1", "project": "docs", "version": "0.1"}, {"id": "acme-0.1", "project": "acme", "version": "0.1"}, {"id": "x"}]
    }));
    assert_eq!(
        ordered_project_keys(&roadmap.phases, &roadmap.projects),
        ["acme", "docs", "shared"]
    );
    let block = project_block(&roadmap);
    assert_eq!(
        serde_json::to_value(&block).unwrap(),
        json!({"acme": {"description": "The SDK side."}, "docs": {"label": "Folio Docs"}})
    );
    assert_eq!(block.keys().collect::<Vec<_>>(), ["acme", "docs"]);
}

#[test]
fn emit_assets_writes_the_docs_page_once_and_always_registers_the_route() {
    let dir = tempfile::tempdir().unwrap();
    let config = configured(dir.path(), json!({"roadmap": {"phases": []}}));
    let mut builder = MemoryBuilder::default();
    RoadmapPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert_eq!(builder.routes.iter().collect::<Vec<_>>(), ["roadmap"]);
    assert_eq!(builder.pages["roadmap"], docs_page_mdx());
    assert_eq!(
        docs_page_mdx(),
        "import { Roadmap } from \"@/components/roadmap\"\n\n# Roadmap\n\n<Roadmap />\n"
    );
    // An authored page wins and is never rewritten.
    let mut builder = MemoryBuilder::with_pages([("roadmap", "# Mine\n")]);
    RoadmapPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert_eq!(builder.pages["roadmap"], "# Mine\n");
    assert!(builder.written_pages.is_empty());
    assert!(builder.routes.contains("roadmap"));
    // routes.docs off: nothing.
    let config = configured(
        dir.path(),
        json!({"roadmap": {"phases": [], "routes": {"docs": false}}}),
    );
    let mut builder = MemoryBuilder::default();
    RoadmapPlugin
        .emit_assets(&mut builder, &config, &mut Vec::new())
        .unwrap();
    assert!(builder.routes.is_empty() && builder.pages.is_empty());
}

#[test]
fn table_rows_are_five_strings_per_phase() {
    let phases = vec![
        json!({"id": "foundation", "project": "docs", "status": "shipped", "version": "0.1", "title": "Foundation", "command": "folio build"}),
        json!({"id": "bare", "version": 0.2, "title": "Bare"}),
        json!("junk"),
    ];
    assert_eq!(
        table_rows(&phases),
        [
            ["docs", "shipped", "0.1", "Foundation", "folio build"].map(String::from),
            ["", "", "0.2", "Bare", ""].map(String::from),
            ["", "", "", "", ""].map(String::from),
        ]
    );
}
