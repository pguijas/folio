"""The ``folio kanban`` command group.

Bare ``folio kanban`` keeps the read-only table view. The write
subcommands (add / move / update / trail / attach) operate on cardfile
boards only — one logical operation, one targeted file edit, optionally
one conventional commit (``--commit``). ``check`` runs the same fail-fast
validation as the build, exposed as a pre-commit/CI gate.
"""

from __future__ import annotations

import datetime as _dt
import re
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import Any, Optional

import typer
import yaml
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from folio.config import load_config
from folio.plugin import PluginHookError
from folio.plugins import kanban as kanban_plugin
from folio.plugins import kanban_ops
from folio.plugins.kanban_board import load_board_dir
from folio.plugins.kanban_edit import (
    append_trail,
    format_trail_entry,
    insert_artifact,
)


def register(app: Any) -> None:
    console = Console()
    kanban_app = typer.Typer(name="kanban", no_args_is_help=False)

    ProjectDirOption = typer.Option(
        None, "--project-dir", help="Project directory (defaults to cwd)"
    )
    ConfigOption = typer.Option("docs.yaml", "--config", "-c", help="Config file path")
    CommitOption = typer.Option(
        False, "--commit", help="Commit this operation (one op, one commit)"
    )

    def _fail(message: str) -> None:
        console.print(f"[red]Error: {escape(message)}[/red]")
        raise typer.Exit(1)

    def _project(project_dir: Optional[Path]) -> Path:
        return (project_dir or Path.cwd()).resolve()

    def _board_dir(target: Path, config_name: str) -> Path:
        """The cardfile board directory, or a loud refusal matching what
        the build refuses — check can never bless a board that folio build
        would reject."""
        config_path = target / config_name
        if not config_path.is_file():
            _fail(f"config file not found: {config_path}")
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        kanban_raw = raw.get("kanban")
        if not isinstance(kanban_raw, dict):
            _fail(f"no `kanban:` section in {config_path}")
        if "columns" in kanban_raw:
            _fail(
                "inline `columns:` boards were removed; a board is a "
                "directory of card files — run `folio kanban init`, or see "
                "the kanban formats page for moving a hand-written YAML board "
                "to cards"
            )
        source = kanban_raw.get("source")
        if not isinstance(source, str) or not source.strip():
            _fail(
                "the board commands need `kanban.source:` pointing at a board "
                "directory (board.yaml + cards/); run `folio kanban init` — "
                "see the kanban formats page"
            )
        path = Path(source.strip())
        if not path.is_absolute():
            path = target / path
        path = path.resolve()
        if path.is_file():
            _fail(
                f"kanban.source '{source}' is a file; the board is a directory "
                "of cards — see the kanban formats page for the migration"
            )
        if not path.exists():
            _fail(f"no board directory at '{path}'; run `folio kanban init`")
        return path

    def _load(board_dir: Path, target: Path) -> dict[str, Any]:
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                board = load_board_dir(board_dir, project_dir=target)
        except ValueError as exc:
            _fail(str(exc))
        for warning in caught:
            console.print(f"[yellow]warning: {escape(str(warning.message))}[/yellow]")
        return board

    def _card_path(board_dir: Path, card_id: str) -> Path:
        path = board_dir / "cards" / f"{card_id}.md"
        if not path.is_file():
            _fail(f"no card '{card_id}' on this board ({path} not found)")
        return path

    def _find_card(board: dict[str, Any], card_id: str) -> tuple[dict, dict]:
        for column in board["columns"]:
            for card in column["cards"]:
                if card["id"] == card_id:
                    return column, card
        _fail(f"no card '{card_id}' on this board")
        raise AssertionError  # unreachable; _fail raises

    def _commit_echo(target: Path, paths: list[Path], message: str) -> None:
        try:
            made = kanban_ops.commit_paths(target, paths, message)
        except kanban_ops.OpError as exc:
            _fail(str(exc))
        if not made:
            console.print(
                "[yellow]nothing to commit (the board was already in "
                "this state)[/yellow]"
            )
            return
        console.print(f"[green]committed:[/green] {escape(message)}")

    def _git_commit(
        target: Path,
        board_dir: Path,
        message: str,
        extra_paths: Optional[list[Path]] = None,
    ) -> None:
        # `init` also writes docs.yaml, so a board commit is not always
        # confined to the board directory.
        _commit_echo(target, [board_dir, *(extra_paths or [])], message)

    _ABOUT_PAGE = (
        "---\n"
        "title: About this board\n"
        "---\n"
        "\n"
        "This site is a cardfile board, and the front page renders it. Every\n"
        "card is one file under `board/cards/`. The operating protocol travels\n"
        "in `board/SKILL.md`. `folio kanban --help` lists the commands that edit\n"
        "the board.\n"
    )

    # What `folio init` writes when it creates the docs directory: one
    # heading and one sentence. A page still matching this shape is the
    # tool's own scaffolding, not somebody's site.
    _INIT_STUB = re.compile(r"^# [^\n]*\n\nWelcome to the documentation\.\n$")

    def _board_home_page(target: Path, raw: dict) -> tuple[Optional[Path], bool]:
        """Write `docs/index.md` about page when the board is all the project publishes.

        Returns `(page, replaced)`: the page written and whether it replaced
        the untouched `folio init` stub, or `(None, False)` when the project
        already publishes something — then it has a front page and a docs
        route, and the board belongs at `/kanban` beside them rather than on
        top of whatever is at `/`. Two things do not count as publishing:
        a configured Python path that does not exist on disk, and a docs
        tree whose one page is the untouched `folio init` stub — both are
        what `folio init -y` leaves behind moments earlier, so the two
        commands compose into a board that opens at `/`.
        """
        source = raw.get("source") if isinstance(raw.get("source"), dict) else {}
        python = source.get("python") if isinstance(source.get("python"), dict) else {}
        paths = python.get("paths") if isinstance(python.get("paths"), list) else []
        if any((target / str(p)).exists() for p in paths):
            return None, False

        docs_sources = source.get("docs")
        if isinstance(docs_sources, list) and docs_sources:
            roots = [target / str(entry) for entry in docs_sources]
            pages = [
                path
                for root in roots
                if root.is_dir()
                for path in sorted(root.rglob("*"))
                # OS and editor droppings do not make a docs tree somebody's
                # site; the cards loader ignores dotfiles for the same reason.
                if path.is_file() and not path.name.startswith(".")
            ]
            if (
                len(pages) == 1
                # The stub lives at the docs root; the same bytes anywhere
                # else are somebody's page, and replacing a nested file
                # would leave the site with no index at all.
                and any(pages[0] == root / "index.md" for root in roots)
                and _INIT_STUB.match(pages[0].read_text(encoding="utf-8"))
            ):
                pages[0].write_text(_ABOUT_PAGE, encoding="utf-8")
                return pages[0], True
            return None, False

        docs_dir = target / "docs"
        if docs_dir.exists():
            # Not configured but present: the directory is someone's, and
            # writing an index into it would be a guess about their site.
            return None, False
        docs_dir.mkdir()
        page = docs_dir / "index.md"
        page.write_text(_ABOUT_PAGE, encoding="utf-8")
        return page, False

    def _switch_to_new_branch(target: Path, branch: str) -> None:
        """Create and check out the branch the board will live on.

        Organization work has a different rhythm from code: a card moves
        several times a week and nobody wants "board: move x done" between
        two commits of a feature. Keeping the board on its own branch keeps
        the code history about code.

        The cost is worth stating plainly: the board is then not in your
        working tree on the default branch, so the site build that renders it
        has to run from this branch.
        """
        if not (target / ".git").exists():
            _fail(
                f"{target} is not a git repository — run `git init` first, or "
                "pass --no-branch to scaffold without one"
            )
        existing = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        if existing.returncode == 0:
            _fail(
                f"branch '{branch}' already exists — switch to it and run "
                "`folio kanban init --no-branch`, or pass --branch with "
                "another name"
            )
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=target,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            _fail(f"could not create branch '{branch}': {exc.stderr or exc.stdout}")
        console.print(f"[green]branch:[/green] {branch}")

    def _today() -> str:
        return _dt.date.today().isoformat()

    def _edit(action) -> None:
        # CardEditError for surgery refusals, plain ValueError for artifact
        # shape rejections (parse_artifact) — both end as clean CLI errors,
        # never tracebacks.
        try:
            action()
        except ValueError as exc:
            _fail(str(exc))

    def _revalidate_or_rollback(
        board_dir: Path, target: Path, path: Path, original: str
    ) -> None:
        try:
            kanban_ops.revalidate_or_rollback(board_dir, target, path, original)
        except kanban_ops.OpError as exc:
            _fail(str(exc))

    def _show(target: Path, config_name: str) -> None:
        try:
            cfg = load_config(target / config_name)
        except FileNotFoundError as exc:
            _fail(str(exc))
        except PluginHookError as exc:
            _fail(str(exc))

        board = kanban_plugin.get_kanban(cfg)
        columns = kanban_plugin.get_columns(cfg)
        if not columns:
            console.print("[yellow]No kanban columns configured in docs.yaml.[/yellow]")
            return

        board_title = str(board["title"])
        table_title = (
            board_title
            if board_title.lower().startswith(cfg.project_name.lower())
            else f"{cfg.project_name} {board_title}"
        )
        table = Table(title=table_title)
        table.add_column("Column", style="cyan")
        table.add_column("Id", style="dim")
        table.add_column("Card", style="bold")
        table.add_column("Type")
        table.add_column("Size")
        table.add_column("Assignee")
        table.add_column("Tags")

        for column in columns:
            cards = column.get("cards", [])
            cards = cards if isinstance(cards, list) else []
            limit = column.get("limit")
            count = f"{len(cards)}/{limit}" if limit else str(len(cards))
            label = f"{column.get('title', '')} ({count})"
            if not cards:
                table.add_row(label, "", "-", "", "", "", "")
            for position, card in enumerate(cards):
                title = str(card.get("title", ""))
                if card.get("blocked_by"):
                    blockers = ", ".join(card["blocked_by"])
                    title += f" [red](blocked by {blockers})[/red]"
                table.add_row(
                    label if position == 0 else "",
                    str(card.get("id", "")),
                    title,
                    str(card.get("type", "")),
                    str(card.get("size", "")),
                    ", ".join(
                        name
                        for name in (card.get("assignee") or [])
                        if isinstance(name, str)
                    ),
                    ", ".join(
                        tag for tag in card.get("tags", []) if isinstance(tag, str)
                    ),
                )
            table.add_section()

        console.print()
        console.print(table)
        console.print()

    @kanban_app.callback(invoke_without_command=True)
    def kanban_main(
        ctx: typer.Context,
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
    ) -> None:
        """Preview and operate the source-defined kanban board."""
        if ctx.invoked_subcommand is None:
            _show(_project(project_dir), config)

    @kanban_app.command(name="init")
    def init(
        path: str = typer.Option("board", "--path", help="Board directory to create"),
        branch: str = typer.Option(
            "board", "--branch", help="Branch to create the board on"
        ),
        no_branch: bool = typer.Option(
            False, "--no-branch", help="Scaffold on the current branch instead"
        ),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Create a board on its own branch: board.yaml, cards/, and config."""
        target = _project(project_dir)
        config_path = target / config
        if not config_path.is_file():
            _fail(
                f"config file not found: {config_path} — run `folio init` first, "
                "then `folio kanban init`"
            )

        board_dir = Path(path)
        if not board_dir.is_absolute():
            board_dir = target / board_dir
        board_dir = board_dir.resolve()
        if board_dir.exists():
            _fail(f"{board_dir} already exists — remove it or pass --path")

        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if isinstance(raw.get("kanban"), dict):
            _fail(
                f"{config_path} already has a `kanban:` section — "
                "point it at a board directory by hand, or remove it first"
            )

        # The branch comes before any file is written, so a refusal here
        # leaves the working tree exactly as it was.
        if not no_branch:
            _switch_to_new_branch(target, branch)

        cards_dir = board_dir / "cards"
        cards_dir.mkdir(parents=True)
        # Three columns, because a personal board is a queue with a middle.
        # The WIP limit is the one opinion here: it is what makes a board a
        # board rather than a list, and it is a warning, never a refusal.
        (board_dir / "board.yaml").write_text(
            "# The column set. Membership is not listed here — a card's own\n"
            "# `status:` decides which column it is in, so two people editing\n"
            "# different cards can never conflict in this file.\n"
            "columns:\n"
            "  - id: backlog\n"
            "    title: Backlog\n"
            "  - id: in-progress\n"
            "    title: In progress\n"
            "    limit: 3\n"
            "  - id: done\n"
            "    title: Done\n",
            encoding="utf-8",
        )

        starter = cards_dir / "read-me-first.md"
        starter.write_text(
            "---\n"
            "title: Read me first\n"
            "status: backlog\n"
            "tags: [example]\n"
            f"created: '{_today()}'\n"
            "---\n"
            "\n"
            "This card is a file, and that is the whole idea: the board is\n"
            "`board/cards/*.md` in your repository, so its history is your\n"
            "commits and it works offline, in a diff, and in a pull request.\n"
            "\n"
            "Delete this card when you have your own.\n"
            "\n"
            "## Acceptance criteria\n"
            "- [x] the board exists\n"
            "- [ ] the first real card is written\n"
            "\n"
            "## Trail\n"
            f"- {_today()} @you: created the board.\n",
            encoding="utf-8",
        )

        template = cards_dir / "_TEMPLATE.md"
        template.write_text(
            "---\n"
            'title: "Card title"\n'
            "status: backlog\n"
            "priority: normal\n"
            "# tags: [example]\n"
            "# assignee: name\n"
            "# size: M\n"
            "# type: feature\n"
            '# milestone: "0.1"\n'
            "---\n"
            "\n"
            "Describe the work here, before the first `##` heading.\n"
            "\n"
            "## Acceptance criteria\n"
            "- [ ] First criterion\n"
            "\n"
            "## Trail\n"
            "- YYYY-MM-DD @actor: card created\n",
            encoding="utf-8",
        )

        # The protocol, in the repo, with a skill preamble. An agent that
        # has the checkout but not the docs site finds it here, and the
        # frontmatter is what lets a runtime that scans for skills match it
        # to a task instead of the agent having to already know it exists.
        (board_dir / "SKILL.md").write_text(
            "---\n"
            "name: kanban-board\n"
            "description: Use when reading or changing this project's work "
            "board — anything touching "
            f"{board_dir.relative_to(target).as_posix()}/board.yaml or "
            f"{board_dir.relative_to(target).as_posix()}/cards/*.md, moving a "
            "card between columns, adding or retiring a card, appending a "
            "trail line, or attaching an artifact.\n"
            "---\n"
            "\n"
            "# Operate this project's board\n"
            "\n"
            "This directory is a cardfile board: `board.yaml` declares the\n"
            "columns, and every file in `cards/` is one card. Git is the only\n"
            "backend — the board changes by editing files and committing.\n"
            "\n"
            "## Read it\n"
            "\n"
            "- `folio kanban` prints the board as a table, with card ids.\n"
            "- `folio kanban check` validates it. This is the same gate the\n"
            "  site build runs, so a board that fails here fails the build.\n"
            "- One card is `cards/<id>.md`. The filename stem is the id.\n"
            "\n"
            "## Change it\n"
            "\n"
            "One logical operation, one command, one commit:\n"
            "\n"
            "```bash\n"
            'folio kanban add "Title" --status backlog\n'
            "folio kanban move <id> in-progress\n"
            'folio kanban trail <id> --note "what happened" --ref <sha>\n'
            "folio kanban update <id> --set priority=high\n"
            "```\n"
            "\n"
            "Add `--commit` to commit the operation on its own.\n"
            "\n"
            "## Rules\n"
            "\n"
            "- Move a card to `in-progress` when work starts on it, not after.\n"
            "- Append a trail line for every session that touched a card, with\n"
            "  the commit sha or PR number as the ref. The trail is a record;\n"
            "  never rewrite an existing line.\n"
            "- `board.yaml` is human-owned. Do not add or rename columns\n"
            "  unless asked for exactly that.\n"
            "- Never edit other cards in the same commit as your operation.\n"
            "- Lists (`tags`, `blocked_by`) are one-line hand edits by design.\n"
            "\n"
            "## Artifact context maintenance\n"
            "\n"
            "Use exactly two stages: create review artifacts under one card,\n"
            "then integrate only after explicit owner confirmation. To reduce\n"
            "working context, use the agent directive\n"
            "`condense artifacts <card-id>`. It is not a shell command: it\n"
            "reads only that card and its sibling artifact directory, changes\n"
            "no files, and rejects `all`, paths, globs, or multiple ids.\n"
            "Every artifact handoff includes a rendered URL that was opened or\n"
            "requested successfully; a repository or filesystem path alone is\n"
            "not a notification.\n"
            "\n"
            "The full contract, including the card schema and the validation\n"
            "rules, is in the kanban plugin documentation.\n",
            encoding="utf-8",
        )

        # A repository whose only content is a board has no Python and no
        # docs, and a site with no pages at all does not build: Nextra's docs
        # route needs something under it. It also has nothing at `/`, because
        # with no `landing:` key the docs index is the front page — so the
        # front page of a board-only site was blank.
        #
        # One page fixes both, and it is the page such a project wants anyway:
        # the board, at `/`. Projects that already publish something keep the
        # board at `/kanban` and get no page they did not ask for.
        home, replaced_stub = _board_home_page(target, raw)

        # Appended as text, never round-tripped: the same rule the write
        # commands follow, so hand formatting and comments in docs.yaml
        # survive untouched. A replaced stub is already wired as a docs
        # source; appending a second source block would shadow it.
        existing = config_path.read_text(encoding="utf-8")
        block = ""
        if home is not None and not replaced_stub:
            block += (
                "\n# Markdown pages. The front page is the board view;\n"
                "# docs/index.md is the about page at /docs/.\n"
                "source:\n"
                "  docs:\n"
                f"    - {home.parent.relative_to(target).as_posix()}\n"
            )

        # Board-only sites (home is not None) get the workspace on the front page.
        # Sites with existing content keep the board at /kanban.
        public_route = (
            '"/"          # the board is the front page'
            if home is not None
            else "true      # published at /kanban"
        )

        block += (
            "\n# The board lives in the repository as Markdown files.\n"
            "# `folio kanban --help` lists the commands that edit it.\n"
            "kanban:\n"
            f"  source: {board_dir.relative_to(target).as_posix()}\n"
            "  routes:\n"
            f"    public: {public_route}\n"
            "    docs: false\n"
        )
        config_path.write_text(
            existing + ("" if existing.endswith("\n") else "\n") + block,
            encoding="utf-8",
        )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                load_board_dir(board_dir, project_dir=target)
        except ValueError as exc:
            _fail(f"the generated board did not validate: {exc}")

        console.print(f"[green]created:[/green] {board_dir.relative_to(target)}/")
        if home is not None:
            verb = "updated" if replaced_stub else "created"
            console.print(f"[green]{verb}:[/green] {home.relative_to(target)}")
        console.print(f"[green]updated:[/green] {config} (kanban section)")
        console.print("\nNext:")
        console.print('  folio kanban add "Your first task"')
        console.print(
            "  folio serve            # the board is at /"
            if home is not None
            else "  folio serve            # the board is at /kanban"
        )
        if not no_branch:
            console.print(
                f"\nThe board lives on '{branch}'. Organization work stays "
                "there, so\nthe code history stays about code — and the site "
                "that renders the\nboard builds from this branch."
            )
        if commit:
            extra = [config_path] + ([home] if home is not None else [])
            _git_commit(target, board_dir, "board: init", extra_paths=extra)

    @kanban_app.command(name="show")
    def show(
        directory: Optional[Path] = typer.Argument(
            default=None, help="Project directory (defaults to cwd)"
        ),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
    ) -> None:
        """The board as a table (id, column, blocked markers)."""
        if directory is not None and project_dir is not None:
            if directory.resolve() != project_dir.resolve():
                _fail(
                    "Pass the project directory either as an argument or "
                    "--project-dir, not both."
                )
        _show(_project(project_dir or directory), config)

    @kanban_app.command(name="check")
    def check(
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
    ) -> None:
        """Validate the cardfile board — the pre-commit / CI gate."""
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        # Run the exact normalization the build runs (loader + card/link/
        # artifact policies), so check can never bless a board that folio
        # build would reject.
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                board = kanban_plugin.normalize_kanban(
                    {"source": str(board_dir)}, project_dir=target
                )
                # The build resolves milestones against the roadmap in
                # configure(); check normalizes the board directly, so it
                # replays that resolution here — otherwise the registry
                # warning would exist everywhere except the gate that is
                # supposed to show it.
                config_path = target / config
                if config_path.exists():
                    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                    kanban_plugin._resolve_roadmap_phases(
                        board,
                        raw_roadmap=raw.get("roadmap")
                        if isinstance(raw, dict)
                        else None,
                    )
        except ValueError as exc:
            _fail(str(exc))
        for warning in caught:
            console.print(f"[yellow]warning: {escape(str(warning.message))}[/yellow]")
        cards = sum(len(column["cards"]) for column in board["columns"])
        console.print(
            f"[green]Board OK:[/green] {cards} cards across "
            f"{len(board['columns'])} columns"
        )

    @kanban_app.command(name="add")
    def add(
        title: str = typer.Argument(..., help="Card title"),
        status: Optional[str] = typer.Option(
            None, "--status", "-s", help="Column id (defaults to the first column)"
        ),
        description: str = typer.Option("", "--description", "-d"),
        tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
        assignee: str = typer.Option("", "--assignee"),
        priority: str = typer.Option("", "--priority", help="low | normal | high"),
        parent: str = typer.Option("", "--parent", help="Parent card id"),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Create a new card file."""
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        _load(board_dir, target)  # loader warnings echo before the write
        # A value of only commas/whitespace names nobody — same as
        # omitting the flag.
        names = [name.strip() for name in assignee.split(",") if name.strip()]
        try:
            result = kanban_ops.add_card(
                board_dir,
                title,
                status=status or "",
                description=description,
                tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
                priority=priority,
                parent=parent,
                assignee=names,
                commit=False,
                project_dir=target,
            )
        except ValueError as exc:
            _fail(str(exc))
        console.print(f"[green]created:[/green] {result.card_id} ({result.detail})")
        if commit:
            _commit_echo(target, [result.path], result.message)

    @kanban_app.command(name="move")
    def move(
        card_id: str = typer.Argument(..., help="Card id (the filename stem)"),
        status: str = typer.Argument(..., help="Target column id"),
        after: Optional[str] = typer.Option(
            None, "--after", help="Place after this card (rank midpoint)"
        ),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Move a card to another column (a one-line status: edit)."""
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        _load(board_dir, target)  # loader warnings echo before the write
        try:
            result = kanban_ops.move_card(
                board_dir,
                card_id,
                status,
                after=after,
                commit=False,
                project_dir=target,
            )
        except ValueError as exc:
            _fail(str(exc))
        for note in result.warnings:
            console.print(f"[yellow]warning: {escape(note)}[/yellow]")
        console.print(f"[green]moved:[/green] {card_id} {result.old_status} → {status}")
        if commit:
            _commit_echo(target, [result.path], result.message)

    @kanban_app.command(name="update")
    def update(
        card_id: str = typer.Argument(...),
        sets: list[str] = typer.Option(
            [],
            "--set",
            help=(
                "field=value (assignee, type, priority, title, order, parent, "
                "created, milestone, size, source)"
            ),
        ),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Update card fields (assignee takes a comma list; tags/blocked_by are hand edits)."""
        if not sets:
            _fail("nothing to update: pass at least one --set field=value")
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        _find_card(_load(board_dir, target), card_id)
        pairs: list[tuple[str, str]] = []
        for pair in sets:
            if "=" not in pair:
                _fail(f"--set expects field=value, got {pair!r}")
            pairs.append(tuple(pair.split("=", 1)))
        path = _card_path(board_dir, card_id)
        original = path.read_text(encoding="utf-8")
        # Multi-set is atomic: any failing pair restores the whole file.
        result = None
        for key, value in pairs:
            try:
                result = kanban_ops.update_card(
                    board_dir, card_id, key, value, commit=False, project_dir=target
                )
            except ValueError as exc:
                path.write_text(original, encoding="utf-8")
                _fail(str(exc))
        console.print(f"[green]updated:[/green] {card_id} ({', '.join(sets)})")
        if commit and result is not None:
            _commit_echo(target, [result.path], result.message)

    @kanban_app.command(name="trail")
    def trail(
        card_id: str = typer.Argument(...),
        note: str = typer.Option(..., "--note", "-n"),
        ref: str = typer.Option("", "--ref", help="Commit sha or PR #n"),
        actor: str = typer.Option("", "--actor", help="Defaults to git user.name"),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Append one session-trail line (always at the section end)."""
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        _find_card(_load(board_dir, target), card_id)
        path = _card_path(board_dir, card_id)
        entry = None

        def _do() -> None:
            nonlocal entry
            entry = format_trail_entry(
                date=_today(),
                actor=actor or kanban_ops.resolve_actor(),
                ref=ref,
                note=note,
            )
            append_trail(path, entry)

        _edit(_do)
        # escape(): the entry carries user prose, and Rich reads [/...] as
        # markup — a bracketed path crashed the echo AFTER the write, so a
        # retry appended a duplicate line.
        console.print(f"[green]trail:[/green] {escape(entry)}")
        if commit:
            _git_commit(target, board_dir, f"board: trail {card_id}")

    @kanban_app.command(name="comment")
    def comment(
        card_id: str = typer.Argument(...),
        text: str = typer.Argument(..., help="The comment; whitespace collapses"),
        by: str = typer.Option("", "--by", help="Defaults to git user.name"),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Append one comment to the card's thread (always at the end)."""
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        _load(board_dir, target)  # loader warnings echo before the write
        try:
            result = kanban_ops.comment_card(
                board_dir, card_id, text, actor=by, commit=False, project_dir=target
            )
        except ValueError as exc:
            _fail(str(exc))
        console.print(f"[green]comment:[/green] {escape(result.detail)}")
        if commit:
            _commit_echo(target, [result.path], result.message)

    @kanban_app.command(name="attach")
    def attach(
        card_id: str = typer.Argument(...),
        path: Optional[Path] = typer.Argument(
            None, help="A file to copy in beside the card"
        ),
        doc: str = typer.Option("", "--doc", help="Project-relative markdown path"),
        api: str = typer.Option("", "--api", help="API symbol"),
        file: str = typer.Option("", "--file", help="Project-relative path[#Lnn]"),
        pr: int = typer.Option(0, "--pr", help="Pull request number"),
        url: str = typer.Option("", "--url"),
        label: str = typer.Option("", "--label"),
        move: bool = typer.Option(
            False, "--move", help="Move PATH instead of copying it"
        ),
        project_dir: Optional[Path] = ProjectDirOption,
        config: str = ConfigOption,
        commit: bool = CommitOption,
    ) -> None:
        """Attach an artifact: a file copied in beside the card, or one typed entry."""
        given: list[tuple[str, Any]] = [
            (kind, value)
            for kind, value in (
                ("doc", doc),
                ("api", api),
                ("file", file),
                ("pr", pr or ""),
                ("url", url),
            )
            if value
        ]
        if path is not None and given:
            _fail("pass a file to copy in, or one typed flag — not both")
        if path is None and move:
            _fail("--move needs a file path to move")
        if path is None and len(given) != 1:
            _fail(
                "pass exactly one artifact: a file path, or "
                "--doc, --api, --file, --pr, or --url"
            )
        target = _project(project_dir)
        board_dir = _board_dir(target, config)
        _find_card(_load(board_dir, target), card_id)
        card_path = _card_path(board_dir, card_id)

        if path is not None:
            moved_source = _attach_file(
                target, board_dir, card_path, card_id, path, label, move
            )
            if commit:
                _git_commit(
                    target,
                    board_dir,
                    f"board: attach {card_id} {path.name}",
                    extra_paths=[moved_source] if moved_source else None,
                )
            return

        kind, value = given[0]
        if kind == "pr":
            value = pr
        original = card_path.read_text(encoding="utf-8")
        _edit(lambda: insert_artifact(card_path, kind, value, label=label))
        _revalidate_or_rollback(
            board_dir, target, card_path, original
        )  # doc/file targets must exist
        console.print(f"[green]attached:[/green] {kind}: {value} → {card_id}")
        if commit:
            _git_commit(target, board_dir, f"board: attach {kind} to {card_id}")

    def _attach_file(
        target: Path,
        board_dir: Path,
        card_path: Path,
        card_id: str,
        path: Path,
        label: str,
        move: bool,
    ) -> Optional[Path]:
        """Copy (or move) one real file into ``cards/<id>/`` — the copy alone
        publishes it, since ``artifacts:`` derives from the directory. Only
        ``--label`` writes frontmatter: a labelless line naming a sibling is
        a rendered no-op, so none is written.

        Returns the source path when ``--commit`` must stage it too: the
        deletion is the other half of a move, so a git-tracked source rides
        the same commit instead of leaving the tree dirty."""
        src = path.expanduser()
        if not src.exists():
            _fail(f"no file at '{src}' — attach copies a real file in beside the card")
        if not src.is_file():
            _fail(f"'{src}' is not a regular file — attach carries one file at a time")
        if move and src.is_symlink():
            # os.rename would move the link itself, and derivation skips
            # symlinks — the move would land and publish nothing.
            _fail(f"'{src}' is a symlink — pass the real file, or copy it instead")
        name = src.name
        if name.startswith((".", "_")):
            _fail(
                f"'{name}' starts with '{name[0]}' and derivation skips such "
                "names — nothing would publish; rename the file first"
            )
        card_dir = card_path.parent / card_id
        if card_dir.exists() and not card_dir.is_dir():
            _fail(f"'{card_dir}' exists and is not a directory — remove it first")
        dest = card_dir / name
        if dest.exists() or dest.is_symlink():
            _fail(
                f"'{name}' is already in the card's directory — to label it, "
                "attach its bare name with --file; otherwise remove or rename first"
            )
        original = card_path.read_text(encoding="utf-8")
        moved_source: Optional[Path] = None
        if move:
            # Probed before the file leaves; an untracked or out-of-repo
            # source keeps the commit scoped to the board directory.
            probe = subprocess.run(
                ["git", "ls-files", "--error-unmatch", "--", str(src.resolve())],
                cwd=target,
                capture_output=True,
                text=True,
            )
            if probe.returncode == 0:
                moved_source = src.resolve()
        made_dir = not card_dir.is_dir()
        card_dir.mkdir(exist_ok=True)
        if move:
            shutil.move(str(src), str(dest))
        else:
            shutil.copy2(src, dest)

        def _undo() -> None:
            if move:
                shutil.move(str(dest), str(src))  # a rollback restores the source
            else:
                dest.unlink()
            if made_dir:
                card_dir.rmdir()

        if label:
            kind = "doc" if src.suffix.lower() in (".md", ".mdx") else "file"
            try:
                # The bare sibling name: the loader lands the label on the
                # derived entry instead of listing the file twice.
                insert_artifact(card_path, kind, name, label=label)
            except ValueError as exc:
                _undo()
                _fail(str(exc))
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                load_board_dir(board_dir, project_dir=target)
        except ValueError as exc:
            card_path.write_text(original, encoding="utf-8")
            _undo()
            _fail(f"{exc} — the attach was rolled back")
        console.print(f"[green]attached:[/green] {escape(name)} → {card_id}")
        return moved_source

    app.add_typer(kanban_app, name="kanban")
