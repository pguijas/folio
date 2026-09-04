from __future__ import annotations

import io
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
import warnings
import webbrowser
from pathlib import Path

import typer
import yaml
from rich.align import Align
from rich.cells import cell_len
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.markup import escape

from folio import __version__
from folio.branding import (
    FOLIO_LOGO_STYLE,
    FOLIO_NEWS_STYLE,
    current_folio_news_item,
    folio_banner,
    folio_news_line,
)
from folio.config import DEFAULT_DOCSTRING_STYLE, plugin_config_keys, resolve_output_dir
from folio.features import disabled_feature_message, is_feature_enabled
from folio._github_pages import app as github_pages_app
from folio.generator.next_runtime import preflight_check
from folio.plugin import DEFAULT_PLUGINS, PluginHookError, PluginManager
from folio.workflows import github_pages_workflows

app = typer.Typer(
    name="folio",
    help="Open-source documentation for the agent era. Builds a static site with llms.txt and Markdown mirrors from your repo.",
    no_args_is_help=True,
)
app.add_typer(github_pages_app, name="github-pages", hidden=True)
console = Console()

_CONFIG_READ_ERRORS = (OSError, UnicodeDecodeError, yaml.YAMLError)
_BUILD_FAILURE_ERRORS = (
    OSError,
    UnicodeDecodeError,
    ValueError,
    RuntimeError,
    subprocess.SubprocessError,
    yaml.YAMLError,
    PluginHookError,
)

# First-party default plugins register their CLI commands through the
# register_cli hook, the same surface third-party plugins use. They are loaded
# in every install, project config or not. load_default_plugins degrades a
# load failure to a warning: this runs at import time, and a broken default
# plugin must never take down the whole CLI (not even `folio --help`).
_builtin_cli_plugins = PluginManager()
_builtin_cli_plugins.load_default_plugins()
_builtin_cli_plugins.call_isolated("register_cli", policy="warn_skip", app=app)


def _load_project_cli_plugins(cli_app: typer.Typer) -> PluginManager | None:
    """Dispatch ``register_cli`` for plugins listed in ``./docs.yaml``.

    Typer finalizes the command table when this module is imported — before
    any command (and its project-directory argument) is parsed — so project
    plugins can only contribute CLI commands when the project config is
    resolvable from the current working directory. Running ``folio`` from
    outside the project still loads project plugins for build hooks; only
    their extra CLI commands require running inside the project. Every
    failure degrades to a warning: a broken plugin must never take down the
    whole CLI.
    """
    config_path = Path.cwd() / "docs.yaml"
    if not config_path.is_file():
        return None
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except _CONFIG_READ_ERRORS:
        return None
    if not isinstance(raw, dict):
        return None
    raw_plugins = raw.get("plugins", [])
    if not isinstance(raw_plugins, list):
        return None
    # First-party default CLI plugins already dispatched above must not
    # register their commands twice when a project also lists them in
    # `plugins:`.
    plugin_names = [
        name
        for name in raw_plugins
        if isinstance(name, str) and name not in DEFAULT_PLUGINS
    ]
    if not plugin_names:
        return None
    pm = PluginManager(base_dir=config_path.parent)
    try:
        pm.load_plugins(plugin_names, base_dir=config_path.parent)
    except Exception as exc:
        warnings.warn(f"Skipping project plugin CLI commands: {exc}")
        return None
    pm.call_isolated("register_cli", policy="warn_skip", app=cli_app)
    return pm


_project_cli_plugins = _load_project_cli_plugins(app)
_VERSION_MANIFEST = ".folio-version.json"
_INIT_DOCSTRING_STYLES = (
    ("google", "Google", "Google-style Args, Returns, and Raises sections."),
    ("numpy", "NumPy", "NumPy/SciPy-style parameter tables."),
    ("auto", "Auto-detect", "Let Folio choose the parser."),
)
_INIT_THEME_PRESETS = (
    (
        "organic-editorial",
        "Organic Editorial",
        "Warm editorial docs with rich backgrounds.",
    ),
    ("beacon", "Beacon", "Bright product docs with clear contrast."),
    ("atlas", "Atlas", "Structured reference docs with dense navigation."),
    ("workshop", "Workshop", "Practical technical docs with compact rhythm."),
)
_INIT_SECTION_STYLES = {
    "detected_border": "#bfdbfe",
    "detected_label": "bold #fbbf24",
    "detected_value": "#f8fafc",
    "banner_logo": FOLIO_LOGO_STYLE,
    "banner_news": FOLIO_NEWS_STYLE,
    "docstring": "bold #a78bfa",
    "theme": "bold #f472b6",
    "success": "bold #22c55e",
    "files": "bold #60a5fa",
    "commands": "bold #f59e0b",
    "command": "bold #38bdf8",
    "ready_border": "#a78bfa",
}
_DETECTED_LABEL_STYLES = {
    "Target": "bold #fb7185",
    "Project": "bold #fbbf24",
    "Source": "bold #c084fc",
    "Repo": "bold #38bdf8",
    "Python": "bold #bef264",
    "Framework": "bold #a78bfa",
    "Status": "bold #fde68a",
}
_INIT_PROMPT_TITLES = (
    "Docstring style",
    "Visual preset",
)
_INIT_PROMPT_TITLE_WIDTH = max(cell_len(title) for title in _INIT_PROMPT_TITLES)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
ACCENT = "\033[38;5;147m"
GREEN = "\033[32m"
CLEAR_LINE = "\033[2K"
CURSOR_UP = "\033[1A"
SAVE_CURSOR = "\0337"
RESTORE_CURSOR = "\0338"
_INIT_NEWS_REFRESH_SECONDS = 1.0
_TERMINAL_DRAW_LOCK = threading.RLock()
_ACTIVE_INIT_INTRO_TICKER: "_InitIntroTicker | None" = None


def _resolve_project_target(directory: Path | None, project_dir: Path | None) -> Path:
    if directory is not None and project_dir is not None:
        directory_path = directory.resolve()
        project_dir_path = project_dir.resolve()
        if directory_path != project_dir_path:
            console.print(
                "[red]Error: Pass the project directory either as an argument "
                "or --project-dir, not both.[/red]"
            )
            raise typer.Exit(1)

    return (project_dir or directory or Path.cwd()).resolve()


def _format_cli_path(target: Path) -> str:
    cwd = Path.cwd().resolve()
    target = target.resolve()
    relative = Path(os.path.relpath(target, cwd))
    return relative.as_posix() or "."


def _command_target_suffix(target: Path) -> str:
    if target == Path.cwd().resolve():
        return ""
    return f" {shlex.quote(_format_cli_path(target))}"


def _exit_if_feature_disabled(feature: str) -> None:
    if is_feature_enabled(feature):
        return
    console.print(f"[yellow]{disabled_feature_message(feature)}[/yellow]")
    raise typer.Exit(1)


def _detected_label_spacer(label: str, label_width: int) -> str:
    return " " * (label_width - len(label) + 2)


def _detected_summary_body(info: dict, target: Path, repo: str) -> Text:
    rows = (
        ("Target", _format_cli_path(target)),
        ("Project", f"{info['name']} {info['version']}"),
        ("Source", info["python_path"] or "no Python detected"),
        ("Repo", repo or "not detected"),
        ("Python", info["python_version"]),
        ("Framework", info["framework"]),
        ("Status", info["status"]),
    )
    label_width = max(len(label) for label, _value in rows)
    body = Text()
    for index, (label, value) in enumerate(rows):
        body.append(
            label,
            style=_DETECTED_LABEL_STYLES.get(
                label,
                _INIT_SECTION_STYLES["detected_label"],
            ),
        )
        body.append(_detected_label_spacer(label, label_width))
        body.append(str(value), style=_INIT_SECTION_STYLES["detected_value"])
        if index < len(rows) - 1:
            body.append("\n")
    return body


def _print_init_intro(
    info: dict,
    target: Path,
    repo: str,
    *,
    compact: bool = False,
    news_item: str | None = None,
) -> tuple[int, str]:
    del compact
    selected_news_item = (
        news_item if news_item is not None else current_folio_news_item()
    )
    console.print()
    renderable = _init_intro_renderable(
        info,
        target,
        repo,
        news_item=selected_news_item,
    )
    rows_below_news = _cursor_rows_below_news(renderable)
    console.print(renderable)
    return rows_below_news, selected_news_item


def _init_intro_renderable(
    info: dict,
    target: Path,
    repo: str,
    *,
    news_item: str | None = None,
) -> Group:
    return Group(
        Text.from_markup(
            folio_banner(
                f"v{__version__}",
                width=console.width,
                news_item=news_item,
            )
        ),
        "",
        Align.center(
            Panel(
                _detected_summary_body(info, target, repo),
                title="Detected",
                border_style=_INIT_SECTION_STYLES["detected_border"],
                expand=False,
            )
        ),
    )


def _renderable_plain_lines(renderable: object) -> list[str]:
    buffer = io.StringIO()
    measure_console = Console(
        file=buffer,
        force_terminal=False,
        width=console.width,
        color_system=None,
    )
    measure_console.print(renderable)
    return buffer.getvalue().splitlines()


def _cursor_rows_below_news(renderable: object) -> int:
    lines = _renderable_plain_lines(renderable)
    news_index = next(
        (index for index, line in enumerate(lines) if "·" in line),
        len(lines) - 1,
    )
    return max(len(lines) - news_index, 1)


class _InitIntroTicker:
    def __init__(
        self,
        *,
        width: int,
        cursor_rows_below_news: int,
        initial_news_item: str,
        interval: float,
    ) -> None:
        self.width = width
        self.cursor_rows_below_news = cursor_rows_below_news
        self.active_prompt_lines = 0
        self.interval = interval
        self._last_news_line = folio_news_line(
            width=width,
            news_item=initial_news_item,
        )
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        if self.interval <= 0:
            return
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=max(self.interval, 0.2))

    def add_static_lines(self, count: int) -> None:
        if count <= 0:
            return
        with _TERMINAL_DRAW_LOCK:
            self.cursor_rows_below_news += count

    def set_active_prompt_lines(self, count: int) -> None:
        with _TERMINAL_DRAW_LOCK:
            self.cursor_rows_below_news += count - self.active_prompt_lines
            self.active_prompt_lines = count

    def clear_active_prompt_lines(self) -> None:
        self.set_active_prompt_lines(0)

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            self.refresh()

    def refresh(self) -> None:
        news_line = folio_news_line(width=self.width)
        if news_line == self._last_news_line:
            return
        self._last_news_line = news_line
        with _TERMINAL_DRAW_LOCK:
            if self.cursor_rows_below_news < 1:
                return
            sys.stdout.write(SAVE_CURSOR)
            sys.stdout.write(f"\033[{self.cursor_rows_below_news}A")
            sys.stdout.write("\r" + CLEAR_LINE)
            console.print(Text.from_markup(news_line), end="")
            sys.stdout.write(RESTORE_CURSOR)
            sys.stdout.flush()


def _active_init_intro_ticker() -> _InitIntroTicker | None:
    return _ACTIVE_INIT_INTRO_TICKER


def _set_active_init_prompt_lines(count: int) -> None:
    ticker = _active_init_intro_ticker()
    if ticker is not None:
        ticker.set_active_prompt_lines(count)


def _clear_active_init_prompt_lines() -> None:
    ticker = _active_init_intro_ticker()
    if ticker is not None:
        ticker.clear_active_prompt_lines()


def _add_static_init_prompt_lines(count: int) -> None:
    ticker = _active_init_intro_ticker()
    if ticker is not None:
        ticker.add_static_lines(count)


def _write_completed_line(choice_set: dict[str, object], value: str) -> None:
    with _TERMINAL_DRAW_LOCK:
        sys.stdout.write(completed_line(choice_set, value) + "\n")
        sys.stdout.flush()
        _add_static_init_prompt_lines(1)


class _InitIntroPrinter:
    def __init__(
        self,
        info: dict,
        target: Path,
        repo: str,
        *,
        compact: bool,
        animate_news: bool,
    ) -> None:
        self.info = info
        self.target = target
        self.repo = repo
        self.compact = compact
        self.animate_news = animate_news
        self._ticker: _InitIntroTicker | None = None

    def __enter__(self) -> "_InitIntroPrinter":
        global _ACTIVE_INIT_INTRO_TICKER

        rows_below_news, initial_news_item = _print_init_intro(
            self.info,
            self.target,
            self.repo,
            compact=self.compact,
        )
        if self.animate_news:
            self._ticker = _InitIntroTicker(
                width=console.width,
                cursor_rows_below_news=rows_below_news,
                initial_news_item=initial_news_item,
                interval=_INIT_NEWS_REFRESH_SECONDS,
            )
            _ACTIVE_INIT_INTRO_TICKER = self._ticker
            self._ticker.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        global _ACTIVE_INIT_INTRO_TICKER

        if self._ticker is not None:
            self._ticker.stop()
        if _ACTIVE_INIT_INTRO_TICKER is self._ticker:
            _ACTIVE_INIT_INTRO_TICKER = None
        return None

    def add_static_lines(self, count: int) -> None:
        if self._ticker is not None:
            self._ticker.add_static_lines(count)


def _ask_init_choice(
    title: str,
    options: tuple[tuple[str, str, str], ...],
    *,
    default: str,
    style: str,
) -> str:
    if _init_can_use_arrow_select():
        arrow_answer = _ask_init_arrow_choice(
            title,
            options,
            default=default,
            style=style,
        )
        if arrow_answer is not None:
            return arrow_answer
        console.print(
            "[yellow]readchar is not installed; falling back to typed input.[/yellow]"
        )

    default_index = next(
        (
            index
            for index, option in enumerate(options, start=1)
            if option[0] == default
        ),
        1,
    )
    console.print()
    console.print(f"  {title}", style=style)
    for index, (value, label, description) in enumerate(options, start=1):
        default_marker = " [dim](default)[/dim]" if index == default_index else ""
        console.print(f"  {index}. [bold]{label}[/bold]{default_marker}")
        console.print(f"     [dim]{description}[/dim]")

    choices = [str(index) for index in range(1, len(options) + 1)] + [
        value for value, _label, _description in options
    ]
    answer = Prompt.ask(
        "  Select",
        choices=choices,
        default=str(default_index),
        show_choices=False,
    )
    if answer.isdigit():
        return options[int(answer) - 1][0]
    return answer


def prompt_line(choice_set: dict[str, object]) -> str:
    title = _formatted_init_prompt_title(str(choice_set["title"]))
    return (
        f"{ACCENT}?{RESET} {title} "
        f"{ACCENT}›{RESET} {DIM}- Use arrow-keys. Return to submit.{RESET}"
    )


def yes_no_prompt_line(choice_set: dict[str, object], default_value: str) -> str:
    hint = "(Y/n)" if default_value == "Yes" else "(y/N)"
    question = _formatted_init_prompt_title(
        str(choice_set.get("question", choice_set["title"]))
    )
    return f"{ACCENT}?{RESET} {question} {ACCENT}›{RESET} {DIM}{hint}{RESET}"


def completed_line(choice_set: dict[str, object], value: str) -> str:
    title = _formatted_init_prompt_title(str(choice_set["title"]))
    return f"{GREEN}✔{RESET} {title} {ACCENT}›{RESET} {BOLD}{value}{RESET}"


def _formatted_init_prompt_title(title: str) -> str:
    padding = " " * max(_INIT_PROMPT_TITLE_WIDTH - cell_len(title), 0)
    return f"{BOLD}{title}{RESET}{padding}"


def menu_line(choice: dict[str, str], index: int, selected_index: int) -> str:
    cursor = "›" if index == selected_index else " "
    label = choice["title"]
    if index == selected_index:
        return f"{cursor} {ACCENT}{UNDERLINE}{label}{RESET}"
    return f"  {label}"


def draw_menu(
    choice_set: dict[str, object],
    choices: list[dict[str, str]],
    selected_index: int,
    first_draw: bool,
) -> None:
    line_count = len(choices) + 1
    with _TERMINAL_DRAW_LOCK:
        if not first_draw:
            sys.stdout.write(f"\033[{line_count}A")

        sys.stdout.write(CLEAR_LINE + prompt_line(choice_set) + "\n")
        for index, choice in enumerate(choices):
            sys.stdout.write(
                CLEAR_LINE + menu_line(choice, index, selected_index) + "\n"
            )
        sys.stdout.flush()
        _set_active_init_prompt_lines(line_count)


def draw_yes_no_prompt(
    choice_set: dict[str, object],
    default_value: str,
    first_draw: bool,
) -> None:
    with _TERMINAL_DRAW_LOCK:
        if not first_draw:
            sys.stdout.write(CURSOR_UP)

        sys.stdout.write(
            CLEAR_LINE + yes_no_prompt_line(choice_set, default_value) + "\n"
        )
        sys.stdout.flush()
        _set_active_init_prompt_lines(1)


def clear_menu(choices: list[dict[str, str]]) -> None:
    line_count = len(choices) + 1
    with _TERMINAL_DRAW_LOCK:
        for _ in range(line_count):
            sys.stdout.write(CURSOR_UP + CLEAR_LINE)
        sys.stdout.flush()
        _clear_active_init_prompt_lines()


def clear_prompt() -> None:
    with _TERMINAL_DRAW_LOCK:
        sys.stdout.write(CURSOR_UP + CLEAR_LINE)
        sys.stdout.flush()
        _clear_active_init_prompt_lines()


def _init_can_use_arrow_select() -> bool:
    if os.environ.get("CI"):
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def _init_readchar():
    try:
        from readchar import key, readkey
    except ModuleNotFoundError:
        return None
    return readkey, key


def _ask_init_arrow_choice(
    title: str,
    options: tuple[tuple[str, str, str], ...],
    *,
    default: str,
    style: str,
) -> str | None:
    del style
    readchar = _init_readchar()
    if readchar is None:
        return None
    readkey, key = readchar

    choices = [
        {"title": label, "value": value} for value, label, _description in options
    ]
    choice_set: dict[str, object] = {"title": title, "choices": choices}
    selected_index = next(
        (index for index, choice in enumerate(choices) if choice["value"] == default),
        0,
    )
    first_draw = True
    enter_keys = {getattr(key, "ENTER", "\r"), "\r", "\n"}
    cancel_keys = {getattr(key, "ESC", "\x1b"), getattr(key, "CTRL_C", "\x03"), "q"}

    while True:
        draw_menu(choice_set, choices, selected_index, first_draw)
        first_draw = False
        pressed = readkey()

        if pressed in (getattr(key, "UP", "\x1b[A"), "k"):
            selected_index = (selected_index - 1) % len(choices)
        elif pressed in (getattr(key, "DOWN", "\x1b[B"), "j"):
            selected_index = (selected_index + 1) % len(choices)
        elif pressed in enter_keys:
            choice = choices[selected_index]
            clear_menu(choices)
            _write_completed_line(choice_set, choice["value"])
            return choice["value"]
        elif pressed in cancel_keys:
            clear_menu(choices)
            raise KeyboardInterrupt
        elif pressed.isdigit():
            shortcut_index = int(pressed) - 1
            if 0 <= shortcut_index < len(choices):
                choice = choices[shortcut_index]
                clear_menu(choices)
                _write_completed_line(choice_set, choice["value"])
                return choice["value"]


def _ask_init_arrow_yes_no(title: str, *, default: bool) -> bool | None:
    readchar = _init_readchar()
    if readchar is None:
        return None
    readkey, key = readchar
    choices = [{"title": "Yes", "value": "Yes"}, {"title": "No", "value": "No"}]
    choice_set: dict[str, object] = {
        "title": title,
        "question": title,
        "choices": choices,
    }
    selected_index = 0 if default else 1
    first_draw = True
    enter_keys = {getattr(key, "ENTER", "\r"), "\r", "\n"}
    cancel_keys = {getattr(key, "ESC", "\x1b"), getattr(key, "CTRL_C", "\x03")}

    while True:
        draw_yes_no_prompt(choice_set, choices[selected_index]["value"], first_draw)
        first_draw = False
        pressed = readkey()

        if pressed in (getattr(key, "UP", "\x1b[A"), "k"):
            selected_index = (selected_index - 1) % len(choices)
        elif pressed in (getattr(key, "DOWN", "\x1b[B"), "j"):
            selected_index = (selected_index + 1) % len(choices)
        elif pressed in enter_keys:
            answer = choices[selected_index]["value"]
            clear_prompt()
            _write_completed_line(choice_set, answer)
            return answer == "Yes"
        elif pressed.lower() == "y":
            clear_prompt()
            _write_completed_line(choice_set, "Yes")
            return True
        elif pressed.lower() == "n":
            clear_prompt()
            _write_completed_line(choice_set, "No")
            return False
        elif pressed in cancel_keys:
            clear_prompt()
            raise KeyboardInterrupt


def _ask_init_yes_no(title: str, *, default: bool, style: str) -> bool:
    if _init_can_use_arrow_select():
        arrow_answer = _ask_init_arrow_yes_no(title, default=default)
        if arrow_answer is not None:
            return arrow_answer
        console.print(
            "[yellow]readchar is not installed; falling back to typed input.[/yellow]"
        )

    return Confirm.ask(f"  [{style}]{title}[/]", default=default)


def _print_init_ready(
    target: Path, created: list[str], *, compact: bool = False
) -> None:
    suffix = _command_target_suffix(target)
    if compact:
        console.print()
        for path in created:
            console.print(
                f"  [{_INIT_SECTION_STYLES['success']}]✔ Created {path}[/]",
                soft_wrap=True,
            )
        console.print(
            f"  [dim]Next[/] [{_INIT_SECTION_STYLES['command']}]folio serve{suffix}[/]",
            soft_wrap=True,
        )
        return

    panel_width = min(96, max(44, console.width - 2))
    line_width = panel_width - 4
    target_prefix = _format_cli_path(target)
    target_prefix = f"{target_prefix}/" if target_prefix not in {"", "."} else ""
    panel_created: list[str] = []
    for path in created:
        display_path = path
        if (
            len(f"  Created {display_path}") > line_width
            and target_prefix
            and path.startswith(target_prefix)
        ):
            display_path = path[len(target_prefix) :]
        panel_created.append(f"  Created {display_path}")
    created_lines = "\n".join(panel_created)
    console.print()
    console.print(
        Panel(
            f"[{_INIT_SECTION_STYLES['success']}]✓ Documentation project ready.[/]\n\n"
            f"[{_INIT_SECTION_STYLES['files']}]Files[/]\n"
            f"{created_lines}\n\n"
            f"[{_INIT_SECTION_STYLES['commands']}]Next commands[/]\n"
            f"  [{_INIT_SECTION_STYLES['command']}]folio serve{suffix}[/]\n"
            f"  [{_INIT_SECTION_STYLES['command']}]folio build{suffix}[/]\n"
            f"  [{_INIT_SECTION_STYLES['command']}]folio coverage{suffix}[/]",
            title="Ready",
            border_style=_INIT_SECTION_STYLES["ready_border"],
            width=panel_width,
            expand=False,
        )
    )


def _created_cli_path(target: Path, relative_path: str | Path) -> str:
    return _format_cli_path(target / relative_path)


def _dependency_name(spec: str) -> str:
    name = spec.split(";", 1)[0].strip().lower()
    for separator in ("[", " ", "<", ">", "=", "!", "~"):
        name = name.split(separator, 1)[0]
    return name.replace("_", "-")


def _project_dependency_names(pyproject_data: dict) -> set[str]:
    names: set[str] = set()
    project = pyproject_data.get("project", {})
    if isinstance(project, dict):
        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            names.update(
                _dependency_name(dep) for dep in dependencies if isinstance(dep, str)
            )
        optional_dependencies = project.get("optional-dependencies", {})
        if isinstance(optional_dependencies, dict):
            for dependency_group in optional_dependencies.values():
                if isinstance(dependency_group, list):
                    names.update(
                        _dependency_name(dep)
                        for dep in dependency_group
                        if isinstance(dep, str)
                    )

    dependency_groups = pyproject_data.get("dependency-groups", {})
    if isinstance(dependency_groups, dict):
        for dependency_group in dependency_groups.values():
            if isinstance(dependency_group, list):
                names.update(
                    _dependency_name(dep)
                    for dep in dependency_group
                    if isinstance(dep, str)
                )
    return names


def _detect_framework(pyproject_data: dict) -> str:
    dependencies = _project_dependency_names(pyproject_data)
    if "typer" in dependencies:
        return "Typer package"
    if "fastapi" in dependencies:
        return "FastAPI package"
    if "django" in dependencies:
        return "Django package"
    if "flask" in dependencies:
        return "Flask package"
    if "click" in dependencies:
        return "Click package"
    if pyproject_data:
        return "Python package"
    return "Python project"


def _documentation_status(target: Path) -> str:
    if (target / "docs.yaml").exists():
        return "Documentation scaffold found"
    if (target / "docs").exists():
        return "docs/ found, docs.yaml missing"
    return "Documentation scaffold not found"


def _detect_project(target: Path) -> dict:
    """Detect project name, version, and Python source paths from pyproject.toml."""
    info: dict = {
        "name": target.name,
        "version": "0.1.0",
        "python_path": "src/",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "framework": "Python project",
        "status": _documentation_status(target),
    }

    pyproject = target / "pyproject.toml"
    pyproject_data: dict = {}
    if pyproject.exists():
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore[no-redef]
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                pyproject_data = data
            project = data.get("project", {})
            if not isinstance(project, dict):
                console.print(
                    "[yellow]Warning: Could not read project metadata from "
                    "pyproject.toml: [project] must be a table[/yellow]"
                )
            else:
                project_name = project.get("name")
                project_version = project.get("version")
                if isinstance(project_name, str) and project_name:
                    info["name"] = project_name
                elif project_name is not None:
                    console.print(
                        "[yellow]Warning: Could not read project metadata from "
                        "pyproject.toml: project.name must be a string[/yellow]"
                    )
                if isinstance(project_version, str) and project_version:
                    info["version"] = project_version
                elif project_version is not None:
                    console.print(
                        "[yellow]Warning: Could not read project metadata from "
                        "pyproject.toml: project.version must be a string[/yellow]"
                    )
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            console.print(
                f"[yellow]Warning: Could not read project metadata from pyproject.toml: {escape(str(e))}[/yellow]"
            )

    pkg_name = info["name"].replace("-", "_")
    if (target / "src" / pkg_name).is_dir():
        info["python_path"] = f"src/{pkg_name}"
    elif (target / "src").is_dir():
        info["python_path"] = "src/"
    elif (target / pkg_name).is_dir():
        info["python_path"] = f"{pkg_name}/"
    elif (target / info["name"]).is_dir():
        info["python_path"] = f"{info['name']}/"
    else:
        # Nothing on disk matches: the config must not claim sources that
        # do not exist, or every build warns about init's own scaffolding.
        info["python_path"] = None

    info["framework"] = _detect_framework(pyproject_data)
    return info


def _detect_git_remote(target: Path) -> str:
    """Try to detect the GitHub repo URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        url = result.stdout.strip()
        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/")
        if url.endswith(".git"):
            url = url[:-4]
        return url if url.startswith("https://") else ""
    except OSError as e:
        console.print(
            f"[yellow]Warning: Could not detect git remote: {escape(str(e))}[/yellow]"
        )
        return ""


def _generate_docs_yaml(info: dict) -> str:
    name = info["name"]
    version = info.get("version", "0.1.0")
    python_path = info.get("python_path", "src/")
    repo = info.get("repo", "")
    docstring_style = info.get("docstring_style", DEFAULT_DOCSTRING_STYLE)
    theme_preset = info.get("theme_preset", "organic-editorial")

    lines = [
        "# Folio configuration",
        "# Full reference: https://pguijas.github.io/folio/docs/configuration",
        "",
        "project:",
        f'  name: "{name}"',
        f'  version: "{version}"',
    ]
    if repo:
        lines.append(f'  repo: "{repo}"')
    else:
        lines.append('  # repo: "https://github.com/owner/repo"')

    lines += ["", "source:"]
    if python_path:
        lines += [
            "  python:",
            "    paths:",
            f'      - "{python_path}"',
        ]
        if docstring_style != DEFAULT_DOCSTRING_STYLE:
            lines.append(f'    docstring_style: "{docstring_style}"')
        lines += [
            "    # exclude:",
            '    #   - "**/test_*.py"',
        ]
    else:
        lines += [
            "  # No Python sources detected; uncomment to publish an API reference.",
            "  # python:",
            "  #   paths:",
            '  #     - "src/"',
        ]
    lines += [
        "  docs:",
        '    - "docs/"',
        "",
        'output: "_site"',
        "",
        "theme:",
        f'  preset: "{theme_preset}"',
        "  dark_mode: true",
        '  # logo: "docs/logo.png"',
        '  # favicon: "docs/favicon.ico"',
        "",
        "nav:",
        '  - "Introduction"',
    ]
    if python_path:
        lines.append('  - "API Reference"')
    lines += [
        "",
        "llm:",
        "  generate_llms_txt: true",
        "  generate_llms_full_txt: true",
    ]

    lines.append("")
    return "\n".join(lines)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"folio {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version",
    ),
) -> None:
    pass


@app.command()
def init(
    directory: Path = typer.Argument(
        default=None, help="Project directory (defaults to cwd)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip prompts, use detected defaults"
    ),
) -> None:
    """Initialize a new Folio documentation project."""
    # Init itself only writes files, so a missing toolchain is a warning
    # here (and a hard error at build time) - but surfacing it now saves
    # the user a failed first build.
    try:
        preflight_check()
    except RuntimeError as e:
        console.print(f"[yellow]{escape(str(e))}[/yellow]")
    target = directory or Path.cwd()
    target = target.resolve()
    docs_yaml = target / "docs.yaml"
    if docs_yaml.exists():
        console.print("[yellow]docs.yaml already exists, skipping.[/yellow]")
        raise typer.Exit(0)

    info = _detect_project(target)
    repo_default = _detect_git_remote(target)
    animate_intro_news = not yes and _init_can_use_arrow_select()
    if animate_intro_news:
        animate_intro_news = _init_readchar() is not None

    try:
        with _InitIntroPrinter(
            info,
            target,
            repo_default,
            compact=not yes,
            animate_news=animate_intro_news,
        ) as intro:
            if yes:
                info["repo"] = repo_default
                info["docstring_style"] = DEFAULT_DOCSTRING_STYLE
                info["theme_preset"] = "organic-editorial"
            else:
                with _TERMINAL_DRAW_LOCK:
                    console.print()
                    intro.add_static_lines(1)
                info["repo"] = repo_default

                info["docstring_style"] = _ask_init_choice(
                    "Docstring style",
                    _INIT_DOCSTRING_STYLES,
                    default=DEFAULT_DOCSTRING_STYLE,
                    style=_INIT_SECTION_STYLES["docstring"],
                )

                info["theme_preset"] = _ask_init_choice(
                    "Visual preset",
                    _INIT_THEME_PRESETS,
                    default="organic-editorial",
                    style=_INIT_SECTION_STYLES["theme"],
                )
    except KeyboardInterrupt:
        console.print("\n[dim yellow]^C Init aborted. No files changed.[/dim yellow]")
        raise typer.Exit(1)

    created: list[str] = []
    docs_yaml.write_text(_generate_docs_yaml(info))
    created.append(_created_cli_path(target, "docs.yaml"))

    docs_dir = target / "docs"
    if not docs_dir.exists():
        docs_dir.mkdir()
        (docs_dir / "index.md").write_text(
            f"# {info['name']}\n\nWelcome to the documentation.\n"
        )
        created.append(_created_cli_path(target, "docs/index.md"))

    for relative_path, content in github_pages_workflows().items():
        workflow_path = target / relative_path
        if workflow_path.exists():
            continue
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(content, encoding="utf-8")
        created.append(_created_cli_path(target, relative_path))

    _print_init_ready(target, created, compact=not yes)


def _serve_static_site(
    site_dir: Path,
    port: int = 8787,
    open_browser: bool = False,
    kill_existing: bool = False,
) -> None:
    """Start a local HTTP server for a built static site."""
    import http.server
    import functools
    import threading
    import socket

    if kill_existing:
        from folio.generator.site_builder import SiteBuilder

        SiteBuilder.kill_port(port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while s.connect_ex(("localhost", port)) == 0:
            port += 1

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(site_dir)
    )
    server = http.server.HTTPServer(("localhost", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{port}"
    console.print(f"\n[green]Serving site at[/green] [bold cyan]{url}[/bold cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    if open_browser:
        webbrowser.open(url)

    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
        console.print("\n[dim]Server stopped.[/dim]")


def _serve_and_open(site_dir: Path, port: int = 8787) -> None:
    """Start a local HTTP server for the built site and open it in the browser."""
    _serve_static_site(site_dir, port=port, open_browser=True)


def _read_output_dir_best_effort(config_path: Path, target: Path) -> Path:
    output_dir = target / "_site"
    if not config_path.exists():
        return output_dir

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except _CONFIG_READ_ERRORS as e:
        console.print(
            f"[yellow]Warning: Could not read output from docs.yaml: {escape(str(e))}[/yellow]"
        )
        return output_dir

    if isinstance(raw, dict) and isinstance(raw.get("output"), str):
        try:
            output_dir = resolve_output_dir(target, raw["output"])
        except ValueError as e:
            console.print(
                f"[yellow]Warning: Ignoring unsafe output in docs.yaml: {escape(str(e))}[/yellow]"
            )
    return output_dir


def _resolve_version_output_dir(output_base: Path, version_path: object) -> Path:
    raw_path = str(version_path).strip()
    if not raw_path:
        raise ValueError("Version output path must be a non-empty relative path")

    relative_path = Path(raw_path)
    if relative_path.is_absolute():
        raise ValueError("Version output path must be relative to the output directory")

    output_root = output_base.resolve()
    resolved = (output_root / relative_path).resolve()
    if resolved == output_root or not resolved.is_relative_to(output_root):
        raise ValueError("Version output path must stay within the output directory")

    return resolved


def _write_default_version_redirect(output_base: Path, version_path: str) -> None:
    """Write a static root redirect to the default docs version."""
    import html

    target = version_path.strip("/") or "latest"
    href = f"{target}/"
    escaped_href = html.escape(href, quote=True)
    output_base.mkdir(parents=True, exist_ok=True)
    (output_base / "index.html").write_text(
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f'  <meta http-equiv="refresh" content="0; url={escaped_href}">\n'
        f'  <link rel="canonical" href="{escaped_href}">\n'
        "  <title>Redirecting...</title>\n"
        "</head>\n"
        "<body>\n"
        f'  <p>Redirecting to <a href="{escaped_href}">{escaped_href}</a>.</p>\n'
        f'  <script>window.location.replace("{escaped_href}");</script>\n'
        "</body>\n"
        "</html>\n",
        encoding="utf-8",
    )


def _sync_version_matrix(
    config_path: Path,
    versions: list[dict],
    synced_config: dict | None = None,
) -> None:
    """Inject current version/plugin config into a checked-out historical ref."""
    import yaml

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw["versions"] = versions
    for key, value in (synced_config or {}).items():
        raw[key] = value
    config_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")


def _version_sync_config(config_path: Path, pm: object) -> dict:
    import yaml

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return {"plugins": []}

    synced: dict = {"plugins": raw.get("plugins", [])}
    for key in plugin_config_keys(pm):
        if key in raw:
            synced[key] = raw[key]
    return synced


def _stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_git_commit(project_dir: Path, ref: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"{ref}^{{commit}}"],
        cwd=project_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _version_build_manifest(
    *,
    version: dict,
    commit: str,
    versions: list[dict],
    synced_config: dict,
) -> dict:
    return {
        "schema": 1,
        "label": version.get("label", version.get("path", "")),
        "path": str(version.get("path", "")),
        "ref": str(version.get("ref", "")),
        "commit": commit,
        "versions_hash": _stable_hash(versions),
        "synced_config_hash": _stable_hash(synced_config),
        "folio_version": __version__,
    }


def _read_version_build_manifest(output_path: Path) -> dict | None:
    manifest_path = output_path / _VERSION_MANIFEST
    if not manifest_path.is_file():
        return None
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _version_output_has_content(output_path: Path) -> bool:
    if not output_path.is_dir():
        return False
    return any(child.name != _VERSION_MANIFEST for child in output_path.iterdir())


def _version_build_manifest_matches(output_path: Path, expected: dict) -> bool:
    return (
        _version_output_has_content(output_path)
        and _read_version_build_manifest(output_path) == expected
    )


def _write_version_build_manifest(output_path: Path, manifest: dict) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / _VERSION_MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _remove_version_worktree(project_dir: Path, worktree_dir: Path) -> None:
    """Remove a generated version worktree and prune stale Git metadata."""
    subprocess.run(
        ["git", "worktree", "remove", str(worktree_dir), "--force"],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=project_dir,
        capture_output=True,
    )


def _build_configured_versions(
    *,
    project_dir: Path,
    verbose: bool,
    config: str,
    clean: bool,
) -> None:
    """Build docs for every version configured in docs.yaml."""
    from folio.config import load_config_with_plugins

    _exit_if_feature_disabled("versions")

    config_path = project_dir / config
    cfg, pm = load_config_with_plugins(config_path, plugin_base_dir=project_dir)
    synced_config = _version_sync_config(config_path, pm)

    if not cfg.versions:
        console.print(
            "[yellow]No versions configured in docs.yaml. Use 'folio build' instead.[/yellow]"
        )
        console.print(
            "[dim]Add a 'versions' section to docs.yaml to use multi-version builds.[/dim]"
        )
        raise typer.Exit(1)

    output_base = resolve_output_dir(project_dir, cfg.output_dir)
    if clean and output_base.exists():
        shutil.rmtree(output_base)
    output_base.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for i, version in enumerate(cfg.versions):
        label = version.get("label", f"v{i}")
        vpath = version.get("path", f"v{i}")
        ref = version.get("ref", "")
        output_path = _resolve_version_output_dir(output_base, vpath)
        worktree_dir: Path | None = None
        commit = ""
        manifest = _version_build_manifest(
            version=version,
            commit=commit,
            versions=cfg.versions,
            synced_config=synced_config,
        )

        if ref:
            try:
                commit = _resolve_git_commit(project_dir, str(ref))
            except subprocess.CalledProcessError as e:
                failure = (
                    f"{label}: failed to checkout ref '{ref}' "
                    f"for output '{output_path}'"
                )
                failures.append(failure)
                console.print(
                    f"  [red]Failed to checkout ref '{ref}' for {label} "
                    f"→ {escape(str(output_path))}: {escape(str(e))}[/red]"
                )
                typer.echo(f"  Version output: {output_path}")
                continue

            manifest = _version_build_manifest(
                version=version,
                commit=commit,
                versions=cfg.versions,
                synced_config=synced_config,
            )
            if not clean and _version_build_manifest_matches(output_path, manifest):
                console.print(
                    f"\n  [dim]Reusing version: {label}[/dim] → {output_path}"
                )
                continue

        console.print(f"\n  [bold]Building version: {label}[/bold] → {output_path}")

        if ref:
            worktree_dir = _resolve_version_output_dir(
                project_dir / ".build" / "worktrees",
                vpath,
            )
            try:
                _remove_version_worktree(project_dir, worktree_dir)
                subprocess.run(
                    ["git", "worktree", "add", str(worktree_dir), ref],
                    cwd=project_dir,
                    check=True,
                    capture_output=not verbose,
                )
                source_dir = worktree_dir
                _sync_version_matrix(source_dir / config, cfg.versions, synced_config)
            except subprocess.CalledProcessError as e:
                failure = (
                    f"{label}: failed to checkout ref '{ref}' "
                    f"for output '{output_path}'"
                )
                failures.append(failure)
                console.print(
                    f"  [red]Failed to checkout ref '{ref}' for {label} "
                    f"→ {escape(str(output_path))}: {escape(str(e))}[/red]"
                )
                typer.echo(f"  Version output: {output_path}")
                continue
        else:
            source_dir = project_dir

        from folio.build import run_build

        try:
            run_build(
                source_dir,
                serve=False,
                verbose=verbose,
                config_file=config,
                clean=clean,
                output_override=str(output_path),
                current_version_path=str(vpath),
                include_versions=True,
                source_ref_override=ref,
            )
            _write_version_build_manifest(output_path, manifest)
        except _BUILD_FAILURE_ERRORS as e:
            failure = f"{label}: build failed for output '{output_path}': {e}"
            failures.append(failure)
            console.print(
                f"  [red]Build failed for {label} → {escape(str(output_path))}: {escape(str(e))}[/red]"
            )
            typer.echo(f"  Version output: {output_path}")
            continue
        finally:
            if worktree_dir is not None:
                _remove_version_worktree(project_dir, worktree_dir)

    if failures:
        console.print("\n  [red]Version build failed:[/red]")
        for failure in failures:
            console.print(f"  [red]- {failure}[/red]")
        raise typer.Exit(1)

    _write_default_version_redirect(
        output_base, str(cfg.versions[0].get("path", "latest"))
    )
    console.print(f"\n  [green]All versions built to {cfg.output_dir}/[/green]\n")


@app.command()
def build(
    directory: Path = typer.Argument(
        default=None, help="Project directory (defaults to cwd)"
    ),
    project_dir: Path = typer.Option(
        default=None,
        help="Compatibility option for scripts that prefer named arguments",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    config: str = typer.Option("docs.yaml", "--config", "-c", help="Config file path"),
    clean: bool = typer.Option(
        False, "--clean", help="Force full rebuild (clear cache)"
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        "-o",
        help="Starts a static preview in the browser and blocks until interrupted",
    ),
) -> None:
    from folio.build import run_build

    target = _resolve_project_target(directory, project_dir)
    try:
        run_build(
            target,
            serve=False,
            verbose=verbose,
            config_file=config,
            clean=clean,
            include_versions=False,
        )
    except FileNotFoundError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(1)
    except _BUILD_FAILURE_ERRORS as e:
        console.print(f"[red]Build failed: {escape(str(e))}[/red]")
        raise typer.Exit(1)
    if open_browser:
        from folio.config import load_config

        cfg = load_config(target / config)
        site_dir = resolve_output_dir(target, cfg.output_dir)
        console.print(
            "[yellow]--open starts a static preview server and blocks until interrupted.[/yellow]"
        )
        _serve_and_open(site_dir)


@app.command(name="build-versions", hidden=True)
def build_versions(
    directory: Path = typer.Argument(
        default=None, help="Project directory (defaults to cwd)"
    ),
    project_dir: Path = typer.Option(
        default=None,
        help="Compatibility option for scripts that prefer named arguments",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    config: str = typer.Option("docs.yaml", "--config", "-c", help="Config file path"),
    clean: bool = typer.Option(
        False, "--clean", help="Force full rebuild (clear cache)"
    ),
) -> None:
    """Build docs for all configured versions."""
    _exit_if_feature_disabled("versions")
    target = _resolve_project_target(directory, project_dir)
    try:
        _build_configured_versions(
            project_dir=target,
            verbose=verbose,
            config=config,
            clean=clean,
        )
    except ValueError as e:
        console.print(f"[red]Build failed: {escape(str(e))}[/red]")
        raise typer.Exit(1)


@app.command()
def serve(
    directory: Path = typer.Argument(
        default=None, help="Project directory (defaults to cwd)"
    ),
    project_dir: Path = typer.Option(
        default=None,
        help="Compatibility option for scripts that prefer named arguments",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    config: str = typer.Option("docs.yaml", "--config", "-c", help="Config file path"),
    port: int = typer.Option(4321, "--port", "-p", help="Dev server port"),
    open_browser: bool = typer.Option(
        False, "--open", "-o", help="Open browser automatically"
    ),
    clean: bool = typer.Option(
        False, "--clean", help="Force full rebuild (clear cache)"
    ),
    versions: bool = typer.Option(
        False,
        "--versions",
        help="Build and serve every configured version as a static preview",
        hidden=True,
    ),
    kill_existing: bool = typer.Option(
        False,
        "--kill-existing",
        help="Stop an existing process on the selected port before serving",
    ),
) -> None:
    from folio.config import load_config

    target = _resolve_project_target(directory, project_dir)
    if versions:
        _exit_if_feature_disabled("versions")

    try:
        cfg = load_config(target / config)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(1)

    if versions:
        console.print("[bold]Building configured versions for static preview...[/bold]")
        try:
            _build_configured_versions(
                project_dir=target,
                verbose=verbose,
                config=config,
                clean=clean,
            )
            site_dir = resolve_output_dir(target, cfg.output_dir)
        except ValueError as e:
            console.print(f"[red]Build failed: {escape(str(e))}[/red]")
            raise typer.Exit(1)
        _serve_static_site(
            site_dir,
            port=port,
            open_browser=open_browser,
            kill_existing=kill_existing,
        )
        return

    from folio.build import run_build

    try:
        run_build(
            target,
            serve=True,
            verbose=verbose,
            config_file=config,
            port=port,
            open_browser=open_browser,
            clean=clean,
            include_versions=False,
            kill_existing=kill_existing,
        )
    except FileNotFoundError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")


@app.command()
def coverage(
    directory: Path = typer.Argument(
        default=None, help="Project directory (defaults to cwd)"
    ),
    project_dir: Path = typer.Option(
        default=None,
        help="Compatibility option for scripts that prefer named arguments",
    ),
    config: str = typer.Option("docs.yaml", "--config", "-c", help="Config file path"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="List each undocumented symbol"
    ),
    min_coverage: float = typer.Option(
        0, "--min", help="Minimum coverage percentage (exit 1 if below)"
    ),
) -> None:
    """Analyze documentation coverage of Python source files."""
    from rich.table import Table

    from folio.config import load_config
    from folio.coverage import aggregate, analyze_modules
    from folio.sources import parse_python_sources

    target = _resolve_project_target(directory, project_dir)
    config_path = target / config

    try:
        cfg = load_config(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(1)

    resolved = cfg.resolve_paths(target)

    parsed_python = parse_python_sources(resolved)
    for src in parsed_python.missing_paths:
        console.print(f"[yellow]Warning: Python source path not found: {src}[/yellow]")
    all_modules = parsed_python.modules

    if not all_modules:
        console.print(
            "[red]Error: No Python modules found. Check source paths in docs.yaml.[/red]"
        )
        raise typer.Exit(1)

    results = analyze_modules(all_modules)
    total = aggregate(results)

    table = Table(title="Documentation Coverage")
    table.add_column("Module", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Documented", justify="right")
    table.add_column("Coverage", justify="right")

    for module_name, result in results.items():
        pct = result.percentage
        if pct >= 80:
            style = "green"
        elif pct >= 50:
            style = "yellow"
        else:
            style = "red"
        table.add_row(
            module_name,
            str(result.total),
            str(result.documented),
            f"[{style}]{pct:.1f}%[/{style}]",
        )

    table.add_section()
    total_pct = total.percentage
    if total_pct >= 80:
        total_style = "green"
    elif total_pct >= 50:
        total_style = "yellow"
    else:
        total_style = "red"
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total.total}[/bold]",
        f"[bold]{total.documented}[/bold]",
        f"[bold {total_style}]{total_pct:.1f}%[/bold {total_style}]",
    )

    console.print()
    console.print(table)

    if verbose and total.undocumented:
        console.print()
        console.print("[bold]Undocumented:[/bold]")
        for name in sorted(total.undocumented):
            console.print(f"  {name}")

    console.print()
    if min_coverage > 0 and total_pct < min_coverage:
        console.print(
            f"[red]Coverage {total_pct:.1f}% is below minimum {min_coverage:.1f}%[/red]"
        )
        raise typer.Exit(1)


@app.command()
def clean(
    directory: Path = typer.Argument(
        default=None, help="Project directory (defaults to cwd)"
    ),
    project_dir: Path = typer.Option(
        default=None,
        help="Compatibility option for scripts that prefer named arguments",
    ),
) -> None:
    target = _resolve_project_target(directory, project_dir)
    build_dir = target / ".build"
    config_path = target / "docs.yaml"

    output_dir = _read_output_dir_best_effort(config_path, target)

    removed = []
    for d in [build_dir, output_dir]:
        if d.exists():
            shutil.rmtree(d)
            removed.append(str(d.relative_to(target)))

    if removed:
        console.print(f"[green]Cleaned: {', '.join(removed)}[/green]")
    else:
        console.print("[yellow]Nothing to clean.[/yellow]")
