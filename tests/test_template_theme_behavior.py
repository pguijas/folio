"""Behavioral tests for the bundled template's theme registry and bootstrap.

The template package has no JS test harness, but its pure theme modules
(``template/theme/preset-registry.ts`` and ``template/theme/preset-types.ts``)
only carry erasable TypeScript syntax, so Node's built-in type stripping can
import and exercise them directly. These tests drive the real modules (not
replicas) through small Node scripts and assert the invariants the Python
string assertions in test_site_builder.py cannot observe:

- registerPreset is last-wins, so a generated project preset that reuses a
  builtin id replaces the builtin (exactly one registry entry).
- registerPreset before registerGroup creates a placeholder group that
  registerGroup later merges into (label + union of preset ids).
- groupPresetsForDisplay shows every preset exactly once (first group wins,
  project group first), falls back to an "Other" group for ungrouped presets,
  and drops empty groups.
- buildBootstrapPresets embeds only the default resolution for presets whose
  option-combination count exceeds MAX_BOOTSTRAP_COMBINATIONS, and decides
  that from the option-count product WITHOUT enumerating the full cartesian
  product first.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

_TEMPLATE_THEME_DIR = Path(__file__).parents[1] / "template" / "theme"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node is required for template theme behavior tests",
)


def _run_node_driver(tmp_path: Path, script: str, *module_paths: Path) -> dict:
    driver = tmp_path / "driver.mjs"
    driver.write_text(script, encoding="utf-8")
    result = subprocess.run(
        ["node", "--no-warnings", str(driver), *[str(p) for p in module_paths]],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        if "ERR_UNKNOWN_FILE_EXTENSION" in result.stderr:
            pytest.skip("this Node version cannot import TypeScript directly")
        raise AssertionError(
            f"node driver failed (exit {result.returncode}):\n{result.stderr}"
        )
    return json.loads(result.stdout)


_REGISTRY_DRIVER = """
import { pathToFileURL } from "node:url"

const [registryPath] = process.argv.slice(2)
const {
  registerPreset,
  registerGroup,
  getPresets,
  getGroups,
  groupPresetsForDisplay,
} = await import(pathToFileURL(registryPath).href)

const theme = {
  preview: { light: "#fff", dark: "#000" },
  radius: "0",
  style: {},
  light: {},
  dark: {},
}
const makePreset = (id, name = id) => ({
  id,
  name,
  description: "",
  scene: "",
  preview: { light: "#fff", dark: "#000" },
  defaultOptions: {},
  controls: [],
  resolve: () => theme,
})

// Mirror the presets.ts registration sequence: builtins first, then a
// generated project preset that reuses a builtin id ("atlas"), then an
// extension preset registered into a group that does not exist yet, then a
// preset with no group at all, then the registerGroup calls.
registerPreset(makePreset("atlas", "Atlas"))
registerPreset(makePreset("beacon", "Beacon"))
registerPreset(makePreset("atlas", "Customized Atlas"), "project")
registerPreset(makePreset("ext-preset", "Extension"), "someGroup")
registerPreset(makePreset("loose", "Loose"))

registerGroup("project", "Project", ["atlas"])
registerGroup("someGroup", "Some Group", [])
registerGroup("reference", "Reference", ["atlas", "beacon"])
registerGroup("empty", "Empty", [])

const presets = getPresets()
const groups = getGroups()
const display = groupPresetsForDisplay(groups, presets)

console.log(JSON.stringify({
  atlasEntries: presets.filter((p) => p.id === "atlas").map((p) => p.name),
  someGroup: groups.find((g) => g.id === "someGroup"),
  display: display.map((g) => ({
    id: g.id,
    label: g.label,
    presetNames: g.presets.map((p) => p.name),
  })),
}))
"""


def test_preset_registry_last_wins_and_placeholder_merge(tmp_path: Path) -> None:
    data = _run_node_driver(
        tmp_path, _REGISTRY_DRIVER, _TEMPLATE_THEME_DIR / "preset-registry.ts"
    )

    # Last-wins: the project preset registered after the builtin replaces it,
    # leaving exactly one "atlas" entry -- the customized one. If the
    # registration were flipped to first-wins (or presets.ts registered the
    # project preset before the builtins), this would fail.
    assert data["atlasEntries"] == ["Customized Atlas"]

    # registerPreset before registerGroup: the placeholder group later merges
    # the registerGroup label while keeping the registered preset id.
    assert data["someGroup"]["label"] == "Some Group"
    assert data["someGroup"]["presetIds"] == ["ext-preset"]


def test_group_presets_for_display_dedups_and_falls_back(tmp_path: Path) -> None:
    data = _run_node_driver(
        tmp_path, _REGISTRY_DRIVER, _TEMPLATE_THEME_DIR / "preset-registry.ts"
    )
    display = data["display"]
    by_id = {group["id"]: group for group in display}

    # The customized builtin appears exactly once, under Project (first group
    # wins; the project placeholder group is created before any other group).
    appearances = [
        (group["id"], name)
        for group in display
        for name in group["presetNames"]
        if name.endswith("Atlas")
    ]
    assert appearances == [("project", "Customized Atlas")]

    # Later groups skip the already-shown preset but keep their own members.
    assert by_id["reference"]["presetNames"] == ["Beacon"]

    # A preset registered into a group before registerGroup stays visible.
    assert by_id["someGroup"]["presetNames"] == ["Extension"]

    # Ungrouped presets land in the "Other" fallback group; empty groups are
    # dropped entirely.
    assert by_id["other"]["presetNames"] == ["Loose"]
    assert "empty" not in by_id


_BOOTSTRAP_DRIVER = """
import { pathToFileURL } from "node:url"

const [typesPath] = process.argv.slice(2)
const {
  buildBootstrapPresets,
  countPresetOptionCombinations,
  MAX_BOOTSTRAP_COMBINATIONS,
} = await import(pathToFileURL(typesPath).href)

const theme = {
  preview: { light: "", dark: "" },
  radius: "0",
  style: {},
  light: {},
  dark: {},
}
const makeControl = (id, count) => ({
  id,
  label: id,
  options: Array.from({ length: count }, (_, i) => ({
    label: `${id}${i}`,
    value: `${id}${i}`,
  })),
})
const makePreset = (id, controls, counter) => ({
  id,
  name: id,
  description: "",
  scene: "",
  preview: { light: "", dark: "" },
  defaultOptions: Object.fromEntries(
    controls.map((control) => [control.id, control.options[0].value])
  ),
  controls,
  resolve: () => {
    counter.count += 1
    return theme
  },
})

const smallCounter = { count: 0 }
const small = makePreset(
  "small",
  [makeControl("a", 2), makeControl("b", 2)],
  smallCounter
)

// 2^9 = 512 combinations: exactly on budget, fully embedded.
const boundaryCounter = { count: 0 }
const boundary = makePreset(
  "boundary",
  Array.from({ length: 9 }, (_, i) => makeControl(`b${i}`, 2)),
  boundaryCounter
)

// 8 * 8 * 9 = 576 > 512: over budget, only the default resolution embedded.
const overCounter = { count: 0 }
const over = makePreset(
  "over",
  [makeControl("a", 8), makeControl("b", 8), makeControl("c", 9)],
  overCounter
)

// 10 controls x 10 options = 10^10 combinations. If the cap were evaluated
// only after eagerly materializing the cartesian product this would hang or
// exhaust memory instead of finishing instantly.
const hugeCounter = { count: 0 }
const huge = makePreset(
  "huge",
  Array.from({ length: 10 }, (_, i) => makeControl(`h${i}`, 10)),
  hugeCounter
)

const bootstrap = buildBootstrapPresets([small, boundary, over, huge])
const byId = Object.fromEntries(bootstrap.map((preset) => [preset.id, preset]))

console.log(JSON.stringify({
  max: MAX_BOOTSTRAP_COMBINATIONS,
  smallThemeKeyCount: Object.keys(byId.small.themes).length,
  boundaryThemeKeyCount: Object.keys(byId.boundary.themes).length,
  overThemeKeys: Object.keys(byId.over.themes),
  overDefaultKey: byId.over.defaultKey,
  hugeThemeKeys: Object.keys(byId.huge.themes),
  hugeDefaultKey: byId.huge.defaultKey,
  hugeResolveCalls: hugeCounter.count,
  overCombinationCount: countPresetOptionCombinations(over),
  hugeCombinationCount: countPresetOptionCombinations(huge),
}))
"""


def test_bootstrap_presets_cap_combinations(tmp_path: Path) -> None:
    data = _run_node_driver(
        tmp_path, _BOOTSTRAP_DRIVER, _TEMPLATE_THEME_DIR / "preset-types.ts"
    )

    assert data["max"] == 512

    # Within budget: every combination is embedded (including the 512
    # boundary), so the inline bootstrap can resolve any option choice.
    assert data["smallThemeKeyCount"] == 4
    assert data["boundaryThemeKeyCount"] == 512

    # Over budget: only the default resolution is embedded, keyed by the
    # preset's default key (which the inline bootstrap falls back to).
    assert data["overCombinationCount"] == 576
    assert data["overThemeKeys"] == [data["overDefaultKey"]]

    # The cap bounds enumeration cost too: a 10^10-combination preset resolves
    # its theme exactly once and the count comes from the option-count product
    # rather than a materialized cartesian product (the driver would time out
    # otherwise).
    assert data["hugeCombinationCount"] == 10**10
    assert data["hugeThemeKeys"] == [data["hugeDefaultKey"]]
    assert data["hugeResolveCalls"] == 1
