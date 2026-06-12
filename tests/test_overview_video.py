from pathlib import Path
import json
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
VIDEO_NAME = "folio-commercial-v2.mp4"
POSTER_NAME = "folio-commercial-v2-poster.jpeg"


def test_overview_page_does_not_require_project_video_plugin_in_mvp() -> None:
    overview = (ROOT / "docs" / "guide" / "index.md").read_text(encoding="utf-8")

    assert "<FolioOverviewVideo />" not in overview


def test_template_does_not_register_project_specific_folio_video() -> None:
    mdx_components = (ROOT / "template" / "mdx-components.tsx").read_text(
        encoding="utf-8"
    )

    assert "FolioOverviewVideo" not in mdx_components
    assert not (ROOT / "template" / "components" / "folio-overview-video.tsx").exists()
    assert not (ROOT / "template" / "public" / "media" / VIDEO_NAME).exists()
    assert not (ROOT / "template" / "public" / "media" / POSTER_NAME).exists()


def test_docs_config_loads_project_overview_video_plugin() -> None:
    config = (ROOT / "docs.yaml").read_text(encoding="utf-8")

    assert "./docs/plugins/overview_video.py" in config


def test_folio_overview_video_component_uses_project_media_assets() -> None:
    component_path = ROOT / "docs" / "components" / "folio-overview-video.tsx"

    assert component_path.exists()

    component = component_path.read_text(encoding="utf-8")
    assert f'poster="/media/{POSTER_NAME}"' in component
    assert f'src="/media/{VIDEO_NAME}"' in component
    assert "Folio overview video" in component
    assert "<figcaption" not in component
    assert "max-w-6xl" in component
    assert "border border-border" in component
    assert "autoPlay" in component
    assert "loop" in component
    assert "controls" not in component


def test_project_overview_video_plugin_copies_project_media(tmp_path: Path) -> None:
    import importlib.util

    plugin_path = ROOT / "docs" / "plugins" / "overview_video.py"
    spec = importlib.util.spec_from_file_location("overview_video", plugin_path)
    assert spec is not None
    assert spec.loader is not None
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)

    class Builder:
        build_dir = tmp_path / "build"

    plugin.emit_assets(builder=Builder(), config=None)

    media_dir = tmp_path / "build" / "public" / "media"
    assert (media_dir / VIDEO_NAME).read_bytes() == (
        ROOT / "assets" / "media" / VIDEO_NAME
    ).read_bytes()
    assert (media_dir / POSTER_NAME).read_bytes() == (
        ROOT / "assets" / "media" / POSTER_NAME
    ).read_bytes()


def test_folio_commercial_v2_assets_exist() -> None:
    media_dir = ROOT / "assets" / "media"
    video = media_dir / VIDEO_NAME
    poster = media_dir / POSTER_NAME

    assert video.exists()
    assert video.stat().st_size > 150_000
    assert video.stat().st_size < 750_000
    assert poster.exists()
    assert poster.stat().st_size > 50_000


def test_folio_commercial_v2_video_is_1080p_without_audio() -> None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        pytest.skip("ffprobe is not installed")

    video = ROOT / "assets" / "media" / VIDEO_NAME
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(result.stdout)
    streams = metadata["streams"]
    video_stream = next(stream for stream in streams if stream["codec_type"] == "video")

    assert video_stream["width"] == 1920
    assert video_stream["height"] == 1080
    assert not any(stream["codec_type"] == "audio" for stream in streams)
    assert 9.8 <= float(metadata["format"]["duration"]) <= 10.2


def test_readme_does_not_embed_project_video() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert f"assets/media/{VIDEO_NAME}" not in readme
    assert f"assets/media/{POSTER_NAME}" not in readme
    assert "Watch the 10-second overview" not in readme
    assert "git clone" not in readme
    assert "https://github.com/pguijas/folio" in readme
