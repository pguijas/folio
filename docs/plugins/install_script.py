"""Project plugin: publish install.sh at the site root.

Files under the workspace ``public/`` directory pass through the Next static
export untouched, so the repo's installer becomes curl-able at the site URL —
``curl -LsSf https://pguijas.github.io/folio/install.sh | sh`` — instead of
the longer raw.githubusercontent.com one-liner.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from folio.plugin import hookimpl


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SCRIPT = PROJECT_ROOT / "install.sh"


@hookimpl
def emit_assets(builder: Any, config: Any) -> None:
    target_dir = Path(builder.build_dir) / "public"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INSTALL_SCRIPT, target_dir / INSTALL_SCRIPT.name)
