from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from types import ModuleType
from typing import get_args, get_origin, get_type_hints

import pytest

from folio.plugin import (
    ConfigKeyNames,
    HookSpec,
    PluginConfig,
    PluginManager,
    RawConfig,
    hookimpl,
    normalize_config_key_names,
)


def test_hookspec_has_expected_hooks():
    assert hasattr(HookSpec, "register_components")
    assert hasattr(HookSpec, "post_build")
    assert hasattr(HookSpec, "config_keys")
    assert hasattr(HookSpec, "configure")
    assert hasattr(HookSpec, "register_extensions")
    assert hasattr(HookSpec, "emit_assets")
    assert not hasattr(HookSpec, "register_parsers")
    assert not hasattr(HookSpec, "register_docstring_styles")
    assert not hasattr(HookSpec, "modify_theme")
    assert not hasattr(HookSpec, "register_rst_directives")


def test_plugin_manager_creates():
    pm = PluginManager()
    assert pm.pm is not None


def test_plugin_manager_register_and_call():
    class MyPlugin:
        @hookimpl
        def post_build(self, site_dir):
            return f"built:{site_dir}"

    pm = PluginManager()
    pm.register(MyPlugin())
    results = pm.pm.hook.post_build(site_dir="/tmp/site")
    assert results == ["built:/tmp/site"]


def test_plugin_manager_can_collect_config_keys():
    class MyPlugin:
        @hookimpl
        def config_keys(self):
            return ["roadmap"]

    pm = PluginManager()
    pm.register(MyPlugin())
    assert pm.pm.hook.config_keys() == [["roadmap"]]


def test_hookimpl_decorator():
    assert callable(hookimpl)


def test_plugin_boundary_uses_explicit_public_type_aliases():
    assert get_origin(RawConfig) is Mapping
    assert object not in get_args(RawConfig)

    config_key_args = get_args(ConfigKeyNames)
    assert str not in config_key_args

    config_hints = get_type_hints(PluginConfig)
    assert get_origin(config_hints["extra"]) is MutableMapping
    assert object not in get_args(config_hints["extra"])

    post_build_hints = get_type_hints(HookSpec.post_build)
    assert post_build_hints["return"] is type(None)

    register_hints = get_type_hints(PluginManager.register)
    assert register_hints["plugin"].__name__ == "FolioPlugin"


def test_plugin_manager_registers_module_plugins():
    module = ModuleType("test_module_plugin")

    @hookimpl
    def post_build(site_dir):
        return f"module-built:{site_dir}"

    module.post_build = post_build

    pm = PluginManager()
    pm.register(module)

    assert pm.pm.hook.post_build(site_dir="/tmp/site") == ["module-built:/tmp/site"]


def test_config_key_names_require_sequence_container():
    assert normalize_config_key_names(["roadmap"]) == ["roadmap"]
    assert normalize_config_key_names(("roadmap",)) == ("roadmap",)

    with pytest.raises(TypeError, match="list or tuple"):
        normalize_config_key_names("roadmap")

    with pytest.raises(TypeError, match="only string keys"):
        normalize_config_key_names(["roadmap", 1])
