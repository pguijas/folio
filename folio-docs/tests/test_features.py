from folio_docs import features
from folio_docs.features import (
    disabled_api_feature_for_module,
    disabled_doc_feature_for_route,
    disabled_feature_message,
    experimental_feature_state,
    is_feature_enabled,
)


def test_experimental_features_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert is_feature_enabled("versions") is False
    assert is_feature_enabled("theme_configurator") is True
    assert is_feature_enabled("search") is True


def test_plugins_are_released_and_always_enabled(monkeypatch):
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert is_feature_enabled("plugins") is True
    assert is_feature_enabled("plugins", {}) is True


def test_roadmap_is_released_and_always_enabled(monkeypatch):
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert is_feature_enabled("roadmap") is True
    assert is_feature_enabled("roadmap", {}) is True
    # The roadmap and landing docs routes are published; gated routes stay hidden.
    assert disabled_doc_feature_for_route("roadmap") is None
    assert disabled_doc_feature_for_route("landing") is None
    assert disabled_doc_feature_for_route("versioning") == "versions"


def test_landing_is_released_and_always_enabled(monkeypatch):
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert is_feature_enabled("landing") is True
    assert is_feature_enabled("landing", {}) is True


def test_custom_components_are_released_and_always_enabled(monkeypatch):
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert is_feature_enabled("custom_components") is True
    assert is_feature_enabled("custom_components", {}) is True


def test_experimental_features_ignore_unrelated_env_flags():
    env = {"ANY_FLAG": "1"}

    assert is_feature_enabled("versions", env) is False
    assert is_feature_enabled("theme_configurator", env) is True


def test_folio_experimental_enables_named_feature():
    env = {"FOLIO_EXPERIMENTAL": "versions"}

    assert is_feature_enabled("versions", env) is True
    # Only the listed feature is enabled; the rest stay disabled.
    assert is_feature_enabled("i18n", env) is False


def test_folio_experimental_accepts_comma_list_with_whitespace():
    env = {"FOLIO_EXPERIMENTAL": " i18n , versions "}

    assert is_feature_enabled("i18n", env) is True
    assert is_feature_enabled("versions", env) is True


def test_folio_experimental_empty_value_keeps_features_disabled():
    env = {"FOLIO_EXPERIMENTAL": " , "}

    assert is_feature_enabled("versions", env) is False


def test_folio_experimental_reads_process_environment(monkeypatch):
    monkeypatch.setenv("FOLIO_EXPERIMENTAL", "i18n")

    assert is_feature_enabled("i18n") is True
    assert is_feature_enabled("versions") is False


def test_experimental_feature_state_lists_enabled_features():
    assert experimental_feature_state({}) == "disabled"
    assert (
        experimental_feature_state({"FOLIO_EXPERIMENTAL": "versions,i18n"})
        == "i18n,versions"
    )


def test_disabled_feature_message_names_the_feature():
    assert (
        disabled_feature_message("versions")
        == "The 'versions' feature is not available in this release."
    )


def test_plugin_api_modules_are_published():
    assert disabled_api_feature_for_module("folio_docs.extensions") is None
    assert disabled_api_feature_for_module("folio_docs.docs.extension_emitter") is None
    assert disabled_api_feature_for_module("folio_docs.plugin") is None
    assert disabled_api_feature_for_module("folio_docs.docs.integrations.roadmap") is None
    assert disabled_api_feature_for_module("folio_docs.config") is None


def test_gated_doc_routes_are_hidden_while_their_feature_is_off(monkeypatch):
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert disabled_doc_feature_for_route("versioning") == "versions"
    assert disabled_doc_feature_for_route("/versioning/") == "versions"
    assert disabled_doc_feature_for_route("i18n") == "i18n"
    assert disabled_doc_feature_for_route("quickstart") is None


def test_folio_experimental_publishes_the_routes_it_enables():
    env = {"FOLIO_EXPERIMENTAL": "versions"}

    # Regression: the env argument was accepted and never read, so an enabled
    # feature still lost its pages from navigation, search, and llms output.
    assert disabled_doc_feature_for_route("versioning", env) is None
    assert disabled_doc_feature_for_route("/versioning/", env) is None
    # Only the enabled feature is published; the rest stay gated.
    assert disabled_doc_feature_for_route("i18n", env) == "i18n"


def test_gated_doc_routes_read_the_process_environment(monkeypatch):
    monkeypatch.setenv("FOLIO_EXPERIMENTAL", "i18n,versions")

    assert disabled_doc_feature_for_route("i18n") is None
    assert disabled_doc_feature_for_route("versioning") is None


def test_gated_api_modules_stay_gated_regardless_of_mvp_feature_list(monkeypatch):
    """Membership in the module map is itself the gate.

    ``is_feature_enabled`` only gates names listed in ``MVP_DISABLED_FEATURES``,
    so routing this lookup through it would publish every mapped module whose
    feature is not on that list.
    """
    monkeypatch.setattr(
        features, "MVP_DISABLED_API_MODULES", {"folio_docs.docs.integrations.roadmap": "plugins"}
    )
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)

    assert disabled_api_feature_for_module("folio_docs.docs.integrations.roadmap") == "plugins"
    # Submodules inherit the gate; unrelated modules do not.
    assert disabled_api_feature_for_module("folio_docs.docs.integrations.roadmap.data") == "plugins"
    assert disabled_api_feature_for_module("folio_docs.docs.integrations.landing") is None


def test_folio_experimental_publishes_the_api_modules_it_enables(monkeypatch):
    monkeypatch.setattr(
        features, "MVP_DISABLED_API_MODULES", {"folio_docs.docs.integrations.roadmap": "plugins"}
    )

    assert (
        disabled_api_feature_for_module(
            "folio_docs.docs.integrations.roadmap", {"FOLIO_EXPERIMENTAL": "plugins"}
        )
        is None
    )
    # An unrelated feature name in the variable leaves the module gated.
    assert (
        disabled_api_feature_for_module(
            "folio_docs.docs.integrations.roadmap", {"FOLIO_EXPERIMENTAL": "versions"}
        )
        == "plugins"
    )
