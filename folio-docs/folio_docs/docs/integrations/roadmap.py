from __future__ import annotations

from pathlib import Path
from typing import Any

from folio_docs.plugin import hookimpl

FOLIO_PLUGIN_API = "1.1"

DEFAULT_ROUTES = {"docs": True, "public": False}
DEFAULT_PROJECT = "shared"
# Per-project presentation, all optional. A project is a card inside the one
# roadmap page, so this is the copy that card's heading shows — not a route.
# Both fields reach the page: the label names the card, the description sits
# under it. A project with neither is left out and the component falls back to
# the raw key.
PROJECT_FIELDS = ("label", "description")
ROADMAP_TYPES = (
    'export type RoadmapStatus = "shipped" | "active" | "next" | "later"\n\n'
    "export interface RoadmapPhase {\n"
    "  id: string\n"
    "  version: string\n"
    "  milestone?: string\n"
    "  project?: string\n"
    "  title: string\n"
    "  status: RoadmapStatus\n"
    "  layer: string\n"
    "  summary: string\n"
    "  command?: string\n"
    "  features: string[]\n"
    "}\n"
)


@hookimpl
def config_keys() -> list[str]:
    return ["roadmap"]


# tryfirst: parse the `roadmap:` key before any project plugin's configure()
# runs, so project plugins can override config.extra["roadmap"] (default
# plugins register first and folio's isolated dispatch is LIFO, which would
# otherwise run this hook after — and clobber — project configure() hooks).
@hookimpl(tryfirst=True)
def configure(config: Any, raw_config: dict[str, Any]) -> None:
    # The plugin is loaded for every build as a first-party default; the
    # `roadmap:` config key is what activates it. Without the key the plugin
    # stays inert (no config.extra entry, no components, no routes).
    if "roadmap" not in raw_config:
        return
    config.extra["roadmap"] = normalize_roadmap(raw_config.get("roadmap", {}))


@hookimpl
def register_extensions(registry: Any, config: Any) -> None:
    roadmap = active_roadmap(config)
    if roadmap is None:
        return
    registry.register_component(
        "Roadmap",
        import_path="@/components/roadmap",
        expose_mdx=True,
        props={
            "phases": "RoadmapPhase[] | undefined",
            "project": "string | undefined",
            "compact": "boolean | undefined",
            "maxPhases": "number | undefined",
            "title": "string | undefined",
            "links": "{ label: string; href: string }[] | undefined",
        },
    )
    # The page composes the header and the release line. It is a separate
    # component from `Roadmap` because the header is interactive and `Roadmap`
    # stays a server component for the landing's miniature.
    registry.register_component(
        "RoadmapPage",
        import_path="@/components/roadmap-page",
        expose_mdx=False,
        props={
            "phases": "RoadmapPhase[] | undefined",
            "projects": (
                "Record<string, { label?: string; description?: string }> | undefined"
            ),
            "title": "string | undefined",
            "description": "string | undefined",
            "links": "{ label: string; href: string }[] | undefined",
        },
    )
    registry.write_data_module(
        "roadmap",
        export_name="roadmapPhases",
        data=roadmap["phases"],
        type_source=ROADMAP_TYPES,
        type_annotation="RoadmapPhase[]",
        module_path="roadmap-data",
    )

    if not roadmap["routes"].get("public"):
        return

    # The board lives wherever kanban's routes.public says: True is the
    # /kanban default, a string is the path itself. Empty when the kanban
    # plugin is off, which drops the cross-links entirely.
    kanban_cfg = getattr(config, "extra", {}).get("kanban")
    kanban_public_route = None
    if isinstance(kanban_cfg, dict):
        kanban_public_route = (kanban_cfg.get("routes") or {}).get("public")
    board_path = None
    if kanban_public_route:
        board_path = (
            "/kanban" if kanban_public_route is True else str(kanban_public_route)
        )

    # `dense` drops the layout's title band, because the page draws its own
    # header: the name, the description and the board cross-link, all on one
    # background, with one card per project under it. The band's slab, its
    # decorative spine and its mono labels are what that header replaced, so
    # keeping both would stack two page names.
    props: dict[str, Any] = {"dense": True}

    page_title = f"{config.project_name} Roadmap"
    block_props: dict[str, Any] = {"title": page_title}

    if roadmap["description"]:
        block_props["description"] = roadmap["description"]

    projects = project_block(roadmap)
    if projects:
        block_props["projects"] = projects

    if board_path is not None:
        # One cross-link, in the header. The per-phase deep links went with the
        # board itself: the docs package no longer ships the card data the
        # component needed to know which milestones have work, and
        # re-importing it would undo the split.
        block_props["links"] = [
            {"label": "Development board", "href": board_href(board_path, 1)}
        ]

    registry.add_view(
        path="/roadmap",
        layout="folio_docs.public",
        title=page_title,
        props=props,
        slots={"main": [{"component": "RoadmapPage", "props": block_props}]},
    )


@hookimpl
def emit_assets(builder: Any, config: Any) -> None:
    """Compatibility hook for generated docs pages.

    Public routes and data modules are emitted through register_extensions().
    """
    roadmap = active_roadmap(config)
    if roadmap is None:
        return

    if roadmap["routes"].get("docs"):
        builder.register_route("roadmap")
        if not builder.page_exists("roadmap"):
            builder.write_page("roadmap", docs_page_mdx())


def board_href(board_path: str, depth: int) -> str:
    """Href to the public board from a view ``depth`` segments below the root.

    The roadmap sits at /roadmap, so ``depth`` is 1 today. It is a parameter
    rather than a constant because the caller knows the route and this helper
    does not, and a hard-coded single ``../`` was already wrong once.
    """
    stripped = board_path.strip("/")
    up = "../" * depth
    if stripped:
        return f"{up}{stripped}/"
    return up or "./"


def project_keys(phases: Any) -> list[str]:
    """Distinct project values, in the order their first phase appears.

    A phase without a ``project`` belongs to the default one, which is what
    the Roadmap component groups it under too.
    """
    keys: list[str] = []
    if not isinstance(phases, list):
        return keys
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        raw = phase.get("project")
        key = str(raw).strip() if isinstance(raw, str) else ""
        key = key or DEFAULT_PROJECT
        if key not in keys:
            keys.append(key)
    return keys


def ordered_project_keys(phases: Any, projects: dict[str, dict[str, str]]) -> list[str]:
    """Project keys that have phases, in the order the page should show them.

    Project order is visible state — the order the groups are drawn in — so
    ``projects:`` declaration order in docs.yaml is the authority. A key that
    has phases but no ``projects:`` entry keeps its first-appearance order,
    after the declared ones. Declared keys with no phases are left out: there
    is nothing to draw.
    """
    present = project_keys(phases)
    declared = [key for key in projects if key in present]
    return declared + [key for key in present if key not in declared]


def project_block(roadmap: dict[str, Any]) -> dict[str, dict[str, str]]:
    """``{key: {label, description}}`` for the projects the page will draw.

    A project with any configured field is included; one with none is left
    out entirely, because the component already falls back to the key. The
    filter is on "has any field" rather than "has a label" so a project
    described but not labelled still reaches the page.
    """
    projects = roadmap["projects"]
    block: dict[str, dict[str, str]] = {}
    for key in ordered_project_keys(roadmap["phases"], projects):
        entry = {
            field: value
            for field, value in projects.get(key, {}).items()
            if field in PROJECT_FIELDS and value
        }
        if entry:
            block[key] = entry
    return block


def normalize_projects(raw_projects: Any) -> dict[str, dict[str, str]]:
    projects: dict[str, dict[str, str]] = {}
    if not isinstance(raw_projects, dict):
        return projects
    for key, value in raw_projects.items():
        if not isinstance(value, dict):
            continue
        entry = {}
        for field in PROJECT_FIELDS:
            candidate = value.get(field)
            if isinstance(candidate, str) and candidate.strip():
                entry[field] = candidate.strip()
        projects[str(key)] = entry
    return projects


def empty_roadmap() -> dict[str, Any]:
    """An inert roadmap carrying every key a normalized one has.

    Callers index the result (``roadmap["description"]``), so the empty
    shape and the parsed shape have to agree on their keys; they drifted
    once already.
    """
    return {
        "routes": dict(DEFAULT_ROUTES),
        "phases": [],
        "description": "",
        "projects": {},
    }


def normalize_roadmap(raw_roadmap: Any) -> dict[str, Any]:
    if not isinstance(raw_roadmap, dict):
        return empty_roadmap()

    routes = dict(DEFAULT_ROUTES)
    raw_routes = raw_roadmap.get("routes", {})
    if isinstance(raw_routes, dict):
        for key in routes:
            if key in raw_routes:
                routes[key] = bool(raw_routes[key])

    phases = raw_roadmap.get("phases", [])
    if not isinstance(phases, list):
        phases = []

    description = raw_roadmap.get("description")
    description = description.strip() if isinstance(description, str) else ""

    return {
        "routes": routes,
        "phases": phases,
        "description": description,
        "projects": normalize_projects(raw_roadmap.get("projects")),
    }


def active_roadmap(config: Any) -> dict[str, Any] | None:
    """The normalized roadmap config, or None when the plugin is inactive.

    The plugin loads for every build (it is a default plugin) but only a
    ``roadmap:`` section in docs.yaml — surfaced as ``config.extra["roadmap"]``
    by configure() — activates its output.
    """
    roadmap = getattr(config, "extra", {}).get("roadmap")
    if not isinstance(roadmap, dict):
        return None
    normalized = normalize_roadmap(roadmap)
    normalized["phases"] = roadmap.get("phases", normalized["phases"])
    return normalized


def get_roadmap(config: Any) -> dict[str, Any]:
    roadmap = active_roadmap(config)
    if roadmap is not None:
        return roadmap
    return empty_roadmap()


def get_phases(config: Any) -> list[dict[str, Any]]:
    phases = get_roadmap(config)["phases"]
    return phases if isinstance(phases, list) else []


def docs_page_mdx() -> str:
    return (
        'import { Roadmap } from "@/components/roadmap"\n\n'
        "# Roadmap\n\n"
        "This page is generated by the official `folio_docs.docs.integrations.roadmap` plugin "
        "when no source roadmap document exists.\n\n"
        "<Roadmap />\n"
    )


@hookimpl
def register_cli(app: Any) -> None:
    import typer
    from rich.console import Console
    from rich.markup import escape
    from rich.table import Table

    from folio_docs.config import load_config

    console = Console()

    @app.command(name="roadmap")
    def roadmap(
        directory: Path = typer.Argument(
            default=None, help="Project directory (defaults to cwd)"
        ),
        project_dir: Path = typer.Option(
            default=None,
            help="Compatibility option for scripts that prefer named arguments",
        ),
        config: str = typer.Option(
            "docs.yaml", "--config", "-c", help="Config file path"
        ),
    ) -> None:
        """Preview source-defined roadmap phases."""
        if directory is not None and project_dir is not None:
            directory_path = directory.resolve()
            project_dir_path = project_dir.resolve()
            if directory_path != project_dir_path:
                console.print(
                    "[red]Error: Pass the project directory either as an argument "
                    "or --project-dir, not both.[/red]"
                )
                raise typer.Exit(1)

        target = (project_dir or directory or Path.cwd()).resolve()
        try:
            cfg = load_config(target / config)
        except FileNotFoundError as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            raise typer.Exit(1)

        phases = get_phases(cfg)
        if not phases:
            console.print("[yellow]No roadmap phases configured in docs.yaml.[/yellow]")
            return

        table = Table(title=f"{cfg.project_name} Roadmap")
        table.add_column("Project")
        table.add_column("Status", style="cyan")
        table.add_column("Version")
        table.add_column("Title", style="bold")
        table.add_column("Command")

        for phase in phases:
            table.add_row(
                str(phase.get("project", "")),
                str(phase.get("status", "")),
                str(phase.get("version", "")),
                str(phase.get("title", "")),
                str(phase.get("command", "")),
            )

        console.print()
        console.print(table)
        console.print()
