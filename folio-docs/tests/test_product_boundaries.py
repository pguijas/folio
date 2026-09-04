from pathlib import Path

from folio_docs.agent_output import AgentArtifacts
from folio_docs.config import Config


def test_agent_artifacts_publish_without_the_docs_builder(tmp_path: Path) -> None:
    output_dir = tmp_path / "site"
    artifacts = AgentArtifacts(
        Config(
            project_name="Boundary",
            output_dir=str(output_dir),
            site_url="https://example.com",
        ),
        build_dir=tmp_path / "build",
        output_dir=output_dir,
    )

    mirror = artifacts.write_markdown_mirror(
        "guide/start",
        "---\ntitle: Start\n---\n# Start\n\n<Callout>Portable context.</Callout>\n",
    )
    artifacts.write_llm_files("# Boundary\n", None)
    contract = artifacts.write_authoring_contract(
        generated_at="2026-08-29T00:00:00Z",
        components=None,
        config_keys={"project"},
        routes={"/docs/guide/start/"},
    )

    assert mirror.read_text(encoding="utf-8") == "# Start\n\nPortable context.\n"
    assert (output_dir / "llms.txt").read_text(encoding="utf-8") == "# Boundary\n"
    assert contract.is_file()
