import hashlib
import io
import sys
import json
import re
import shutil
import subprocess
import time as real_time
import types
from pathlib import Path

import pytest
import typer
import yaml
from rich.cells import cell_len
from rich.console import Console
from typer.main import get_command
from typer.testing import CliRunner

import folio.build as build_module
import folio.branding as branding_module
import folio.config as config_module
from folio import __version__
from folio import cli as cli_module
from folio.branding import FOLIO_ASCII_ART, folio_banner
from folio.cli import _generate_docs_yaml, _sync_version_matrix, app
from folio.config import load_config

runner = CliRunner()
CLI_DOC = Path(__file__).parents[1] / "docs" / "guide" / "cli.md"


def _enable_disabled_features(monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "is_feature_enabled", lambda feature: True)
    monkeypatch.setattr(config_module, "is_feature_enabled", lambda feature: True)


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _version_manifest(
    *,
    label: str,
    path: str,
    ref: str,
    commit: str,
    versions: list[dict],
    synced_config: dict,
) -> dict:
    return {
        "schema": 1,
        "label": label,
        "path": path,
        "ref": ref,
        "commit": commit,
        "versions_hash": _stable_hash(versions),
        "synced_config_hash": _stable_hash(synced_config),
        "folio_version": __version__,
    }


def _has_folio_update_line(output: str) -> bool:
    return any(f"· {item} ·" in output for item in branding_module.FOLIO_NEWS_ITEMS)


def _strip_ansi(output: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", output)


def test_cli_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])
    assert result.exit_code == 0
    assert (tmp_path / "docs.yaml").exists()
    assert (tmp_path / "docs" / "index.md").exists()


def test_cli_init_yes_prints_polished_setup_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output
    assert "████████╗ ██████╗ ██╗" in result.output
    assert "______ ____" not in result.output
    assert "Initialize docs from your Python project" not in result.output
    assert "Folio will write docs.yaml" not in result.output
    assert "Detected" in result.output
    assert "Project scan" not in result.output
    assert "Target" in result.output
    assert "Python" in result.output
    assert "Framework" in result.output
    assert "Status" in result.output
    assert "Documentation scaffold not found" in result.output
    assert "✓ Documentation project ready" in result.output
    assert "Created " in result.output
    assert "docs.yaml" in result.output
    assert "Next commands" in result.output
    assert "folio serve" in result.output
    assert "folio build" in result.output
    assert "folio coverage" in result.output
    parsed = yaml.safe_load((tmp_path / "docs.yaml").read_text(encoding="utf-8"))
    assert parsed["theme"]["preset"] == "organic-editorial"
    assert "landing" not in parsed


def test_cli_init_interactive_uses_iterative_choices(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)], input="\n\n\n\n")

    assert result.exit_code == 0, result.output
    assert "████████╗ ██████╗ ██╗" in result.output
    assert "Turn Python into polished docs" not in result.output
    assert "News:" not in result.output
    assert _has_folio_update_line(result.output)
    assert f"v{__version__}" in result.output
    assert f"Folio v{__version__}" not in result.output
    assert "______ ____" not in result.output
    assert "Initialize docs from your Python project" not in result.output
    assert "Folio will write docs.yaml" not in result.output
    assert "Project scan" not in result.output
    assert "Detected" in result.output
    assert "Target" in result.output
    assert "Project" in result.output
    assert "Source" in result.output
    assert "Repo" in result.output
    assert "Python" in result.output
    assert "Framework" in result.output
    assert "Status" in result.output
    assert "Documentation scaffold not found" in result.output
    assert "Use detected project settings" not in result.output
    assert "Docstring style" in result.output
    assert "1. Google" in result.output
    assert "2. NumPy" in result.output
    assert "3. Auto-detect" in result.output
    assert "Visual preset" in result.output
    assert "1. Organic Editorial" in result.output
    assert "2. Beacon" in result.output
    assert "3. Atlas" in result.output
    assert "4. Workshop" in result.output
    assert "🏠 Starter landing page" not in result.output
    assert "✔ Created " in result.output
    assert "docs.yaml" in result.output


def test_cli_init_defaults_docstring_style_to_auto(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)], input="\n\n\n")

    assert result.exit_code == 0, result.output
    assert "3. Auto-detect (default)" in result.output
    config = load_config(tmp_path / "docs.yaml")
    assert config.docstring_style == "auto"


def test_cli_init_arrow_prompts_are_consecutive(tmp_path: Path, monkeypatch) -> None:
    class FakeKey:
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.ENTER, FakeKey.ENTER, "n"])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )

    monkeypatch.setattr(cli_module, "_init_can_use_arrow_select", lambda: True)
    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0, result.output
    clean_output = _strip_ansi(result.output)
    assert re.search(
        r"✔ Docstring style\s+› auto\n\? Visual preset\s+›",
        clean_output,
    )
    assert re.search(
        r"✔ Visual preset\s+› organic-editorial",
        clean_output,
    )
    assert "Starter landing page" not in clean_output


def test_cli_init_arrow_completed_lines_align_choice_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeKey:
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.ENTER, FakeKey.ENTER, "n"])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )

    monkeypatch.setattr(cli_module, "_init_can_use_arrow_select", lambda: True)
    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0, result.output
    clean_output = _strip_ansi(result.output)
    completed_lines = [
        line
        for line in clean_output.splitlines()
        if line.startswith("✔ ")
        and any(
            title in line
            for title in (
                "Docstring style",
                "Visual preset",
            )
        )
    ]
    answer_columns = {cell_len(line[: line.index("›")]) for line in completed_lines}

    assert len(completed_lines) == 2
    assert len(answer_columns) == 1


def test_cli_init_prints_created_paths_relative_to_current_directory() -> None:
    with runner.isolated_filesystem():
        target = Path("tmp/sample-init-check")
        target.mkdir(parents=True)

        result = runner.invoke(app, ["init", str(target)], input="\n2\nn\n")

        assert result.exit_code == 0, result.output
        assert "✔ Created tmp/sample-init-check/docs.yaml" in result.output
        assert "✔ Created docs.yaml" not in result.output
        assert "Next folio serve tmp/sample-init-check" in result.output


def test_cli_init_terminal_intro_does_not_repaint_inside_arrow_prompt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeKey:
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.ENTER, FakeKey.ENTER, "y"])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )

    test_console = Console(record=True, force_terminal=True, width=160)
    monkeypatch.setattr(cli_module, "console", test_console)
    monkeypatch.setattr(cli_module, "_init_can_use_arrow_select", lambda: True)
    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0, result.output
    clean_output = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", result.output)
    first_prompt = clean_output.index("? Docstring style")
    assert "████████╗ ██████╗ ██╗" in clean_output[:first_prompt]
    assert "████████╗ ██████╗ ██╗" not in clean_output[first_prompt:]


def test_cli_init_terminal_intro_refreshes_news_while_arrow_prompt_waits(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class FakeKey:
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    class FakeClock:
        current = 0.0

        def time(self) -> float:
            return self.current

    clock = FakeClock()
    pressed_keys = iter([FakeKey.ENTER, FakeKey.ENTER, "y"])

    def readkey() -> str:
        clock.current = 1
        deadline = real_time.monotonic() + 0.05
        while real_time.monotonic() < deadline:
            real_time.sleep(0.001)
        return next(pressed_keys)

    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=readkey,
    )

    test_console = Console(record=True, force_terminal=True, width=160)
    monkeypatch.setattr(branding_module.time, "time", clock.time)
    monkeypatch.setattr(cli_module, "console", test_console)
    monkeypatch.setattr(cli_module, "_init_can_use_arrow_select", lambda: True)
    monkeypatch.setattr(cli_module, "_INIT_NEWS_REFRESH_SECONDS", 0.01)
    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert f"· {branding_module.FOLIO_NEWS_ITEMS[0]} ·" in result.output
    assert f"· {branding_module.FOLIO_NEWS_ITEMS[1]} ·" in result.output


def test_cli_init_intro_uses_current_one_second_news_window(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(branding_module.time, "time", lambda: 1)

    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output
    assert f"· {branding_module.FOLIO_NEWS_ITEMS[1]} ·" in result.output


def test_cli_init_uses_reference_section_color_palette() -> None:
    styles = cli_module._INIT_SECTION_STYLES

    assert styles["detected_border"] == "#bfdbfe"
    assert styles["detected_label"] == "bold #fbbf24"
    assert styles["detected_value"] == "#f8fafc"
    assert styles["banner_logo"] == "bold #c4b5fd"
    assert "banner_subtitle" not in styles
    assert styles["banner_news"] == "bold #bef264"
    assert styles["docstring"] == "bold #a78bfa"
    assert styles["theme"] == "bold #f472b6"
    assert "landing" not in styles
    assert styles["ready_border"] == "#a78bfa"
    assert "bold cyan" not in styles.values()
    assert (
        len(
            {
                styles["detected_border"],
                styles["detected_label"],
                styles["banner_news"],
                styles["docstring"],
                styles["theme"],
                styles["ready_border"],
            }
        )
        == 6
    )


def test_cli_init_detected_labels_use_distinct_row_colors() -> None:
    body = cli_module._detected_summary_body(
        {
            "name": "aurora-labs",
            "version": "1.8.4",
            "python_path": "src/aurora",
            "python_version": "3.12",
            "framework": "Typer package",
            "status": "Documentation scaffold not found",
        },
        Path("tmp/aurora"),
        "https://github.com/example/aurora-labs",
    )
    expected_styles = {
        "Target": "bold #fb7185",
        "Project": "bold #fbbf24",
        "Source": "bold #c084fc",
        "Repo": "bold #38bdf8",
        "Python": "bold #bef264",
        "Framework": "bold #a78bfa",
        "Status": "bold #fde68a",
    }
    actual_styles = {
        body.plain[span.start : span.end]: str(span.style)
        for span in body.spans
        if body.plain[span.start : span.end] in expected_styles
    }

    assert actual_styles == expected_styles
    assert len(set(actual_styles.values())) == len(expected_styles)


def test_cli_init_detected_panel_is_compact_reference_style_and_avoids_duplicate_icons(
    monkeypatch,
) -> None:
    test_console = Console(record=True, width=160, color_system=None)
    monkeypatch.setattr(cli_module, "console", test_console)

    cli_module._print_init_intro(
        {
            "name": "aurora-labs",
            "version": "1.8.4",
            "python_path": "src/aurora",
            "python_version": "3.12",
            "framework": "Typer package",
            "status": "Documentation scaffold not found",
        },
        Path("tmp/aurora"),
        "https://github.com/example/aurora-labs",
    )

    output = test_console.export_text()
    border_lines = [
        line
        for line in output.splitlines()
        if "Detected" in line or line.lstrip().startswith("╰")
    ]
    assert border_lines
    assert max(len(line.strip()) for line in border_lines) < 100
    assert all(line.startswith(" ") for line in border_lines)
    expected_rows = (
        ("Target", "tmp/aurora"),
        ("Project", "aurora-labs 1.8.4"),
        ("Source", "src/aurora"),
        ("Repo", "https://github.com/example/aurora-labs"),
        ("Python", "3.12"),
        ("Framework", "Typer package"),
        ("Status", "Documentation scaffold not found"),
    )
    value_columns = set()
    for label, value in expected_rows:
        line = next(
            line for line in output.splitlines() if label in line and value in line
        )
        value_columns.add(cell_len(line[: line.index(value)]))
    assert len(value_columns) == 1
    assert "Target     tmp/aurora" in output
    assert "Project    aurora-labs 1.8.4" in output
    assert "Python     3.12" in output
    assert "Python      🐍" not in output
    assert "Framework" in output
    assert "Framework  Typer package" in output
    assert "Framework  ⚡" not in output
    assert "Status     Documentation scaffold not found" in output
    assert "Status     ✨" not in output
    assert "Status     🟡" not in output


def test_folio_banner_includes_sparkle_framed_update() -> None:
    banner = folio_banner(
        "v1.2.3",
        width=80,
        news_item=branding_module.FOLIO_NEWS_ITEMS[0],
    )
    plain = re.sub(r"\[/?[^\]]+\]", "", banner)

    assert "Turn Python into polished docs" not in plain
    assert "News:" not in plain
    assert f"· {branding_module.FOLIO_NEWS_ITEMS[0]} ·" in plain
    news_line = plain.splitlines()[-1].strip()
    assert "⚡ " not in news_line
    assert " ⚡" not in news_line


def test_folio_news_items_are_a_varied_hardcoded_feature_list() -> None:
    assert len(branding_module.FOLIO_NEWS_ITEMS) >= 10
    assert len(set(branding_module.FOLIO_NEWS_ITEMS)) == len(
        branding_module.FOLIO_NEWS_ITEMS
    )
    assert any("Pagefind" in item for item in branding_module.FOLIO_NEWS_ITEMS)
    assert any("Mermaid" in item for item in branding_module.FOLIO_NEWS_ITEMS)
    assert any("Coverage" in item for item in branding_module.FOLIO_NEWS_ITEMS)
    assert all(
        cell_len(f"· {item} ·") <= 80 for item in branding_module.FOLIO_NEWS_ITEMS
    )


def test_folio_banner_default_news_uses_current_one_second_window(monkeypatch) -> None:
    monkeypatch.setattr(branding_module.time, "time", lambda: 1)

    banner = folio_banner("v1.2.3", width=80)

    assert f"· {branding_module.FOLIO_NEWS_ITEMS[1]} ·" in banner


def test_folio_banner_news_line_is_centered_by_terminal_cells() -> None:
    banner = folio_banner(
        "v1.2.3",
        width=80,
        news_item=branding_module.FOLIO_NEWS_ITEMS[0],
    )
    visible_lines = [re.sub(r"\[/?[^\]]+\]", "", line) for line in banner.splitlines()]
    news_line = visible_lines[-1]
    left_padding = len(news_line) - len(news_line.lstrip(" "))
    right_padding = 80 - cell_len(news_line)

    assert abs(left_padding - right_padding) <= 1


def test_folio_banner_separates_logo_and_news_with_blank_line() -> None:
    banner = folio_banner(
        "v1.2.3",
        width=80,
        news_item=branding_module.FOLIO_NEWS_ITEMS[0],
    )
    visible_lines = [re.sub(r"\[/?[^\]]+\]", "", line) for line in banner.splitlines()]

    assert visible_lines[len(FOLIO_ASCII_ART.splitlines())] == ""
    assert visible_lines[-1].strip() == f"· {branding_module.FOLIO_NEWS_ITEMS[0]} ·"


def test_folio_news_item_changes_every_second() -> None:
    assert branding_module.folio_news_item(0) == branding_module.FOLIO_NEWS_ITEMS[0]
    assert branding_module.folio_news_item(0.99) == branding_module.FOLIO_NEWS_ITEMS[0]
    assert branding_module.folio_news_item(1) == branding_module.FOLIO_NEWS_ITEMS[1]
    assert branding_module.folio_news_item(2) == branding_module.FOLIO_NEWS_ITEMS[2]


def test_cli_init_choice_uses_arrow_selector_when_tty(monkeypatch) -> None:
    calls = []

    def fake_select(title, options, *, default, style):
        calls.append((title, options, default, style))
        return "beacon"

    monkeypatch.setattr(cli_module, "_init_can_use_arrow_select", lambda: True)
    monkeypatch.setattr(cli_module, "_ask_init_arrow_choice", fake_select)

    result = cli_module._ask_init_choice(
        "🎨 Visual preset",
        cli_module._INIT_THEME_PRESETS,
        default="organic-editorial",
        style=cli_module._INIT_SECTION_STYLES["theme"],
    )

    assert result == "beacon"
    assert calls == [
        (
            "🎨 Visual preset",
            cli_module._INIT_THEME_PRESETS,
            "organic-editorial",
            cli_module._INIT_SECTION_STYLES["theme"],
        )
    ]


def test_cli_init_arrow_choice_uses_readchar_inline_selector(monkeypatch) -> None:
    class FakeKey:
        UP = "UP"
        DOWN = "DOWN"
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.DOWN, FakeKey.ENTER])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )
    stdout = io.StringIO()

    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)
    monkeypatch.setattr(sys, "stdout", stdout)

    result = cli_module._ask_init_arrow_choice(
        "🎨 Visual preset",
        cli_module._INIT_THEME_PRESETS,
        default="organic-editorial",
        style=cli_module._INIT_SECTION_STYLES["theme"],
    )

    output = stdout.getvalue()
    assert result == "beacon"
    assert "\033[38;5;147m?\033[0m \033[1m🎨 Visual preset\033[0m" in output
    assert "Use arrow-keys. Return to submit." in output
    assert "\033[4mOrganic Editorial\033[0m" in output
    assert "\033[4mBeacon\033[0m" in output
    assert "\033[5A" in output
    assert "\033[2K" in output
    assert "✔" in output
    assert "\033[38;5;147m›\033[0m \033[1mbeacon\033[0m" in output


def test_cli_init_readchar_yes_no_uses_single_line_hint(monkeypatch) -> None:
    class FakeKey:
        UP = "UP"
        DOWN = "DOWN"
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.ENTER])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )
    stdout = io.StringIO()

    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)
    monkeypatch.setattr(sys, "stdout", stdout)

    result = cli_module._ask_init_arrow_yes_no(
        "Use detected project settings",
        default=True,
    )

    output = stdout.getvalue()
    assert result is True
    assert "(Y/n)" in output
    assert "Use arrow-keys. Return to submit." not in output
    assert "\033[4mYes\033[0m" not in output
    assert "\033[4mNo\033[0m" not in output
    assert "\033[3A" not in output
    assert "\033[1A" in output
    assert "✔" in output
    assert "Yes" in output


def test_cli_init_readchar_yes_no_uses_no_default_hint(monkeypatch) -> None:
    class FakeKey:
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.ENTER])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )
    stdout = io.StringIO()

    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)
    monkeypatch.setattr(sys, "stdout", stdout)

    result = cli_module._ask_init_arrow_yes_no(
        "Use detected project settings",
        default=False,
    )

    output = stdout.getvalue()
    assert result is False
    assert "(y/N)" in output
    assert "✔" in output
    assert "No" in output


def test_cli_init_readchar_yes_no_allows_arrow_selection(monkeypatch) -> None:
    class FakeKey:
        UP = "UP"
        DOWN = "DOWN"
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    pressed_keys = iter([FakeKey.DOWN, FakeKey.ENTER])
    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: next(pressed_keys),
    )
    stdout = io.StringIO()

    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)
    monkeypatch.setattr(sys, "stdout", stdout)

    result = cli_module._ask_init_arrow_yes_no(
        "Use detected project settings",
        default=True,
    )

    output = stdout.getvalue()
    assert result is False
    assert "(Y/n)" in output
    assert "(y/N)" in output
    assert "Use arrow-keys. Return to submit." not in output
    assert "\033[4mYes\033[0m" not in output
    assert "\033[4mNo\033[0m" not in output
    assert "✔" in output
    assert "No" in output


def test_cli_init_readchar_yes_no_accepts_keyboard_shortcut(monkeypatch) -> None:
    class FakeKey:
        ENTER = "\r"
        ESC = "\x1b"
        CTRL_C = "\x03"

    fake_readchar = types.SimpleNamespace(
        key=FakeKey,
        readkey=lambda: "n",
    )
    stdout = io.StringIO()

    monkeypatch.setitem(sys.modules, "readchar", fake_readchar)
    monkeypatch.setattr(sys, "stdout", stdout)

    result = cli_module._ask_init_arrow_yes_no(
        "Use detected project settings",
        default=True,
    )

    output = stdout.getvalue()
    assert result is False
    assert "(Y/n)" in output
    assert "Use arrow-keys. Return to submit." not in output
    assert "✔" in output
    assert "No" in output


def test_folio_banner_can_center_logo_as_block() -> None:
    banner = folio_banner(
        "v1.2.3",
        width=80,
        news_item=branding_module.FOLIO_NEWS_ITEMS[0],
    )
    visible_lines = [re.sub(r"\[/?[^\]]+\]", "", line) for line in banner.splitlines()]
    raw_lines = FOLIO_ASCII_ART.splitlines()
    expected_padding = (80 - max(len(line) for line in raw_lines)) // 2
    expected_lines = [f"{' ' * expected_padding}{line}" for line in raw_lines]
    expected_lines[-1] = f"{expected_lines[-1]} v1.2.3"

    assert expected_padding > 0
    assert visible_lines[: len(expected_lines)] == expected_lines
    assert len(visible_lines) == len(expected_lines) + 2
    assert visible_lines[len(expected_lines)] == ""
    assert visible_lines[-1].strip() == f"· {branding_module.FOLIO_NEWS_ITEMS[0]} ·"


def test_cli_init_keyboard_interrupt_reports_no_files_changed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def raise_keyboard_interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module, "_ask_init_choice", raise_keyboard_interrupt)

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 1
    assert "^C Init aborted. No files changed." in result.output
    assert not (tmp_path / "docs.yaml").exists()


def test_cli_init_compact_ready_uses_no_panel(monkeypatch) -> None:
    test_console = Console(record=True, width=160, color_system=None)
    monkeypatch.setattr(cli_module, "console", test_console)

    cli_module._print_init_ready(
        Path.cwd(),
        ["docs.yaml", "docs/index.md"],
        compact=True,
    )

    output = test_console.export_text()
    assert "╭" not in output
    assert "╰" not in output
    assert "Ready" not in output
    assert "✔ Created docs.yaml" in output
    assert "✔ Created docs/index.md" in output
    assert "folio serve" in output
    assert len([line for line in output.splitlines() if line.strip()]) == 3


def test_cli_init_compact_ready_keeps_created_filenames_searchable(monkeypatch) -> None:
    test_console = Console(record=True, width=45, color_system=None)
    monkeypatch.setattr(cli_module, "console", test_console)

    cli_module._print_init_ready(
        Path("/tmp/pytest-of-runner/pytest-0/test_cli_init_interactive_uses0"),
        [
            "../../../../../tmp/pytest-of-runner/pytest-0/test_cli_init_interactive_uses0/docs.yaml",
            "../../../../../tmp/pytest-of-runner/pytest-0/test_cli_init_interactive_uses0/docs/index.md",
            "../../../../../tmp/pytest-of-runner/pytest-0/test_cli_init_interactive_uses0/.github/workflows/pages.yml",
            "../../../../../tmp/pytest-of-runner/pytest-0/test_cli_init_interactive_uses0/.github/workflows/branch-previews.yml",
        ],
        compact=True,
    )

    output = test_console.export_text()
    assert "docs.yaml" in output
    assert "docs/index.md" in output
    assert ".github/workflows/pages.yml" in output
    assert ".github/workflows/branch-previews.yml" in output


def test_cli_init_ready_panel_stays_compact(monkeypatch) -> None:
    test_console = Console(record=True, width=160, color_system=None)
    monkeypatch.setattr(cli_module, "console", test_console)

    cli_module._print_init_ready(Path.cwd(), ["docs.yaml", "docs/index.md"])

    lines = test_console.export_text().splitlines()
    border_lines = [line for line in lines if "Ready" in line or line.startswith("╰")]
    assert border_lines
    assert max(len(line) for line in border_lines) < 100


def test_cli_init_choice_falls_back_without_tty(monkeypatch, tmp_path: Path) -> None:
    def fail_arrow_selector(*args, **kwargs):
        raise AssertionError("arrow selector should not run without a TTY")

    monkeypatch.setattr(cli_module, "_init_can_use_arrow_select", lambda: False)
    monkeypatch.setattr(cli_module, "_ask_init_arrow_choice", fail_arrow_selector)

    result = runner.invoke(app, ["init", str(tmp_path)], input="\n2\n\n")

    assert result.exit_code == 0, result.output
    parsed = yaml.safe_load((tmp_path / "docs.yaml").read_text(encoding="utf-8"))
    assert parsed["theme"]["preset"] == "beacon"


def test_cli_init_can_select_theme_preset(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)], input="\n2\n\n")

    assert result.exit_code == 0, result.output
    parsed = yaml.safe_load((tmp_path / "docs.yaml").read_text(encoding="utf-8"))
    assert parsed["theme"]["preset"] == "beacon"
    assert "landing" not in parsed


def test_cli_init_does_not_write_landing_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)], input="\n\n")

    assert result.exit_code == 0, result.output
    parsed = yaml.safe_load((tmp_path / "docs.yaml").read_text(encoding="utf-8"))
    assert "landing" not in parsed


def test_cli_init_prefills_detected_project_values(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'name = "aurora-labs"\n'
        'version = "1.8.4"\n'
        'dependencies = ["typer>=0.9"]\n',
        encoding="utf-8",
    )
    (tmp_path / "src" / "aurora_labs").mkdir(parents=True)

    result = runner.invoke(app, ["init", str(tmp_path)], input="\n\n\n")

    assert result.exit_code == 0, result.output
    parsed = yaml.safe_load((tmp_path / "docs.yaml").read_text(encoding="utf-8"))
    assert parsed["project"]["name"] == "aurora-labs"
    assert parsed["project"]["version"] == "1.8.4"
    assert parsed["source"]["python"]["paths"] == ["src/aurora_labs"]
    assert "Use detected project settings" not in result.output
    assert "Project name" not in result.output
    assert "Typer package" in result.output
    assert "Framework  ⚡" not in result.output


def test_cli_init_creates_github_pages_workflow(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output

    workflow_path = tmp_path / ".github" / "workflows" / "pages.yml"
    preview_workflow_path = tmp_path / ".github" / "workflows" / "branch-previews.yml"
    extra_workflow_path = tmp_path / ".github" / "workflows" / "folio-pages.yml"

    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    preview_workflow_text = preview_workflow_path.read_text(encoding="utf-8")
    preview_workflow = yaml.safe_load(preview_workflow_text)

    assert not extra_workflow_path.exists()
    assert workflow["name"] == "Deploy Docs"
    assert "env" not in workflow
    assert "github.event.repository.name" not in workflow_text
    assert "workflow_call" not in workflow["on"]
    assert workflow["permissions"] == {"contents": "read"}
    assert list(workflow["jobs"]) == ["build", "deploy"]
    assert workflow["concurrency"] == {
        "group": "pages",
        "cancel-in-progress": False,
    }

    steps = workflow["jobs"]["build"]["steps"]
    step_by_name = {step["name"]: step for step in steps if "name" in step}
    assert workflow["jobs"]["build"]["permissions"] == {
        "contents": "write",
        "pages": "write",
        "pull-requests": "read",
    }
    assert (
        step_by_name["Configure GitHub Pages"]["uses"] == "actions/configure-pages@v5"
    )
    assert step_by_name["Build docs"]["run"] == (
        "uv tool run --from folio-docs folio build --clean"
    )
    assert step_by_name["Build docs"]["env"] == {
        "FOLIO_BASE_PATH": "${{ steps.pages.outputs.base_path || '/' }}",
    }
    assert "folio-pages-state" in step_by_name["Preserve branch previews"]["run"]
    assert "previews" in step_by_name["Preserve branch previews"]["run"]
    assert (
        "folio github-pages preserve-previews"
        in step_by_name["Preserve branch previews"]["run"]
    )
    assert (
        "folio github-pages prune-previews"
        in step_by_name["Prune stale previews"]["run"]
    )
    assert "gh pr list --state open" in step_by_name["Prune stale previews"]["run"]
    assert (
        "folio github-pages write-previews-data"
        in step_by_name["Write previews data"]["run"]
    )
    assert "folio github-pages render-previews-index" not in workflow_text
    assert "folio github-pages save-state" in step_by_name["Save Pages state"]["run"]
    assert "folio-pages-state" in step_by_name["Save Pages state"]["run"]
    assert workflow["jobs"]["deploy"]["needs"] == "build"
    assert workflow["jobs"]["deploy"]["permissions"] == {
        "pages": "write",
        "id-token": "write",
    }
    deploy_step_text = "\n".join(
        str(step) for step in workflow["jobs"]["deploy"]["steps"]
    )
    assert "actions/deploy-pages@v4" in deploy_step_text
    assert "Verify and print deployment URL" in deploy_step_text
    assert "steps.deployment.outputs.page_url" in deploy_step_text
    assert "Previews index" in deploy_step_text
    assert "Verified deployment and previews index with HTTP 200" in deploy_step_text
    assert "folio github-pages verify-url" in deploy_step_text
    assert "python - <<'PY'" not in workflow_text
    assert "actions/upload-pages-artifact@v3" in workflow_text
    assert "actions/deploy-pages@v4" in workflow_text
    assert "actions/setup-python@v5" in workflow_text

    assert preview_workflow["name"] == "Deploy Branch Preview Docs"
    assert "push" not in preview_workflow["on"]
    assert preview_workflow["on"]["pull_request_target"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    ]
    assert "pull_request_review" not in preview_workflow["on"]
    assert preview_workflow["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
    }
    assert "concurrency" not in preview_workflow
    assert list(preview_workflow["jobs"]) == ["validate", "build-preview", "deploy"]

    preview_validate_job = preview_workflow["jobs"]["validate"]
    assert preview_validate_job["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
    }
    assert "enabled" in preview_validate_job["outputs"]
    assert "pr_number" in preview_validate_job["outputs"]
    assert "head_sha" in preview_validate_job["outputs"]
    assert "head_ref" in preview_validate_job["outputs"]

    preview_build_job = preview_workflow["jobs"]["build-preview"]
    assert preview_build_job["needs"] == "validate"
    assert preview_build_job["permissions"] == {"contents": "read"}
    preview_build_text = "\n".join(str(step) for step in preview_build_job["steps"])
    assert "Check out preview branch" in preview_build_text
    assert "persist-credentials': False" in preview_build_text
    assert "Configure GitHub Pages" not in preview_build_text
    assert "steps.pages.outputs" not in preview_build_text
    assert "GITHUB_OWNER" in preview_build_text
    assert "pages_base_path" in preview_build_text
    assert "Compute preview path" in preview_build_text
    assert "Build preview docs" in preview_build_text
    assert "uv tool run --from folio-docs folio build --clean" in preview_build_text
    assert "actions/upload-artifact@v4" in preview_workflow_text

    preview_job = preview_workflow["jobs"]["deploy"]
    assert preview_job["needs"] == ["validate", "build-preview"]
    assert preview_job["concurrency"] == {
        "group": "pages",
        "cancel-in-progress": False,
    }
    assert "environment" not in preview_job
    assert preview_job["permissions"] == {
        "contents": "write",
        "issues": "write",
        "pages": "write",
        "id-token": "write",
        "pull-requests": "write",
    }
    preview_step_text = "\n".join(str(step) for step in preview_job["steps"])
    assert "Revalidate preview PR" in preview_step_text
    assert 'gh api --method GET "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}"' in (
        preview_workflow_text
    )
    assert "head has not caught up" in preview_step_text
    assert "trusted approval" not in preview_step_text
    assert "author_association" not in preview_step_text
    assert "/reviews" not in preview_step_text
    assert "Check out production branch" in preview_step_text
    assert "Check out preview branch" not in preview_step_text
    assert "actions/download-artifact@v4" in preview_workflow_text
    assert "actions/configure-pages@v5" in preview_workflow_text
    assert "Compute preview path" in preview_step_text
    assert "Build production docs" in preview_step_text
    assert "Build preview docs" not in preview_step_text
    assert "folio-pages-state" in preview_step_text
    assert "folio github-pages prepare-artifact" in preview_step_text
    assert "folio github-pages copy-branch-preview" in preview_step_text
    assert "folio github-pages prune-previews" in preview_step_text
    assert "folio github-pages write-previews-data" in preview_step_text
    assert "folio github-pages render-previews-index" not in preview_workflow_text
    assert "folio github-pages save-state" in preview_step_text
    assert "folio github-pages verify-url" in preview_step_text
    assert "uv tool run --from folio-docs folio build --clean" in preview_step_text
    assert "FOLIO_BASE_PATH" in preview_step_text
    assert "python - <<'PY'" not in preview_workflow_text
    assert "actions/upload-pages-artifact@v3" in preview_workflow_text
    assert "actions/deploy-pages@v4" in preview_workflow_text
    assert "Verify and print preview URL" in preview_step_text
    assert "Comment preview URL" in preview_step_text
    assert "GH_TOKEN" in preview_step_text
    assert "folio github-pages comment-preview" in preview_step_text
    assert "--repo" in preview_step_text
    assert "--pr-number" in preview_step_text
    assert "--preview-url" in preview_step_text
    assert '--branch "$BRANCH"' in preview_step_text
    assert "Preview URL" in preview_step_text
    assert "Previews index" in preview_step_text
    assert "Verified preview and index with HTTP 200" in preview_step_text
    assert "CLOUDFLARE" not in preview_workflow_text
    assert "${{ github.event.pull_request.head.sha || github.sha }}" not in (
        preview_workflow_text
    )
    # Metadata sidecar (enriched with repo/author context) is written before
    # the previews data file that the site route consumes.
    assert "pr_title" in preview_validate_job["outputs"]
    assert "Write preview metadata" in preview_step_text
    assert "folio github-pages write-preview-metadata" in preview_step_text
    assert "--author" in preview_step_text
    assert "github.event.pull_request.user.avatar_url" in preview_workflow_text
    assert preview_step_text.index("write-preview-metadata") < (
        preview_step_text.index("write-previews-data")
    )

    # Cleanup is garbage collection on deploy, not a separate close-triggered
    # workflow, so no cleanup workflow file is generated.
    assert not (
        tmp_path / ".github" / "workflows" / "branch-preview-cleanup.yml"
    ).exists()
    assert "gh pr list --state open" in preview_workflow_text


def test_cli_init_preserves_existing_github_pages_workflow(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow_path = workflow_dir / "pages.yml"
    preview_workflow_path = workflow_dir / "branch-previews.yml"
    workflow_path.write_text("custom caller\n", encoding="utf-8")
    preview_workflow_path.write_text("custom preview caller\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output
    assert workflow_path.read_text(encoding="utf-8") == "custom caller\n"
    assert (
        preview_workflow_path.read_text(encoding="utf-8") == "custom preview caller\n"
    )
    assert not (workflow_dir / "folio-pages.yml").exists()


def test_cli_init_existing(tmp_path: Path) -> None:
    (tmp_path / "docs.yaml").write_text("existing")
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "docs.yaml").read_text() == "existing"


def test_cli_init_warns_when_pyproject_cannot_be_parsed(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output
    assert (
        "Warning: Could not read project metadata from pyproject.toml" in result.output
    )
    assert (tmp_path / "docs.yaml").exists()


def test_cli_init_warns_when_pyproject_metadata_has_wrong_type(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 123\nversion = true\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output
    assert (
        "Warning: Could not read project metadata from pyproject.toml" in result.output
    )
    assert f'name: "{tmp_path.name}"' in (tmp_path / "docs.yaml").read_text()


def test_cli_init_warns_when_git_remote_detection_fails(
    tmp_path: Path, monkeypatch
) -> None:
    def raise_os_error(*args, **kwargs):
        raise OSError("git unavailable")

    monkeypatch.setattr(cli_module.subprocess, "run", raise_os_error)

    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])

    assert result.exit_code == 0, result.output
    assert "Warning: Could not detect git remote: git unavailable" in result.output
    assert (tmp_path / "docs.yaml").exists()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "folio" in result.output.lower() or "Usage" in result.output


def _option_flags_from_click(command) -> dict[str, set[str]]:
    options: dict[str, set[str]] = {}
    for param in command.params:
        if getattr(param, "hidden", False):
            continue
        opts = {
            opt
            for opt in getattr(param, "opts", [])
            if isinstance(opt, str) and opt.startswith("-")
        }
        if opts:
            long_opt = next(opt for opt in opts if opt.startswith("--"))
            options[long_opt] = opts
    return options


def _doc_section(text: str, heading: str) -> str:
    start = text.index(heading)
    next_heading = text.find("\n##", start + len(heading))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def _documented_option_flags(section: str) -> dict[str, set[str]]:
    options: dict[str, set[str]] = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        flags = set(re.findall(r"`(-{1,2}[^`]+)`", f"{cells[0]} {cells[1]}"))
        flags.discard("--help")
        if not flags:
            continue
        long_flags = sorted(flag for flag in flags if flag.startswith("--"))
        if long_flags:
            options[long_flags[0]] = flags
    return options


def test_cli_reference_documents_current_typer_commands_and_options() -> None:
    docs = CLI_DOC.read_text(encoding="utf-8")
    click_app = get_command(app)
    command_names = {
        name for name, command in click_app.commands.items() if not command.hidden
    }
    documented_commands = set(re.findall(r"^### `folio ([^`]+)`", docs, re.MULTILINE))

    assert documented_commands == command_names

    global_docs = _doc_section(docs, "## Global Options")
    assert _documented_option_flags(global_docs) == _option_flags_from_click(click_app)

    for command_name, command in click_app.commands.items():
        if command.hidden:
            continue
        section = _doc_section(docs, f"### `folio {command_name}`")
        assert _documented_option_flags(section) == _option_flags_from_click(command)


def test_build_open_help_mentions_blocking_static_preview() -> None:
    click_app = get_command(app)
    open_option = _option_flags_from_click(click_app.commands["build"])["--open"]

    assert "-o" in open_option
    for param in click_app.commands["build"].params:
        if "--open" in getattr(param, "opts", []):
            assert "static preview" in param.help
            assert "blocks until interrupted" in param.help
            break
    else:
        raise AssertionError("Expected build command to define --open")


def test_generate_docs_yaml_places_docstring_style_under_source_python() -> None:
    raw = _generate_docs_yaml(
        {
            "name": "Demo",
            "version": "0.1.0",
            "python_path": "src/demo",
            "docstring_style": "numpy",
        }
    )

    parsed = yaml.safe_load(raw)

    assert parsed["source"]["python"]["docstring_style"] == "numpy"
    assert "docstring_style" not in parsed["project"]


def test_cli_roadmap_reports_missing_phases(tmp_path: Path) -> None:
    # No plugins: entry — the roadmap plugin is a first-party default plugin.
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nroadmap:\n  phases: []\n'
    )

    result = runner.invoke(app, ["roadmap", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "No roadmap phases configured" in result.output


def test_cli_roadmap_lists_configured_phases(tmp_path: Path) -> None:
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "roadmap:\n"
        "  phases:\n"
        '    - id: "foundation"\n'
        '      version: "0.1"\n'
        '      title: "Foundation"\n'
        '      status: "shipped"\n'
        '      layer: "Source analysis"\n'
        '      summary: "Parse source files into docs."\n'
        '      command: "folio build"\n'
        "      features:\n"
        '        - "Parser"\n'
    )

    result = runner.invoke(app, ["roadmap", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Demo Roadmap" in result.output
    assert "Foundation" in result.output
    assert "shipped" in result.output
    assert "folio build" in result.output


def test_cli_roadmap_accepts_project_directory_argument(tmp_path: Path) -> None:
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "roadmap:\n"
        "  phases:\n"
        '    - id: "foundation"\n'
        '      version: "0.1"\n'
        '      title: "Foundation"\n'
        '      status: "shipped"\n'
        '      layer: "Source analysis"\n'
        '      summary: "Parse source files into docs."\n'
        "      features:\n"
        '        - "Parser"\n'
    )

    result = runner.invoke(app, ["roadmap", str(tmp_path)])

    assert result.exit_code == 0
    assert "Foundation" in result.output


def test_cli_kanban_reports_missing_columns(tmp_path: Path) -> None:
    # No plugins: entry — the kanban plugin is a first-party default plugin.
    (tmp_path / "docs.yaml").write_text('project:\n  name: "Demo"\n')

    result = runner.invoke(app, ["kanban", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "No kanban columns configured" in result.output


def test_cli_kanban_lists_configured_board(tmp_path: Path) -> None:
    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True)
    (board / "board.yaml").write_text(
        'title: "Project Board"\n'
        "columns:\n"
        "  - id: todo\n"
        "    title: To Do\n"
        "    limit: 4\n"
        "  - id: done\n"
        "    title: Done\n"
    )
    (board / "cards" / "ship-kanban-plugin.md").write_text(
        "---\n"
        "title: Ship kanban plugin\n"
        "status: todo\n"
        "assignee: pedro\n"
        "tags: [plugins]\n"
        "---\n"
    )
    (board / "cards" / "another-card.md").write_text(
        "---\n"
        "title: Another card\n"
        "status: done\n"
        "tags: [docs]\n"
        "---\n"
    )
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nkanban:\n  source: board\n'
    )

    result = runner.invoke(app, ["kanban", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Demo Project Board" in result.output
    assert "To Do (1/4)" in result.output
    assert "Ship kanban plugin" in result.output
    assert "pedro" in result.output
    assert "plugins" in result.output
    assert "Done (1)" in result.output


def test_cli_build_missing_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path)])
    assert result.exit_code != 0


def test_cli_build_accepts_project_directory_argument(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n'
    )
    calls = []

    def fake_run_build(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(app, ["build", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            (tmp_path.resolve(),),
            {
                "serve": False,
                "verbose": False,
                "config_file": "docs.yaml",
                "clean": False,
                "include_versions": False,
            },
        )
    ]


def test_cli_build_rejects_conflicting_project_directory_inputs(tmp_path: Path) -> None:
    other = tmp_path / "other"

    result = runner.invoke(app, ["build", str(tmp_path), "--project-dir", str(other)])

    assert result.exit_code == 1
    assert (
        "Pass the project directory either as an argument or --project-dir"
        in result.output
    )


def test_cli_build_does_not_swallow_unexpected_build_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def raise_unexpected_error(*args, **kwargs):
        raise AssertionError("build invariant bug")

    monkeypatch.setattr(build_module, "run_build", raise_unexpected_error)

    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert isinstance(result.exception, AssertionError)
    assert str(result.exception) == "build invariant bug"


def test_cli_build_reports_plugin_hook_failures_as_build_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A fail-fast plugin failure renders as a clean 'Build failed:' message."""
    from folio.plugin import PluginHookError

    def raise_plugin_hook_error(*args, **kwargs):
        raise PluginHookError("my-plugin", "configure", ValueError("bad source"))

    monkeypatch.setattr(build_module, "run_build", raise_plugin_hook_error)

    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "Build failed:" in result.output
    assert "my-plugin" in result.output


def test_cli_build_failure_output_survives_rich_markup_in_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Errors containing bracketed text (pnpm/Next output looks like rich
    markup) must render as a clean message, never crash markup parsing."""

    def raise_bracketed_error(*args, **kwargs):
        raise RuntimeError(
            "pnpm install failed:\n"
            " ERR_PNPM [/private/tmp/x] mismatched closing tag [/bold red] here"
        )

    monkeypatch.setattr(build_module, "run_build", raise_bracketed_error)

    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "Build failed:" in result.output
    assert "ERR_PNPM" in result.output
    assert "MarkupError" not in result.output


def _write_cli_plugin_project(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "cli_plugin.py").write_text(
        "from folio.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def register_cli(app):\n"
        "    @app.command(name='glossary')\n"
        "    def glossary() -> None:\n"
        "        pass\n",
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "PluginProject"\n'
        "\n"
        "plugins:\n"
        '  - "./plugins/cli_plugin.py"\n',
        encoding="utf-8",
    )


def test_project_plugins_register_cli_commands_from_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_cli_plugin_project(tmp_path)
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)
    monkeypatch.chdir(tmp_path)

    test_app = typer.Typer()
    pm = cli_module._load_project_cli_plugins(test_app)

    assert pm is not None
    assert any(command.name == "glossary" for command in test_app.registered_commands)


def test_project_plugins_cli_dispatch_skips_without_project_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)
    monkeypatch.chdir(tmp_path)

    assert cli_module._load_project_cli_plugins(typer.Typer()) is None


def test_project_plugins_cli_dispatch_warns_on_broken_plugin(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A broken project plugin must never take down the whole CLI."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "broken_plugin.py").write_text(
        "raise RuntimeError('broken at import')\n",
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "PluginProject"\n'
        "\n"
        "plugins:\n"
        '  - "./plugins/broken_plugin.py"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.warns(UserWarning, match="Skipping project plugin CLI commands"):
        assert cli_module._load_project_cli_plugins(typer.Typer()) is None


def test_cli_build_defaults_to_single_version_when_versions_are_configured(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1"\n'
        '    path: "v0.1"\n'
    )
    calls = []

    def fake_run_build(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            (tmp_path.resolve(),),
            {
                "serve": False,
                "verbose": False,
                "config_file": "docs.yaml",
                "clean": False,
                "include_versions": False,
            },
        )
    ]


def test_cli_serve_missing_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["serve", "--project-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "Config file not found" in result.output


def test_cli_serve_accepts_project_directory_argument(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n'
    )
    calls = []

    def fake_run_build(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(app, ["serve", str(tmp_path), "--port", "5678"])

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            (tmp_path.resolve(),),
            {
                "serve": True,
                "verbose": False,
                "config_file": "docs.yaml",
                "port": 5678,
                "open_browser": False,
                "clean": False,
                "include_versions": False,
                "kill_existing": False,
            },
        )
    ]


def test_cli_build_versions_is_disabled_in_mvp(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )
    calls = []
    monkeypatch.setattr(
        build_module,
        "run_build",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert calls == []
    assert "The 'versions' feature is not available in this release" in result.output


def test_cli_build_versions_clean_removes_stale_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "1.0.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )
    stale_file = tmp_path / "_site" / "stale.html"
    stale_file.parent.mkdir()
    stale_file.write_text("old")

    def fake_run_build(*args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        (output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path), "--clean"],
    )

    assert result.exit_code == 0, result.output
    assert not stale_file.exists()
    assert (tmp_path / "_site" / "latest" / "index.html").exists()


def test_cli_build_versions_without_clean_preserves_other_version_outputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "1.0.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )
    old_version_file = tmp_path / "_site" / "v0.1" / "index.html"
    old_version_file.parent.mkdir(parents=True)
    old_version_file.write_text("old version")

    def fake_run_build(*args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        (output_dir / "index.html").write_text("latest")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert old_version_file.read_text() == "old version"
    assert (tmp_path / "_site" / "latest" / "index.html").read_text() == "latest"


def test_cli_build_versions_writes_default_version_redirect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "1.0.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )

    def fake_run_build(*args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        (output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    redirect = tmp_path / "_site" / "index.html"
    assert result.exit_code == 0, result.output
    assert redirect.exists()
    assert "url=latest/" in redirect.read_text()


def test_cli_build_versions_enables_version_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1"\n'
        '    path: "v0.1"\n'
    )
    calls = []

    def fake_run_build(*args, output_override, **kwargs):
        calls.append((output_override, kwargs))
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        (output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            str(tmp_path / "_site" / "latest"),
            {
                "serve": False,
                "verbose": False,
                "config_file": "docs.yaml",
                "clean": False,
                "current_version_path": "latest",
                "source_ref_override": "",
                "include_versions": True,
            },
        ),
        (
            str(tmp_path / "_site" / "v0.1"),
            {
                "serve": False,
                "verbose": False,
                "config_file": "docs.yaml",
                "clean": False,
                "current_version_path": "v0.1",
                "source_ref_override": "",
                "include_versions": True,
            },
        ),
    ]


def test_cli_build_versions_reuses_cached_historical_version(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "version.txt").write_text("old tagged docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "0.1.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
    )
    git("init")
    git("add", "docs.yaml", "docs/version.txt")
    git(
        "-c",
        "user.name=Folio Test",
        "-c",
        "user.email=folio@example.com",
        "commit",
        "-m",
        "docs: old version",
    )
    git("tag", "v0.1.0")
    old_commit = git("rev-parse", "v0.1.0^{commit}")

    versions = [
        {"label": "latest", "path": "latest"},
        {"label": "v0.1.0", "path": "v0.1", "ref": "v0.1.0"},
    ]
    (tmp_path / "docs" / "version.txt").write_text("current working tree docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "0.2.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1.0"\n'
        '    path: "v0.1"\n'
        '    ref: "v0.1.0"\n'
    )
    cached_output = tmp_path / "_site" / "v0.1"
    cached_output.mkdir(parents=True)
    (cached_output / "version.txt").write_text("cached old docs")
    (cached_output / ".folio-version.json").write_text(
        json.dumps(
            _version_manifest(
                label="v0.1.0",
                path="v0.1",
                ref="v0.1.0",
                commit=old_commit,
                versions=versions,
                synced_config={"plugins": []},
            ),
            indent=2,
        )
    )
    calls = []

    def fake_run_build(source_dir, *args, output_override, **kwargs):
        calls.append((Path(source_dir), Path(output_override), kwargs))
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True, exist_ok=True)
        marker = Path(source_dir) / "docs" / "version.txt"
        (output_dir / "version.txt").write_text(marker.read_text())

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0][1] == tmp_path / "_site" / "latest"
    assert calls[0][2]["current_version_path"] == "latest"
    assert (
        tmp_path / "_site" / "v0.1" / "version.txt"
    ).read_text() == "cached old docs"
    assert "Reusing version: v0.1.0" in result.output
    assert not (tmp_path / ".build" / "worktrees" / "v0.1").exists()


def test_cli_build_versions_writes_manifest_for_built_versions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "version.txt").write_text("old tagged docs")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\n'
    )
    git("init")
    git("add", "docs.yaml", "docs/version.txt")
    git(
        "-c",
        "user.name=Folio Test",
        "-c",
        "user.email=folio@example.com",
        "commit",
        "-m",
        "docs: old version",
    )
    git("tag", "v0.1.0")
    old_commit = git("rev-parse", "v0.1.0^{commit}")

    versions = [
        {"label": "latest", "path": "latest"},
        {"label": "v0.1.0", "path": "v0.1", "ref": "v0.1.0"},
    ]
    (tmp_path / "docs" / "version.txt").write_text("current working tree docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1.0"\n'
        '    path: "v0.1"\n'
        '    ref: "v0.1.0"\n'
    )

    def fake_run_build(source_dir, *args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True, exist_ok=True)
        marker = Path(source_dir) / "docs" / "version.txt"
        (output_dir / "version.txt").write_text(marker.read_text())

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (tmp_path / "_site" / "v0.1" / ".folio-version.json").read_text()
    )
    assert manifest == _version_manifest(
        label="v0.1.0",
        path="v0.1",
        ref="v0.1.0",
        commit=old_commit,
        versions=versions,
        synced_config={"plugins": []},
    )


def test_cli_build_versions_fails_when_configured_version_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "1.0.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "missing"\n'
        '    path: "missing"\n'
        '    ref: "missing-tag"\n'
    )

    def fake_run_build(*args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        (output_dir / "index.html").write_text("latest")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 1, result.output
    assert "Failed to checkout ref 'missing-tag'" in result.output
    assert "missing" in result.output
    assert "missing-tag" in result.output
    assert str(tmp_path / "_site" / "missing") in result.output
    assert "Version build failed" in result.output
    assert "All versions built" not in result.output


def test_cli_build_versions_reports_build_failure_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "broken"\n'
        '    path: "v-broken"\n'
    )

    def fake_run_build(*args, **kwargs):
        raise RuntimeError("template failed")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 1, result.output
    assert "broken" in result.output
    assert str(tmp_path / "_site" / "v-broken") in result.output
    assert "template failed" in result.output


def test_cli_build_versions_does_not_swallow_unexpected_build_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )

    def raise_unexpected_error(*args, **kwargs):
        raise AssertionError("version build invariant bug")

    monkeypatch.setattr(build_module, "run_build", raise_unexpected_error)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert isinstance(result.exception, AssertionError)
    assert str(result.exception) == "version build invariant bug"


def test_cli_build_versions_uses_tagged_mock_version(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "version.txt").write_text("old tagged docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "0.1.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
    )
    git("init")
    git("add", "docs.yaml", "docs/version.txt")
    git(
        "-c",
        "user.name=Folio Test",
        "-c",
        "user.email=folio@example.com",
        "commit",
        "-m",
        "docs: old version",
    )
    git("tag", "v0.1.0")

    (tmp_path / "docs" / "version.txt").write_text("current working tree docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "0.2.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1.0"\n'
        '    path: "v0.1"\n'
        '    ref: "v0.1.0"\n'
    )

    def fake_run_build(source_dir, *args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        marker = Path(source_dir) / "docs" / "version.txt"
        (output_dir / "version.txt").write_text(marker.read_text())
        version_labels = [
            version["label"]
            for version in load_config(Path(source_dir) / "docs.yaml").versions
        ]
        (output_dir / "versions.txt").write_text("\n".join(version_labels))
        (output_dir / "current-version.txt").write_text(kwargs["current_version_path"])
        (output_dir / "source-ref.txt").write_text(kwargs["source_ref_override"])

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert (
        tmp_path / "_site" / "latest" / "version.txt"
    ).read_text() == "current working tree docs"
    assert (
        tmp_path / "_site" / "v0.1" / "version.txt"
    ).read_text() == "old tagged docs"
    assert (
        tmp_path / "_site" / "latest" / "versions.txt"
    ).read_text() == "latest\nv0.1.0"
    assert (
        tmp_path / "_site" / "v0.1" / "versions.txt"
    ).read_text() == "latest\nv0.1.0"
    assert (
        tmp_path / "_site" / "latest" / "current-version.txt"
    ).read_text() == "latest"
    assert (tmp_path / "_site" / "v0.1" / "current-version.txt").read_text() == "v0.1"
    assert (tmp_path / "_site" / "latest" / "source-ref.txt").read_text() == ""
    assert (tmp_path / "_site" / "v0.1" / "source-ref.txt").read_text() == "v0.1.0"
    assert "url=latest/" in (tmp_path / "_site" / "index.html").read_text()
    assert not (tmp_path / ".build" / "worktrees" / "v0.1").exists()


def test_cli_build_versions_prunes_stale_worktree_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "version.txt").write_text("old tagged docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "0.1.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
    )
    git("init")
    git("add", "docs.yaml", "docs/version.txt")
    git(
        "-c",
        "user.name=Folio Test",
        "-c",
        "user.email=folio@example.com",
        "commit",
        "-m",
        "docs: old version",
    )
    git("tag", "v0.1.0")

    (tmp_path / "docs" / "version.txt").write_text("current working tree docs")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "0.2.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1.0"\n'
        '    path: "v0.1"\n'
        '    ref: "v0.1.0"\n'
    )
    stale_worktree = tmp_path / ".build" / "worktrees" / "v0.1"
    git("worktree", "add", str(stale_worktree), "v0.1.0")
    shutil.rmtree(stale_worktree)

    def fake_run_build(source_dir, *args, output_override, **kwargs):
        output_dir = Path(output_override)
        output_dir.mkdir(parents=True)
        marker = Path(source_dir) / "docs" / "version.txt"
        (output_dir / "version.txt").write_text(marker.read_text())

    monkeypatch.setattr(build_module, "run_build", fake_run_build)

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert (
        tmp_path / "_site" / "v0.1" / "version.txt"
    ).read_text() == "old tagged docs"
    assert not stale_worktree.exists()


def test_cli_build_versions_rejects_version_output_outside_project(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    outside_dir = tmp_path.parent / f"{tmp_path.name}-version-output"
    outside_dir.mkdir()
    (outside_dir / "keep.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        f'    path: "../{outside_dir.name}"\n',
        encoding="utf-8",
    )
    calls = []

    monkeypatch.setattr(
        build_module,
        "run_build",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    result = runner.invoke(
        app,
        ["build-versions", "--project-dir", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert calls == []
    assert outside_dir.exists()
    assert (outside_dir / "keep.txt").exists()
    assert "Version output path" in result.output


def test_sync_version_matrix_includes_current_plugins_and_plugin_config(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "docs.yaml"
    config_path.write_text(
        "project:\n"
        '  name: "Historical"\n'
        '  version: "0.1.0"\n'
        "plugins:\n"
        '  - "old.plugin"\n'
        "roadmap:\n"
        "  phases: []\n"
        "versions:\n"
        '  - label: "old"\n'
        '    path: "old"\n'
    )
    versions = [{"label": "latest", "path": "latest"}]
    plugin_config = {
        "plugins": ["folio.plugins.roadmap"],
        "roadmap": {
            "routes": {"docs": True, "public": True},
            "phases": [{"id": "current", "title": "Current"}],
        },
    }

    _sync_version_matrix(config_path, versions, plugin_config)

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert raw["project"]["version"] == "0.1.0"
    assert raw["versions"] == versions
    assert raw["plugins"] == ["folio.plugins.roadmap"]
    assert raw["roadmap"] == plugin_config["roadmap"]


def test_cli_serve_defaults_to_current_version_when_versions_are_configured(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "1.0.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1"\n'
        '    path: "v0.1"\n'
        '    ref: "v0.1.0"\n'
    )
    calls = []

    def fake_run_build(*args, **kwargs):
        calls.append(("run_build", args, kwargs))

    def fail_build_versions(**kwargs):
        raise AssertionError("multi-version static preview should be opt-in")

    def fail_serve_static_site(*args, **kwargs):
        raise AssertionError("static version preview should be opt-in")

    monkeypatch.setattr(build_module, "run_build", fake_run_build)
    monkeypatch.setattr(
        cli_module,
        "_build_configured_versions",
        fail_build_versions,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "_serve_static_site",
        fail_serve_static_site,
        raising=False,
    )

    result = runner.invoke(
        app, ["serve", "--project-dir", str(tmp_path), "--port", "5678"]
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            "run_build",
            (tmp_path.resolve(),),
            {
                "serve": True,
                "verbose": False,
                "config_file": "docs.yaml",
                "port": 5678,
                "open_browser": False,
                "clean": False,
                "include_versions": False,
                "kill_existing": False,
            },
        )
    ]
    assert "Serving current version only" not in result.output
    assert "Use --versions for all versions" not in result.output


def test_cli_serve_versions_is_disabled_in_mvp(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )
    calls = []

    monkeypatch.setattr(
        cli_module,
        "_build_configured_versions",
        lambda **kwargs: calls.append(("build_versions", kwargs)),
        raising=False,
    )

    result = runner.invoke(
        app,
        [
            "serve",
            "--project-dir",
            str(tmp_path),
            "--port",
            "5678",
            "--versions",
        ],
    )

    assert result.exit_code == 1
    assert calls == []
    assert "The 'versions' feature is not available in this release" in result.output


def test_cli_serve_versions_builds_and_serves_configured_versions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "1.0.0"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1"\n'
        '    path: "v0.1"\n'
        '    ref: "v0.1.0"\n'
    )
    calls = []

    def fail_run_build(*args, **kwargs):
        raise AssertionError("single-version dev server should not run")

    def fake_build_versions(**kwargs):
        calls.append(("build_versions", kwargs))

    def fake_serve_static_site(site_dir, port, open_browser, kill_existing):
        calls.append(("serve_static", site_dir, port, open_browser, kill_existing))

    monkeypatch.setattr(build_module, "run_build", fail_run_build)
    monkeypatch.setattr(
        cli_module,
        "_build_configured_versions",
        fake_build_versions,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "_serve_static_site",
        fake_serve_static_site,
        raising=False,
    )

    result = runner.invoke(
        app,
        ["serve", "--project-dir", str(tmp_path), "--port", "5678", "--versions"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            "build_versions",
            {
                "project_dir": tmp_path.resolve(),
                "verbose": False,
                "config": "docs.yaml",
                "clean": False,
            },
        ),
        ("serve_static", tmp_path.resolve() / "_site", 5678, False, False),
    ]


def test_cli_serve_versions_kills_existing_port_only_when_requested(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _enable_disabled_features(monkeypatch)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
    )
    calls = []

    def fake_build_versions(**kwargs):
        calls.append(("build_versions", kwargs))

    def fake_serve_static_site(site_dir, port, open_browser, kill_existing):
        calls.append(("serve_static", site_dir, port, open_browser, kill_existing))

    monkeypatch.setattr(
        cli_module,
        "_build_configured_versions",
        fake_build_versions,
        raising=False,
    )
    monkeypatch.setattr(
        cli_module,
        "_serve_static_site",
        fake_serve_static_site,
        raising=False,
    )

    result = runner.invoke(
        app,
        [
            "serve",
            "--project-dir",
            str(tmp_path),
            "--versions",
            "--kill-existing",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[-1] == (
        "serve_static",
        tmp_path.resolve() / "_site",
        4321,
        False,
        True,
    )


def test_cli_clean_ignores_broken_plugins_and_uses_raw_output(
    tmp_path: Path,
) -> None:
    build_dir = tmp_path / ".build"
    output_dir = tmp_path / "public"
    build_dir.mkdir()
    output_dir.mkdir()
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nplugins:\n  - "missing_plugin"\noutput: "public"\n'
    )

    result = runner.invoke(app, ["clean", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert not build_dir.exists()
    assert not output_dir.exists()
    assert "Cleaned: .build, public" in result.output


def test_cli_clean_does_not_swallow_unexpected_output_parse_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\noutput: "public"\n',
        encoding="utf-8",
    )

    def raise_unexpected_error(*args, **kwargs):
        raise RuntimeError("yaml loader bug")

    monkeypatch.setattr(yaml, "safe_load", raise_unexpected_error)

    result = runner.invoke(app, ["clean", "--project-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "yaml loader bug"


def test_cli_clean_does_not_remove_output_outside_project(tmp_path: Path) -> None:
    build_dir = tmp_path / ".build"
    outside_dir = tmp_path.parent / f"{tmp_path.name}-outside-output"
    build_dir.mkdir()
    outside_dir.mkdir()
    (outside_dir / "keep.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        f'project:\n  name: "Demo"\noutput: "../{outside_dir.name}"\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["clean", "--project-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert not build_dir.exists()
    assert outside_dir.exists()
    assert (outside_dir / "keep.txt").exists()
    assert "Ignoring unsafe output" in result.output


def test_cli_build_open_warns_that_static_preview_blocks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "docs.yaml").write_text('project:\n  name: "Demo"\noutput: "_site"\n')
    calls = []

    def fake_run_build(*args, **kwargs):
        calls.append(("run_build", args, kwargs))

    def fake_serve_and_open(site_dir):
        calls.append(("serve_and_open", site_dir))

    monkeypatch.setattr(build_module, "run_build", fake_run_build)
    monkeypatch.setattr(cli_module, "_serve_and_open", fake_serve_and_open)

    result = runner.invoke(app, ["build", "--project-dir", str(tmp_path), "--open"])

    assert result.exit_code == 0, result.output
    assert "static preview server" in result.output
    assert "blocks until interrupted" in result.output
    assert calls[-1] == ("serve_and_open", tmp_path.resolve() / "_site")


def test_init_without_python_sources_writes_a_commented_block(tmp_path: Path) -> None:
    """A repo with no Python gets a config that says so: the python block
    arrives commented out (documentation, not a claim), the API Reference
    nav entry stays out, and the first build carries no source warning."""
    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])
    assert result.exit_code == 0, result.output
    config = (tmp_path / "docs.yaml").read_text(encoding="utf-8")
    assert "  # python:" in config
    assert '  #   paths:' in config
    assert '\n  python:\n' not in config
    assert '"API Reference"' not in config
    assert '"Introduction"' in config


def test_init_with_src_keeps_the_python_block(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    result = runner.invoke(app, ["init", str(tmp_path), "--yes"])
    assert result.exit_code == 0, result.output
    config = (tmp_path / "docs.yaml").read_text(encoding="utf-8")
    assert '  python:\n    paths:\n      - "src/"' in config
    assert '"API Reference"' in config
