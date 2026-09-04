from __future__ import annotations

import os
from collections.abc import Mapping

# Environment kill-switch override for MVP-disabled experimental features.
# Holds a comma-separated list of feature names (e.g. "plugins" or
# "plugins,versions"); listed features are enabled despite being in
# MVP_DISABLED_FEATURES.
EXPERIMENTAL_ENV_VAR = "FOLIO_EXPERIMENTAL"

MVP_DISABLED_FEATURES = frozenset(
    {
        "i18n",
        "versions",
    }
)

MVP_DISABLED_DOC_ROUTES: dict[str, str] = {
    "i18n": "i18n",
    "versioning": "versions",
}

MVP_DISABLED_API_MODULES: dict[str, str] = {}


def _experimental_features(env: Mapping[str, str] | None = None) -> frozenset[str]:
    """Feature names enabled via the FOLIO_EXPERIMENTAL environment variable."""
    source = os.environ if env is None else env
    raw = source.get(EXPERIMENTAL_ENV_VAR, "")
    if not isinstance(raw, str):
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def experimental_enabled(env: Mapping[str, str] | None = None) -> bool:
    return bool(_experimental_features(env))


def is_feature_enabled(feature: str, env: Mapping[str, str] | None = None) -> bool:
    if feature not in MVP_DISABLED_FEATURES:
        return True
    return feature in _experimental_features(env)


def experimental_feature_state(env: Mapping[str, str] | None = None) -> str:
    enabled = _experimental_features(env)
    if not enabled:
        return "disabled"
    return ",".join(sorted(enabled))


def disabled_doc_feature_for_route(
    route: str,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Feature gating ``route``, or ``None`` when the page may be published.

    A route stays gated only while its feature is off, so a feature enabled
    through ``FOLIO_EXPERIMENTAL`` publishes its pages instead of leaving
    them out of navigation, search, and the llms output.
    """
    normalized_route = route.strip("/")
    feature = MVP_DISABLED_DOC_ROUTES.get(normalized_route)
    if feature is None or feature in _experimental_features(env):
        return None
    return feature


def disabled_api_feature_for_module(
    module_name: str,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Feature gating ``module_name``'s API pages, or ``None`` when publishable.

    Membership in the map is itself the gate — unlike ``is_feature_enabled``,
    which only gates names listed in ``MVP_DISABLED_FEATURES``. Only naming the
    feature in ``FOLIO_EXPERIMENTAL`` publishes the module.
    """
    for module_prefix, feature in MVP_DISABLED_API_MODULES.items():
        if module_name == module_prefix or module_name.startswith(f"{module_prefix}."):
            return None if feature in _experimental_features(env) else feature
    return None


def disabled_feature_message(feature: str) -> str:
    return f"The '{feature}' feature is not available in this release."
