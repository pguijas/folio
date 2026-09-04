import re
import shutil
from pathlib import Path

from folio.builtins import BUILTIN_COMPONENTS, register_builtin_components
from folio.extensions import ExtensionRegistry
from folio.generator.builtin_drift import (
    check_template_drift,
    expected_entry_lines,
    expected_import_lines,
)
from folio.generator.extension_emitter import ExtensionEmitter
from folio.plugins.landing import _FUNNEL_ICONS

TEMPLATE = Path(__file__).parents[1] / "template" / "mdx-components.tsx"
LANDING_SECTIONS = (
    Path(__file__).parents[1] / "template" / "components" / "landing" / "sections.tsx"
)


def test_expected_import_lines_group_multi_export_modules() -> None:
    lines = expected_import_lines(BUILTIN_COMPONENTS)
    assert 'import { Tabs, TabItem } from "@/components/tabs"' in lines
    assert 'import { Steps, Step } from "@/components/steps"' in lines
    # One line per module, not per component.
    assert 'import { Tabs } from "@/components/tabs"' not in lines


def test_manifest_imports_present_in_template() -> None:
    content = TEMPLATE.read_text(encoding="utf-8")
    for line in expected_import_lines(BUILTIN_COMPONENTS):
        assert line in content, f"manifest import drifted from template: {line}"


def test_manifest_entries_present_and_ordered() -> None:
    content = TEMPLATE.read_text(encoding="utf-8")
    entries = expected_entry_lines(BUILTIN_COMPONENTS)
    positions = [content.index(entry) for entry in entries]
    assert positions == sorted(positions), "entry order drifted from template"


def test_check_template_drift_is_clean_for_bundled_template() -> None:
    content = TEMPLATE.read_text(encoding="utf-8")

    assert check_template_drift(content) == []


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
        "funnel icon keys drifted between folio/plugins/landing.py and "
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
