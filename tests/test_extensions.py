from folio.config import Config
from folio.extensions import ExtensionRegistry, register_config_components


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
