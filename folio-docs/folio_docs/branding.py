from __future__ import annotations

import time

from rich.cells import cell_len

FOLIO_LOGO_STYLE = "bold #c4b5fd"
FOLIO_NEWS_STYLE = "bold #bef264"
FOLIO_NEWS_ITEMS = (
    "Incremental builds skip pages whose sources are unchanged",
    "Pagefind search opens from the navbar or Cmd+K",
    "GitHub Pages deploys infer the right base path",
    "Theme presets ship polished docs shells by default",
    "Mermaid diagrams render from fenced code blocks",
    "KaTeX math works inline and in display blocks",
    "Coverage gates catch undocumented public APIs",
    "Source links jump straight to GitHub file lines",
    "llms.txt output keeps docs readable for AI assistants",
    "Link validation flags broken internal links at build time",
    "File watching rebuilds changed pages while serving",
    "Social cards generate OpenGraph previews automatically",
)
FOLIO_ASCII_ART = (
    " ████████╗ ██████╗ ██╗     ██╗ ██████╗ \n"
    " ██╔═════╝██╔═══██╗██║     ██║██╔═══██╗\n"
    " █████╗   ██║   ██║██║     ██║██║   ██║\n"
    " ██╔══╝   ██║   ██║██║     ██║██║   ██║\n"
    " ██║      ╚██████╔╝███████╗██║╚██████╔╝\n"
    " ╚═╝       ╚═════╝ ╚══════╝╚═╝ ╚═════╝ "
)


def _center_text(line: str, width: int | None) -> str:
    if not width:
        return line
    padding = max((width - cell_len(line)) // 2, 0)
    return f"{' ' * padding}{line}"


def folio_news_item(elapsed_seconds: float = 0, *, interval: float = 1.0) -> str:
    if not FOLIO_NEWS_ITEMS:
        return ""
    elapsed = max(elapsed_seconds, 0)
    index = int(elapsed // interval)
    return FOLIO_NEWS_ITEMS[index % len(FOLIO_NEWS_ITEMS)]


def current_folio_news_item() -> str:
    return folio_news_item(time.time())


def folio_news_line(
    *,
    width: int | None = None,
    news_item: str | None = None,
) -> str:
    news = news_item if news_item is not None else current_folio_news_item()
    return f"[{FOLIO_NEWS_STYLE}]{_center_text(f'· {news} ·', width)}[/]"


def folio_banner(
    version: str = "",
    *,
    width: int | None = None,
    news_item: str | None = None,
    include_news: bool = True,
) -> str:
    lines = FOLIO_ASCII_ART.splitlines()
    if width:
        padding = max((width - max(cell_len(line) for line in lines)) // 2, 0)
        lines = [f"{' ' * padding}{line}" for line in lines]
    if version:
        lines[-1] = f"{lines[-1]} {version}"
    styled_lines = [
        f"[{FOLIO_LOGO_STYLE}]{line}[/]"
        for line in lines[: len(FOLIO_ASCII_ART.splitlines())]
    ]
    if include_news:
        styled_lines.append("")
        styled_lines.append(folio_news_line(width=width, news_item=news_item))
    return "\n".join(styled_lines)
