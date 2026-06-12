from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from folio.plugin import hookimpl


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEDIA_DIR = PROJECT_ROOT / "assets" / "media"
COMPONENT_PATH = PROJECT_ROOT / "docs" / "components" / "folio-overview-video.tsx"
MEDIA_FILES = (
    "folio-commercial-v2.mp4",
    "folio-commercial-v2-poster.jpeg",
)


@hookimpl
def register_extensions(registry: Any, config: Any) -> None:
    registry.register_component(
        "FolioOverviewVideo",
        import_path="@/components/__folio_components/folio-overview-video",
        source_path=COMPONENT_PATH,
        expose_mdx=True,
    )


@hookimpl
def emit_assets(builder: Any, config: Any) -> None:
    target_dir = Path(builder.build_dir) / "public" / "media"
    target_dir.mkdir(parents=True, exist_ok=True)

    for filename in MEDIA_FILES:
        shutil.copy2(MEDIA_DIR / filename, target_dir / filename)
