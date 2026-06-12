from folio.features import (
    disabled_api_feature_for_module,
    disabled_feature_message,
    experimental_enabled,
    is_feature_enabled,
)


def test_experimental_features_are_disabled():
    assert experimental_enabled() is False
    assert is_feature_enabled("versions") is False
    assert is_feature_enabled("theme_configurator") is True
    assert is_feature_enabled("search") is True


def test_experimental_features_ignore_env_override():
    env = {"ANY_FLAG": "1"}

    assert experimental_enabled(env) is False
    assert is_feature_enabled("versions", env) is False
    assert is_feature_enabled("theme_configurator") is True


def test_disabled_feature_message_does_not_advertise_env_override():
    assert (
        disabled_feature_message("versions")
        == "The 'versions' feature is not available in this release."
    )


def test_disabled_api_modules_are_tied_to_disabled_features():
    assert disabled_api_feature_for_module("folio.extensions") == "plugins"
    assert (
        disabled_api_feature_for_module("folio.generator.extension_emitter")
        == "plugins"
    )
    assert disabled_api_feature_for_module("folio.plugin") == "plugins"
    assert disabled_api_feature_for_module("folio.plugins.roadmap") == "plugins"
    assert disabled_api_feature_for_module("folio.config") is None
