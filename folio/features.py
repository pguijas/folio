from __future__ import annotations

from collections.abc import Mapping

MVP_DISABLED_FEATURES = frozenset(
    {
        "custom_components",
        "i18n",
        "landing",
        "plugins",
        "roadmap",
        "versions",
    }
)

MVP_DISABLED_DOC_ROUTES: dict[str, str] = {
    "i18n": "i18n",
    "landing": "landing",
    "plugins": "plugins",
    "roadmap": "roadmap",
    "versioning": "versions",
}

MVP_DISABLED_API_MODULES: dict[str, str] = {
    "folio.extensions": "plugins",
    "folio.generator.extension_emitter": "plugins",
    "folio.plugin": "plugins",
    "folio.plugins": "plugins",
}


def experimental_enabled(env: Mapping[str, str] | None = None) -> bool:
    return False


def is_feature_enabled(feature: str, env: Mapping[str, str] | None = None) -> bool:
    return feature not in MVP_DISABLED_FEATURES


def experimental_feature_state(env: Mapping[str, str] | None = None) -> str:
    return "disabled"


def disabled_doc_feature_for_route(
    route: str,
    env: Mapping[str, str] | None = None,
) -> str | None:
    normalized_route = route.strip("/")
    return MVP_DISABLED_DOC_ROUTES.get(normalized_route)


def disabled_api_feature_for_module(
    module_name: str,
    env: Mapping[str, str] | None = None,
) -> str | None:
    for module_prefix, feature in MVP_DISABLED_API_MODULES.items():
        if module_name == module_prefix or module_name.startswith(f"{module_prefix}."):
            return feature
    return None


def disabled_feature_message(feature: str) -> str:
    return f"The '{feature}' feature is not available in this release."
