from __future__ import annotations

from folio.generator.extension_emitter import ExtensionEmitter


def test_extension_emitter_apply_requires_extension_registry_boundary() -> None:
    assert ExtensionEmitter.apply.__annotations__["registry"] == "ExtensionRegistry"
