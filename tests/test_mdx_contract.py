import ast
import json
import os
from pathlib import Path

from folio import __version__
from folio.builtins import BUILTIN_COMPONENTS
from folio.config import Config
from folio.extensions import ComponentDefinition, ExtensionRegistry
from folio.generator.mdx_contract import (
    AUTHORING_CONTRACT_INSTRUCTIONS,
    CORE_CONFIG_KEYS,
    FOLIO_AUTHORING_CONTRACT_PATH,
    FOLIO_MDX_COMPONENTS,
    FOLIO_MDX_CONTRACT_VERSION,
    build_authoring_contract,
    build_contract,
    render_authoring_contract,
    required_component_names,
    render_mdx_contract_module,
    strip_js_comments,
    validate_template_mdx_contract,
)
from folio.generator.site_builder import SiteBuilder


ROOT = Path(__file__).parents[1]
BASELINE_PATH = ROOT / "tests" / "fixtures" / "mdx_contract_baseline.json"


def test_mdx_contract_is_versioned_and_documents_required_props() -> None:
    assert FOLIO_MDX_CONTRACT_VERSION == "1.0"

    components = {component["name"]: component for component in FOLIO_MDX_COMPONENTS}

    assert components["ParamTable"]["props"] == {
        "args": "Array<{ name: string; type: string; default?: string; description?: string | null; href?: string }>"
    }
    assert components["ClassOverview"]["props"] == {
        "name": "string",
        "bases": "string[] | Array<{ name: string; href?: string }>",
        "decorators": "string[]",
        "description": "string",
    }
    assert components["ApiReferenceIndex"]["props"] == {
        "modules": "Array<{ name: string; classes: number; functions: number; path: string }>"
    }
    assert components["Callout"]["props"]["type"] == (
        '"note" | "warning" | "info" | "tip" | "check" | "danger"'
    )
    assert components["Tabs"]["props"] == {
        "defaultValue": "string",
        "children": "React.ReactNode",
    }
    assert components["TabItem"]["props"] == {
        "label": "string",
        "value": "string",
        "children": "React.ReactNode",
    }
    assert components["Mermaid"]["props"] == {"chart": "string"}


def test_rendered_mdx_contract_module_is_importable_typescript() -> None:
    module = render_mdx_contract_module()

    assert 'export const folioMdxContractVersion = "1.0" as const' in module
    assert "export const folioMdxComponents = [" in module
    assert '"name": "ParamTable"' in module
    assert "export type FolioMdxComponentName" in module


def _definition(name: str, **overrides) -> ComponentDefinition:
    return ComponentDefinition(
        name=name, import_path=f"@/components/{name.lower()}", **overrides
    )


def test_build_contract_membership_follows_contract_flag() -> None:
    included = _definition(
        "GlossaryList",
        props={"items": "string[]"},
        contract=True,
        source_label="plugin:glossary",
    )
    excluded = _definition("Internal", props={"value": "string"}, contract=False)
    propless = _definition(
        "GlossaryBadge", contract=True, source_label="plugin:glossary"
    )

    contract = build_contract([included, excluded, propless])

    assert [component["name"] for component in contract] == [
        "GlossaryList",
        "GlossaryBadge",
    ]
    assert contract[0]["source"] == "plugin:glossary"
    assert contract[0]["props"] == {"items": "string[]"}


def test_build_contract_source_comes_from_source_label_not_category() -> None:
    component = _definition(
        "GlossaryList",
        contract=True,
        source_label="plugin:glossary",
        category="component-catalog",
    )

    contract = build_contract([component])

    assert contract == [
        {
            "name": "GlossaryList",
            "required": False,
            "source": "plugin:glossary",
            "props": {},
        }
    ]


def test_rendered_contract_module_can_include_registry_components() -> None:
    plugin_component = _definition(
        "GlossaryList",
        props={"items": "string[]"},
        contract=True,
        source_label="plugin:glossary",
    )

    module = render_mdx_contract_module(list(BUILTIN_COMPONENTS) + [plugin_component])

    assert '"name": "GlossaryList"' in module
    assert '"source": "plugin:glossary"' in module


def _write_mdx_components(tmp_path: Path, body: str) -> Path:
    (tmp_path / "mdx-components.tsx").write_text(body, encoding="utf-8")
    return tmp_path


def test_component_only_in_comment_is_reported_missing(tmp_path: Path) -> None:
    names = required_component_names()
    present = "\n".join(f"  {name}," for name in names if name != "ParamTable")
    body = (
        "export const components = {\n"
        f"{present}\n"
        "  // ParamTable, (temporarily disabled)\n"
        "}\n"
    )
    _write_mdx_components(tmp_path, body)

    missing = validate_template_mdx_contract(tmp_path)

    assert missing == ["ParamTable"]


def test_slashes_inside_string_literal_are_not_treated_as_comment(
    tmp_path: Path,
) -> None:
    names = required_component_names()
    entries = " ".join(f"{name}," for name in names)
    body = (
        'const DOCS = "https://example.com"; '
        f"export const components = {{ {entries} }}\n"
    )
    _write_mdx_components(tmp_path, body)

    missing = validate_template_mdx_contract(tmp_path)

    assert missing == []


def test_strip_js_comments_preserves_strings_and_drops_comments() -> None:
    code = (
        'const url = "https://example.com" // trailing comment\n'
        "/* block\ncomment */const other = 'a//b'\n"
    )

    stripped = strip_js_comments(code)

    assert '"https://example.com"' in stripped
    assert "'a//b'" in stripped
    assert "trailing comment" not in stripped
    assert "block" not in stripped


def test_import_only_component_is_reported_missing(tmp_path: Path) -> None:
    names = required_component_names()
    present = "\n".join(f"  {name}," for name in names if name != "ParamTable")
    body = (
        'import { ParamTable } from "@/components/param-table"\n'
        "export const components = {\n"
        f"{present}\n"
        "}\n"
    )
    _write_mdx_components(tmp_path, body)

    missing = validate_template_mdx_contract(tmp_path)

    assert missing == ["ParamTable"]


def test_as_name_reexport_is_not_reported_missing(tmp_path: Path) -> None:
    names = required_component_names()
    present = "\n".join(f"  {name}," for name in names if name != "ParamTable")
    body = (
        "export { Foo as ParamTable } from './foo'\n"
        "export const components = {\n"
        f"{present}\n"
        "}\n"
    )
    _write_mdx_components(tmp_path, body)

    missing = validate_template_mdx_contract(tmp_path)

    assert missing == []


def test_object_property_form_still_passes(tmp_path: Path) -> None:
    names = required_component_names()
    present = "\n".join(f"  {name}," for name in names)
    body = f"export const components = {{\n{present}\n}}\n"
    _write_mdx_components(tmp_path, body)

    missing = validate_template_mdx_contract(tmp_path)

    assert missing == []


def test_bundled_template_satisfies_required_mdx_contract() -> None:
    missing = validate_template_mdx_contract(ROOT / "template")

    assert missing == []
    mdx_components = (ROOT / "template" / "mdx-components.tsx").read_text(
        encoding="utf-8"
    )
    for name in required_component_names():
        assert f"    {name}," in mdx_components


def _derived_baseline_text() -> str:
    payload = {component["name"]: component for component in FOLIO_MDX_COMPONENTS}
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def test_contract_matches_regenerated_baseline_fixture() -> None:
    """The committed fixture is regenerated from the manifest-derived
    contract, so it can never drift into another hand-maintained copy of the
    prop data. After an intentional manifest change, regenerate it with:

        FOLIO_REGEN_FIXTURES=1 uv run pytest tests/test_mdx_contract.py -q
    """
    expected = _derived_baseline_text()
    if os.environ.get("FOLIO_REGEN_FIXTURES") == "1":
        BASELINE_PATH.write_text(expected, encoding="utf-8")
    assert BASELINE_PATH.read_text(encoding="utf-8") == expected, (
        "tests/fixtures/mdx_contract_baseline.json is stale; regenerate with "
        "FOLIO_REGEN_FIXTURES=1 uv run pytest tests/test_mdx_contract.py -q"
    )


def test_contract_is_derived_from_builtin_manifest() -> None:
    """Semantic equivalence: the contract subset is exactly the manifest
    components flagged ``contract=True``, carrying the manifest's own
    props/required/source_label values."""
    expected = [component for component in BUILTIN_COMPONENTS if component.contract]
    assert [entry["name"] for entry in FOLIO_MDX_COMPONENTS] == [
        component.name for component in expected
    ]
    by_name = {component.name: component for component in expected}
    for entry in FOLIO_MDX_COMPONENTS:
        component = by_name[str(entry["name"])]
        assert entry["props"] == dict(component.props)
        assert entry["required"] is component.required
        assert entry["source"] == component.source_label


def _config_core_key_literal() -> set[str]:
    """Read the loader's core config-key set literal out of folio/config.py.

    ``CORE_CONFIG_KEYS`` mirrors a set literal that lives inside
    :mod:`folio.config`; this reads the literal back so the mirror cannot drift
    silently. It accepts either shape the literal can take: a module-level
    ``CORE_CONFIG_KEYS`` assignment or the ``known_keys`` expression inside
    ``load_config_with_plugins``.
    """
    tree = ast.parse((ROOT / "folio" / "config.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = {target.id for target in node.targets if isinstance(target, ast.Name)}
        if not names & {"CORE_CONFIG_KEYS", "known_keys"}:
            continue
        for candidate in ast.walk(node.value):
            if isinstance(candidate, ast.Set):
                return {
                    element.value
                    for element in candidate.elts
                    if isinstance(element, ast.Constant)
                }
    raise AssertionError("No core config-key set literal found in folio/config.py")


def test_core_config_keys_mirror_the_config_loader() -> None:
    assert set(CORE_CONFIG_KEYS) == _config_core_key_literal()


def test_authoring_contract_envelope_carries_versions_and_one_instruction() -> None:
    contract = build_authoring_contract(
        folio_version="9.9.9",
        generated_at="2026-07-28T09:12:04Z",
    )

    assert contract["folioVersion"] == "9.9.9"
    assert contract["mdxContractVersion"] == FOLIO_MDX_CONTRACT_VERSION
    assert contract["generatedAt"] == "2026-07-28T09:12:04Z"
    assert contract["instructions"] == AUTHORING_CONTRACT_INSTRUCTIONS
    assert "Ignore fields you do not recognise" in contract["instructions"]
    # No components passed: the builtin manifest is the fallback.
    assert contract["components"] == FOLIO_MDX_COMPONENTS


def test_authoring_contract_sorts_and_deduplicates_keys_and_routes() -> None:
    contract = build_authoring_contract(
        folio_version=__version__,
        generated_at="2026-07-28T09:12:04Z",
        config_keys=["roadmap", "project", "roadmap"],
        routes=["/docs/guide/", "/docs/", "/docs/guide/"],
    )

    assert contract["configKeys"] == ["project", "roadmap"]
    assert contract["routes"] == ["/docs/", "/docs/guide/"]


def test_authoring_contract_describes_plugin_contract_components() -> None:
    plugin_component = _definition(
        "GlossaryList",
        props={"items": "string[]"},
        contract=True,
        source_label="plugin:glossary",
    )

    contract = build_authoring_contract(
        folio_version=__version__,
        generated_at="2026-07-28T09:12:04Z",
        components=list(BUILTIN_COMPONENTS) + [plugin_component],
    )

    assert {
        "name": "GlossaryList",
        "required": False,
        "source": "plugin:glossary",
        "props": {"items": "string[]"},
    } in contract["components"]


def test_rendered_authoring_contract_is_json_with_a_trailing_newline() -> None:
    text = render_authoring_contract(
        folio_version=__version__,
        generated_at="2026-07-28T09:12:04Z",
        config_keys=CORE_CONFIG_KEYS,
    )

    assert text.endswith("}\n")
    assert json.loads(text)["configKeys"] == sorted(CORE_CONFIG_KEYS)


def _site_builder(tmp_path: Path) -> SiteBuilder:
    return SiteBuilder(
        Config(project_name="Demo", output_dir=str(tmp_path / "output")),
        str(tmp_path / "template"),
        str(tmp_path / "build"),
    )


def _plugin_registry() -> ExtensionRegistry:
    registry = ExtensionRegistry()
    registry.register_component(
        "ParamTable",
        import_path="@/components/param-table",
        props={"args": "unknown[]"},
        required=True,
        contract=True,
        source_label="api-reference",
        origin="builtin",
    )
    registry.register_component(
        "GlossaryList",
        import_path="@/components/glossary-list",
        props={"items": "string[]"},
        contract=True,
        source_label="plugin:glossary",
    )
    return registry


def test_apply_extensions_writes_registry_components_into_the_contract_module(
    tmp_path: Path,
) -> None:
    """The emitted TypeScript contract follows the registry, not the builtins.

    Template preparation writes the module before plugins run, so it can only
    carry the builtin manifest; applying the extensions has to replace it or a
    plugin component flagged ``contract=True`` never reaches the contract.
    """
    builder = _site_builder(tmp_path)

    builder.apply_extensions(_plugin_registry())

    module = (tmp_path / "build" / "lib" / "folio-mdx-contract.ts").read_text(
        encoding="utf-8"
    )
    assert '"name": "GlossaryList"' in module
    assert '"source": "plugin:glossary"' in module
    assert '"name": "ParamTable"' in module


def test_write_authoring_contract_publishes_a_static_file_in_the_export(
    tmp_path: Path,
) -> None:
    builder = _site_builder(tmp_path)
    builder.apply_extensions(_plugin_registry())
    builder.register_route("api-reference/index")
    builder.register_route("guide/plugins/authoring")

    target = builder.write_authoring_contract(
        config_keys={"project", "roadmap"},
        generated_at="2026-07-28T09:12:04Z",
    )

    assert target == tmp_path / "build" / "public" / FOLIO_AUTHORING_CONTRACT_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["folioVersion"] == __version__
    assert payload["mdxContractVersion"] == FOLIO_MDX_CONTRACT_VERSION
    assert payload["generatedAt"] == "2026-07-28T09:12:04Z"
    assert payload["configKeys"] == ["project", "roadmap"]
    assert payload["routes"] == [
        "/docs/api-reference/",
        "/docs/guide/plugins/authoring/",
    ]
    assert [entry["name"] for entry in payload["components"]] == [
        "ParamTable",
        "GlossaryList",
    ]


def test_write_authoring_contract_falls_back_to_the_builtin_components(
    tmp_path: Path,
) -> None:
    """Without applied extensions there is no registry, so the builtins stand in."""
    builder = _site_builder(tmp_path)

    target = builder.write_authoring_contract(
        config_keys=CORE_CONFIG_KEYS,
        generated_at="2026-07-28T09:12:04Z",
    )

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["components"] == FOLIO_MDX_COMPONENTS
    assert payload["routes"] == []
