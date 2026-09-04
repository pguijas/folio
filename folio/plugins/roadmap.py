from __future__ import annotations

from pathlib import Path
from typing import Any

from folio.plugin import hookimpl

FOLIO_PLUGIN_API = "1.1"

DEFAULT_ROUTES = {"docs": True, "public": False}
ROADMAP_TYPES = (
    'export type RoadmapStatus = "shipped" | "active" | "next" | "later"\n\n'
    "export interface RoadmapPhase {\n"
    "  id: string\n"
    "  version: string\n"
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
            "compact": "boolean | undefined",
            "maxPhases": "number | undefined",
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

    if roadmap["routes"].get("public"):
        props: dict[str, Any] = {"narrow": True}
        raw = getattr(config, "extra", {}).get("roadmap")
        description = raw.get("description") if isinstance(raw, dict) else None
        if isinstance(description, str) and description.strip():
            props["description"] = description.strip()
        # Cross-link the sibling public board when the kanban plugin is on.
        kanban_cfg = getattr(config, "extra", {}).get("kanban")
        kanban_public_route = None
        if isinstance(kanban_cfg, dict):
            kanban_public_route = (kanban_cfg.get("routes") or {}).get("public")
        roadmap_block: dict[str, Any] = {"component": "Roadmap"}
        if kanban_public_route:
            # The board lives wherever routes.public says: True is the
            # /kanban default, a string is the path itself. One computed
            # href serves both the links band and the per-phase deep links.
            board_path = (
                "/kanban" if kanban_public_route is True else str(kanban_public_route)
            )
            stripped = board_path.strip("/")
            board_href = f"../{stripped}/" if stripped else "../"
            props["links"] = [{"label": "Development board", "href": board_href}]
            # Each phase deep-links into the board pre-filtered by milestone.
            roadmap_block["props"] = {"boardHref": board_href}
        registry.add_view(
            path="/roadmap",
            layout="folio.public",
            title=f"{config.project_name} Roadmap",
            props=props,
            slots={"main": [roadmap_block]},
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


def normalize_roadmap(raw_roadmap: Any) -> dict[str, Any]:
    if not isinstance(raw_roadmap, dict):
        return {"routes": dict(DEFAULT_ROUTES), "phases": []}

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

    return {"routes": routes, "phases": phases, "description": description}


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
    return {"routes": dict(DEFAULT_ROUTES), "phases": []}


def get_phases(config: Any) -> list[dict[str, Any]]:
    phases = get_roadmap(config)["phases"]
    return phases if isinstance(phases, list) else []


def docs_page_mdx() -> str:
    return (
        'import { Roadmap } from "@/components/roadmap"\n\n'
        "# Roadmap\n\n"
        "This page is generated by the official `folio.plugins.roadmap` plugin "
        "when no source roadmap document exists.\n\n"
        "<Roadmap />\n"
    )


@hookimpl
def register_cli(app: Any) -> None:
    import typer
    from rich.console import Console
    from rich.markup import escape
    from rich.table import Table

    from folio.config import load_config

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
        table.add_column("Status", style="cyan")
        table.add_column("Version")
        table.add_column("Title", style="bold")
        table.add_column("Command")

        for phase in phases:
            table.add_row(
                str(phase.get("status", "")),
                str(phase.get("version", "")),
                str(phase.get("title", "")),
                str(phase.get("command", "")),
            )

        console.print()
        console.print(table)
        console.print()
