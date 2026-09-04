import pytest

from folio.config import Config, load_config
from folio.extensions import ExtensionRegistry, register_config_components
from folio.generator.extension_emitter import ExtensionEmitter


def test_registry_requires_layout_for_views() -> None:
    registry = ExtensionRegistry()
    registry.register_component("Hero", import_path="@/components/hero")

    try:
        registry.add_view(
            path="/", layout="missing", slots={"main": [{"component": "Hero"}]}
        )
    except ValueError as exc:
        assert "Unknown layout" in str(exc)
    else:
        raise AssertionError("Expected missing layout to fail")


def test_registry_requires_known_components_in_view_slots() -> None:
    registry = ExtensionRegistry()
    registry.register_layout(
        "folio.public",
        import_path="@/components/folio-view-layouts",
        export_name="PublicLayout",
    )

    try:
        registry.add_view(
            path="/custom",
            layout="folio.public",
            slots={"main": [{"component": "Missing"}]},
        )
    except ValueError as exc:
        assert "Unknown component" in str(exc)
    else:
        raise AssertionError("Expected missing component to fail")


def test_registry_rejects_duplicate_view_paths() -> None:
    registry = ExtensionRegistry()
    registry.register_layout(
        "folio.public",
        import_path="@/components/folio-view-layouts",
        export_name="PublicLayout",
    )
    registry.register_component("Hero", import_path="@/components/hero")
    registry.add_view(
        path="/custom",
        layout="folio.public",
        slots={"main": [{"component": "Hero"}]},
    )

    try:
        registry.add_view(
            path="/custom",
            layout="folio.public",
            slots={"main": [{"component": "Hero"}]},
        )
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Expected duplicate view to fail")


def test_register_config_components_exposes_named_files(tmp_path) -> None:
    component = tmp_path / "hero.tsx"
    component.write_text("export function Hero() { return <section /> }\n")
    config = Config(
        project_name="Demo",
        component_specs=[
            {
                "name": "Hero",
                "from": str(component),
                "export": "Hero",
                "expose": {"mdx": True, "landing": True},
            }
        ],
    )
    registry = ExtensionRegistry()

    register_config_components(registry, config)

    hero = registry.components["Hero"]
    assert hero.source_path == component
    assert hero.import_path == "@/components/__folio_components/hero"
    assert hero.expose_mdx is True
    assert not hasattr(hero, "expose_landing")


def test_register_config_components_disambiguates_duplicate_source_stems(
    tmp_path,
) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first_component = first_dir / "widget.tsx"
    second_component = second_dir / "widget.tsx"
    first_component.write_text("export function FirstWidget() { return <section /> }\n")
    second_component.write_text(
        "export function SecondWidget() { return <section /> }\n"
    )
    config = Config(
        project_name="Demo",
        component_specs=[
            {
                "name": "FirstWidget",
                "from": str(first_component),
                "export": "FirstWidget",
            },
            {
                "name": "SecondWidget",
                "from": str(second_component),
                "export": "SecondWidget",
            },
        ],
    )
    registry = ExtensionRegistry()

    register_config_components(registry, config)

    first = registry.components["FirstWidget"]
    second = registry.components["SecondWidget"]
    assert first.import_path == "@/components/__folio_components/widget-FirstWidget"
    assert second.import_path == "@/components/__folio_components/widget-SecondWidget"
    assert first.import_path != second.import_path


def test_register_config_components_expands_directory_entries(tmp_path) -> None:
    components_dir = tmp_path / "docs" / "components"
    components_dir.mkdir(parents=True)
    (components_dir / "hero.tsx").write_text(
        "export function Hero() { return <section /> }\n"
    )
    (components_dir / "my-chart.jsx").write_text(
        "export function MyChart() { return <svg /> }\n"
    )
    (components_dir / "notes.md").write_text("not a component\n")
    config = Config(
        project_name="Demo",
        component_dirs=[str(components_dir)],
        project_dir=str(tmp_path),
    )
    registry = ExtensionRegistry()

    register_config_components(registry, config)

    hero = registry.components["Hero"]
    chart = registry.components["MyChart"]
    assert hero.source_path == components_dir / "hero.tsx"
    assert hero.import_path == "@/components/__folio_components/hero"
    assert hero.origin == "config"
    assert hero.expose_mdx is True
    assert chart.source_path == components_dir / "my-chart.jsx"
    assert chart.export_name == "MyChart"
    # The .md file is not a component and registers nothing.
    assert set(registry.components) == {"Hero", "MyChart"}


def test_register_config_components_anchors_relative_dirs_to_project_dir(
    tmp_path,
) -> None:
    components_dir = tmp_path / "docs" / "components"
    components_dir.mkdir(parents=True)
    (components_dir / "hero.tsx").write_text(
        "export function Hero() { return <section /> }\n"
    )
    config = Config(
        project_name="Demo",
        component_dirs=["docs/components"],
        project_dir=str(tmp_path),
    )
    registry = ExtensionRegistry()

    register_config_components(registry, config)

    assert registry.components["Hero"].source_path == components_dir / "hero.tsx"


def test_register_config_components_missing_directory_fails_loudly(tmp_path) -> None:
    config = Config(
        project_name="Demo",
        component_dirs=[str(tmp_path / "missing")],
        project_dir=str(tmp_path),
    )
    registry = ExtensionRegistry()

    with pytest.raises(ValueError, match="Component directory not found"):
        register_config_components(registry, config)


def test_register_config_components_empty_directory_warns(tmp_path) -> None:
    empty_dir = tmp_path / "docs" / "components"
    empty_dir.mkdir(parents=True)
    config = Config(
        project_name="Demo",
        component_dirs=[str(empty_dir)],
        project_dir=str(tmp_path),
    )
    registry = ExtensionRegistry()

    with pytest.warns(UserWarning, match="no .tsx/.jsx files"):
        register_config_components(registry, config)

    assert registry.components == {}


def test_register_config_components_dedupes_dir_and_spec_stems(tmp_path) -> None:
    components_dir = tmp_path / "dir"
    components_dir.mkdir()
    (components_dir / "widget.tsx").write_text(
        "export function Widget() { return <section /> }\n"
    )
    spec_file = tmp_path / "widget.tsx"
    spec_file.write_text("export function SpecWidget() { return <section /> }\n")
    config = Config(
        project_name="Demo",
        component_dirs=[str(components_dir)],
        component_specs=[{"name": "SpecWidget", "from": str(spec_file)}],
        project_dir=str(tmp_path),
    )
    registry = ExtensionRegistry()

    register_config_components(registry, config)

    dir_widget = registry.components["Widget"]
    spec_widget = registry.components["SpecWidget"]
    assert dir_widget.import_path != spec_widget.import_path
    assert dir_widget.import_path == "@/components/__folio_components/widget-Widget"
    assert (
        spec_widget.import_path == "@/components/__folio_components/widget-SpecWidget"
    )


def test_components_key_flows_from_config_to_registry_and_emitter(tmp_path) -> None:
    """Integration: docs.yaml components: dir -> registry -> workspace copy."""
    components_dir = tmp_path / "docs" / "components"
    components_dir.mkdir(parents=True)
    (components_dir / "hero.tsx").write_text(
        "export function Hero() { return <section /> }\n"
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ComponentProject"

components:
  - "docs/components"
"""
    )

    config = load_config(cfg_file).resolve_paths(tmp_path)
    registry = ExtensionRegistry()
    register_config_components(registry, config)

    hero = registry.components["Hero"]
    assert hero.origin == "config"
    assert hero.import_path == "@/components/__folio_components/hero"

    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    ExtensionEmitter(build_dir, project_dir=config.project_dir).apply(registry)

    copied = build_dir / "components" / "__folio_components" / "hero.tsx"
    assert copied.read_text() == "export function Hero() { return <section /> }\n"


def test_component_definition_has_contract_metadata_defaults() -> None:
    registry = ExtensionRegistry()
    comp = registry.register_component("Foo", import_path="@/components/foo")
    assert comp.props == {}
    assert comp.required is False
    assert comp.category == "general"
    assert comp.contract is False
    assert comp.source_label == ""
    assert comp.origin == "plugin"


def test_register_component_accepts_contract_metadata() -> None:
    registry = ExtensionRegistry()
    comp = registry.register_component(
        "Bar",
        import_path="@/components/bar",
        props={"x": "string"},
        required=True,
        category="api-reference",
        contract=True,
        source_label="api-reference",
    )
    assert comp.props == {"x": "string"}
    assert comp.required is True
    assert comp.category == "api-reference"
    assert comp.contract is True
    assert comp.source_label == "api-reference"


def test_register_component_rejects_unknown_origin() -> None:
    registry = ExtensionRegistry()

    with pytest.raises(ValueError, match="Invalid component origin"):
        registry.register_component(
            "Hero", import_path="@/components/hero", origin="user"
        )


def test_plugin_component_shadows_builtin_with_warning() -> None:
    registry = ExtensionRegistry()
    registry.register_component(
        "Callout", import_path="@/components/callout", origin="builtin"
    )

    with pytest.warns(
        UserWarning, match="Component 'Callout' overrides the Folio builtin"
    ):
        replaced = registry.register_component(
            "Callout", import_path="@/components/my-callout", origin="plugin"
        )

    assert registry.components["Callout"] is replaced
    assert replaced.import_path == "@/components/my-callout"
    assert replaced.origin == "plugin"


def test_non_builtin_duplicate_component_raises_naming_origins() -> None:
    registry = ExtensionRegistry()
    registry.register_component(
        "Hero", import_path="@/components/hero", origin="config"
    )

    with pytest.raises(ValueError) as excinfo:
        registry.register_component(
            "Hero", import_path="@/components/other-hero", origin="plugin"
        )

    message = str(excinfo.value)
    assert "Component already registered: Hero" in message
    assert "existing origin: config" in message
    assert "new origin: plugin" in message


def test_builtin_duplicate_component_still_raises() -> None:
    registry = ExtensionRegistry()
    registry.register_component(
        "Callout", import_path="@/components/callout", origin="builtin"
    )

    with pytest.raises(ValueError) as excinfo:
        registry.register_component(
            "Callout", import_path="@/components/callout", origin="builtin"
        )

    message = str(excinfo.value)
    assert "existing origin: builtin" in message
    assert "new origin: builtin" in message


def test_register_config_components_shadow_builtin_with_config_origin(
    tmp_path,
) -> None:
    component = tmp_path / "callout.tsx"
    component.write_text("export function Callout() { return <aside /> }\n")
    config = Config(
        project_name="Demo",
        component_specs=[
            {"name": "Callout", "from": str(component), "export": "Callout"}
        ],
    )
    registry = ExtensionRegistry()
    registry.register_component(
        "Callout", import_path="@/components/callout", origin="builtin"
    )

    with pytest.warns(
        UserWarning, match="Component 'Callout' overrides the Folio builtin"
    ):
        register_config_components(registry, config)

    callout = registry.components["Callout"]
    assert callout.origin == "config"
    assert callout.source_path == component
