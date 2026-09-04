import re
import shutil
from pathlib import Path

from folio_docs.builtins import BUILTIN_COMPONENTS, register_builtin_components
from folio_docs.extensions import ExtensionRegistry
from folio_docs.docs.builtin_drift import (
    check_component_prop_drift,
    check_template_drift,
    component_object_field_names,
    component_prop_names,
)
from folio_docs.docs.extension_emitter import ExtensionEmitter
from folio_docs.docs.integrations.landing import _FUNNEL_ICONS

TEMPLATE = Path(__file__).parents[1] / "template" / "mdx-components.tsx"
COMPONENTS_DIR = Path(__file__).parents[1] / "template" / "components"
LANDING_SECTIONS = (
    Path(__file__).parents[1] / "template" / "components" / "landing" / "sections.tsx"
)


def _expected_import_lines() -> list[str]:
    names_by_module: dict[str, list[str]] = {}
    for component in BUILTIN_COMPONENTS:
        names_by_module.setdefault(component.import_path, []).append(
            component.imported_name
        )
    return [
        f'import {{ {", ".join(names)} }} from "{import_path}"'
        for import_path, names in names_by_module.items()
    ]


def test_manifest_imports_present_in_template() -> None:
    content = TEMPLATE.read_text(encoding="utf-8")
    for line in _expected_import_lines():
        assert line in content, f"manifest import drifted from template: {line}"


def test_manifest_entries_present_and_ordered() -> None:
    content = TEMPLATE.read_text(encoding="utf-8")
    entries = [f"    {component.name}," for component in BUILTIN_COMPONENTS]
    positions = [content.index(entry) for entry in entries]
    assert positions == sorted(positions), "entry order drifted from template"


def test_check_template_drift_is_clean_for_bundled_template() -> None:
    content = TEMPLATE.read_text(encoding="utf-8")

    assert check_template_drift(content) == []


class TestComponentPropParsing:
    """`component_prop_names` reads a component's real props out of its TSX."""

    def test_inline_destructured_annotation(self) -> None:
        source = """
export function TimelineItem({
  date,
  title,
  badge,
  children,
}: {
  date: string
  title: string
  badge?: string
  children: React.ReactNode
}) {
  return null
}
"""
        assert component_prop_names(source, "TimelineItem") == {
            "date": True,
            "title": True,
            "badge": False,
            "children": True,
        }

    def test_named_props_interface(self) -> None:
        source = """
interface CardGridProps {
  columns?: 2 | 3 | 4
  children: React.ReactNode
}

export function CardGrid({ columns = 3, children }: CardGridProps) {
  return null
}
"""
        assert component_prop_names(source, "CardGrid") == {
            "columns": False,
            "children": True,
        }

    def test_quoted_prop_name(self) -> None:
        source = """
interface TabsProps {
  children: React.ReactNode
  "aria-label"?: string
}

export function Tabs({ children }: TabsProps) {
  return null
}
"""
        assert component_prop_names(source, "Tabs") == {
            "children": True,
            "aria-label": False,
        }

    def test_object_fields_behind_a_named_type_alias_are_resolved(self) -> None:
        source = """
type ApiModule = {
  name: string
  description: string
  href: string
  classCount: number
  functionCount: number
}

export function ApiReferenceIndex({ modules }: { modules: ApiModule[] }) {
  return null
}
"""
        assert component_prop_names(source, "ApiReferenceIndex") == {
            "modules": True
        }
        assert component_object_field_names(source, "ApiReferenceIndex") == {
            "modules": {
                "name",
                "description",
                "href",
                "classCount",
                "functionCount",
            }
        }

    def test_unknown_component_returns_nothing(self) -> None:
        assert component_prop_names("export const x = 1\n", "Nope") is None


def test_manifest_props_match_the_bundled_components() -> None:
    """The manifest and the TSX declare props separately; nothing bound them.

    `check_template_drift` compared component *names* only, so a manifest prop
    the component never reads - or a component prop the manifest never
    declares - shipped with a green suite. Six components had drifted.
    """
    assert check_component_prop_drift(COMPONENTS_DIR) == []


def test_check_component_prop_drift_flags_a_renamed_prop(tmp_path: Path) -> None:
    """A synthetic drift must be reported, so the guard has teeth."""
    components = tmp_path / "components"
    components.mkdir()
    shutil.copytree(COMPONENTS_DIR, components, dirs_exist_ok=True)
    card_grid = components / "card-grid.tsx"
    card_grid.write_text(
        card_grid.read_text(encoding="utf-8").replace("columns", "cols"),
        encoding="utf-8",
    )

    drift = check_component_prop_drift(components)

    assert any("CardGrid" in entry and "columns" in entry for entry in drift), drift


def test_check_template_drift_flags_builtin_missing_from_template() -> None:
    content = TEMPLATE.read_text(encoding="utf-8").replace(
        "    ComparisonMatrix,\n", ""
    )

    drift = check_template_drift(content)

    assert len(drift) == 1
    assert "ComparisonMatrix" in drift[0]
    assert "no entry in mdx-components.tsx" in drift[0]


def test_check_template_drift_flags_template_entry_missing_from_manifest() -> None:
    content = TEMPLATE.read_text(encoding="utf-8").replace(
        "    ...components,", "    NewWidget,\n    ...components,"
    )

    drift = check_template_drift(content)

    assert len(drift) == 1
    assert "NewWidget" in drift[0]
    assert "not declared in the builtin manifest" in drift[0]


def test_check_template_drift_ignores_comments_and_import_lists() -> None:
    """Commented-out entries and names inside multi-line import lists must not
    count as component entries."""
    content = TEMPLATE.read_text(encoding="utf-8").replace(
        "    ...components,",
        "    // GhostWidget,\n    ...components,",
    )
    content = 'import {\n  IgnoredWidget,\n} from "./ignored"\n' + content

    assert check_template_drift(content) == []


def test_funnel_icon_keys_match_the_template_map() -> None:
    """The plugin drops any funnel `icon` value outside its whitelist, so a key
    the template can draw but the plugin does not know is silently unreachable
    from docs.yaml — and the reverse renders a card with no mark. Pin them."""
    content = LANDING_SECTIONS.read_text(encoding="utf-8")
    block = re.search(
        r"const FUNNEL_ICONS: Record<string, IconSvgElement> = \{(.*?)\n\}",
        content,
        re.DOTALL,
    )
    assert block, "FUNNEL_ICONS map not found in sections.tsx"
    template_keys = set(re.findall(r"^\s*(\w+):", block.group(1), re.MULTILINE))

    assert template_keys == set(_FUNNEL_ICONS), (
        "funnel icon keys drifted between folio/docs/integrations/landing.py and "
        "template/components/landing/sections.tsx"
    )


def test_registering_builtins_leaves_template_mdx_components_unchanged(
    tmp_path: Path,
) -> None:
    """End-to-end: emitting a registry that contains the builtins against the
    real bundled template must not modify mdx-components.tsx (builtins are
    already wired there; only plugin/config components get injected)."""
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    shutil.copy2(TEMPLATE, build_dir / "mdx-components.tsx")
    original = (build_dir / "mdx-components.tsx").read_text(encoding="utf-8")

    registry = ExtensionRegistry()
    register_builtin_components(registry)
    ExtensionEmitter(build_dir).apply(registry)

    assert (build_dir / "mdx-components.tsx").read_text(encoding="utf-8") == original
