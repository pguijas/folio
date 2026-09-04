from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from types import ModuleType
from typing import get_args, get_origin, get_type_hints

import pytest

from folio_docs.plugin import (
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
    assert hasattr(HookSpec, "collect_docs")
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


def test_register_cli_is_a_declared_hookspec() -> None:
    assert hasattr(HookSpec, "register_cli")


def test_roadmap_cli_command_dispatched_through_register_cli_hook() -> None:
    import typer

    from folio_docs.plugin import PluginManager
    from folio_docs.docs.integrations import roadmap

    pm = PluginManager()
    pm.register(roadmap)

    cli = typer.Typer()
    pm.pm.hook.register_cli(app=cli)

    names = {command.name for command in cli.registered_commands}
    assert "roadmap" in names


def test_default_plugins_include_roadmap() -> None:
    from folio_docs.plugin import DEFAULT_PLUGINS

    assert "folio_docs.docs.integrations.roadmap" in DEFAULT_PLUGINS


def test_user_plugin_names_rejects_non_list_plugins() -> None:
    """`plugins: my_plugin` (a YAML scalar) must fail the build loudly.

    Silently dropping the entries would ship a site with the user's plugin
    output missing; iterating the string would explode it into characters.
    """
    from folio_docs.plugin import user_plugin_names

    with pytest.raises(ValueError, match="plugins: must be a YAML list"):
        user_plugin_names({"name": "my_plugin"})
    # None (empty `plugins:` key) and real lists stay accepted.
    assert user_plugin_names(None) == []
    assert user_plugin_names(["my_plugin"]) == ["my_plugin"]


def test_load_default_plugins_bypasses_entry_point_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An installed distribution declaring a folio entry point named after a
    default plugin (e.g. 'folio_docs.docs.integrations.landing') must never shadow the
    bundled first-party module: defaults are imported directly."""
    import folio_docs.plugin as plugin_module
    import folio_docs.docs.integrations.landing as landing
    import folio_docs.docs.integrations.roadmap as roadmap

    def entry_point_lookup_forbidden(name: str) -> object:
        raise AssertionError(
            f"default plugin '{name}' must never be resolved via entry points"
        )

    monkeypatch.setattr(
        plugin_module, "_find_entry_point", entry_point_lookup_forbidden
    )

    pm = plugin_module.PluginManager()
    pm.load_default_plugins()

    assert pm.pm.is_registered(roadmap)
    assert pm.pm.is_registered(landing)


def test_load_default_plugins_warns_and_continues_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A default plugin that fails to import degrades to a warning: it must
    not take down every build and CLI start (cli.py loads defaults at import
    time, before typer even parses arguments)."""
    import importlib

    import folio_docs.plugin as plugin_module
    import folio_docs.docs.integrations.roadmap as roadmap

    real_import = importlib.import_module

    def broken_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "folio_docs.docs.integrations.landing":
            raise ImportError("broken install")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", broken_import)

    pm = plugin_module.PluginManager()
    with pytest.warns(UserWarning, match="Skipping default plugin"):
        pm.load_default_plugins()

    # The healthy default still loaded; the broken one was skipped.
    assert pm.pm.is_registered(roadmap)
    assert "folio_docs.docs.integrations.landing" not in pm.plugin_labels.values()


def test_default_plugins_load_and_dedup_in_plugin_manager() -> None:
    from folio_docs.plugin import DEFAULT_PLUGINS, PluginManager, user_plugin_names

    pm = PluginManager()
    pm.load_default_plugins()
    pm.load_plugins(user_plugin_names(list(DEFAULT_PLUGINS)))

    registered = [getattr(plugin, "__name__", "") for plugin in pm.pm.get_plugins()]
    assert registered.count("folio_docs.docs.integrations.roadmap") == 1


def test_roadmap_plugin_hooks_are_inert_without_config_key() -> None:
    from types import SimpleNamespace

    from folio_docs.docs.integrations import roadmap

    config = SimpleNamespace(extra={})

    # Without a `roadmap:` key configure leaves config.extra untouched...
    roadmap.configure(config=config, raw_config={})
    assert config.extra == {}

    # ...and the build hooks emit nothing (registry/builder are never used).
    roadmap.register_extensions(registry=None, config=config)
    roadmap.emit_assets(builder=None, config=config)


def test_roadmap_plugin_activates_on_config_key() -> None:
    from types import SimpleNamespace

    from folio_docs.docs.integrations import roadmap

    config = SimpleNamespace(extra={})
    roadmap.configure(config=config, raw_config={"roadmap": {"phases": []}})

    assert config.extra["roadmap"] == {
        "routes": {"docs": True, "public": False},
        "phases": [],
        "description": "",
        "projects": {},
    }


def test_roadmap_plugin_configure_preserves_description() -> None:
    from types import SimpleNamespace

    from folio_docs.docs.integrations import roadmap

    # register_extensions() reads the description back from
    # config.extra["roadmap"] and hands it to the layout's title band;
    # normalization must not drop it.
    config = SimpleNamespace(extra={})
    roadmap.configure(
        config=config,
        raw_config={"roadmap": {"phases": [], "description": "  Page copy.  "}},
    )

    assert config.extra["roadmap"]["description"] == "Page copy."


def test_roadmap_shapes_agree_on_their_keys() -> None:
    """Every roadmap dict carries the same keys, so indexing one cannot raise.

    ``register_extensions`` reads ``roadmap["description"]`` off whatever
    these return, and ``project_block`` reads ``roadmap["projects"]``. The
    empty shape and the parsed shape drifted apart once already, which is a
    KeyError at build time rather than a missing paragraph on the page.
    """
    from types import SimpleNamespace

    from folio_docs.docs.integrations import roadmap

    keys = {"routes", "phases", "description", "projects"}

    shapes = [
        roadmap.empty_roadmap(),
        # normalize_roadmap: the mapping branch and the "not a mapping" branch.
        roadmap.normalize_roadmap({"phases": []}),
        roadmap.normalize_roadmap({"description": "Copy."}),
        roadmap.normalize_roadmap("not a mapping"),
        roadmap.normalize_roadmap(None),
        # get_roadmap: inactive (no extra, non-dict extra) and active.
        roadmap.get_roadmap(SimpleNamespace(extra={})),
        roadmap.get_roadmap(SimpleNamespace(extra={"roadmap": "nonsense"})),
        roadmap.get_roadmap(SimpleNamespace(extra={"roadmap": {}})),
        roadmap.get_roadmap(SimpleNamespace(extra={"roadmap": {"phases": []}})),
    ]
    for shape in shapes:
        assert set(shape) == keys
        # The one the page props are built from must be indexable, not just present.
        assert isinstance(shape["description"], str)

    # active_roadmap is the one path that may return None; when it does not,
    # it agrees with the rest.
    assert roadmap.active_roadmap(SimpleNamespace(extra={})) is None
    assert set(roadmap.active_roadmap(SimpleNamespace(extra={"roadmap": {}}))) == keys


def test_call_isolated_fail_fast_reraises_as_plugin_hook_error() -> None:
    from folio_docs.plugin import PluginHookError, PluginManager, hookimpl

    class Boom:
        @hookimpl
        def register_extensions(self, registry, config) -> None:
            raise ValueError("kaboom")

    pm = PluginManager()
    pm.register(Boom(), name="boom-plugin")

    try:
        pm.call_isolated(
            "register_extensions",
            policy="fail_fast",
            registry=object(),
            config=object(),
        )
    except PluginHookError as exc:
        assert "boom-plugin" in str(exc)
        assert "register_extensions" in str(exc)
        assert isinstance(exc.__cause__, ValueError)
    else:
        raise AssertionError("expected PluginHookError")


def test_call_isolated_warn_skip_continues_and_attributes() -> None:
    from folio_docs.plugin import PluginManager, hookimpl

    class Boom:
        @hookimpl
        def emit_assets(self, builder, config) -> None:
            raise RuntimeError("nope")

    class Good:
        @hookimpl
        def emit_assets(self, builder, config) -> None:
            builder.append("good-ran")

    pm = PluginManager()
    pm.register(Good(), name="good-plugin")
    pm.register(Boom(), name="boom-plugin")

    warnings_seen: list[str] = []
    sink: list[str] = []
    pm.call_isolated(
        "emit_assets",
        policy="warn_skip",
        on_warn=warnings_seen.append,
        builder=sink,
        config=object(),
    )

    assert sink == ["good-ran"]
    assert len(warnings_seen) == 1
    assert "boom-plugin" in warnings_seen[0]


def test_call_isolated_filters_kwargs_to_impl_argnames() -> None:
    from folio_docs.plugin import PluginManager, hookimpl

    class SubsetSig:
        @hookimpl
        def emit_assets(self, builder) -> None:  # declares only builder, not config
            builder.append("ran")

    pm = PluginManager()
    pm.register(SubsetSig(), name="subset")

    sink: list[str] = []
    pm.call_isolated("emit_assets", policy="warn_skip", builder=sink, config=object())
    assert sink == ["ran"]


def test_call_isolated_matches_native_broadcast_order() -> None:
    from folio_docs.plugin import PluginManager, hookimpl

    class A:
        @hookimpl
        def config_keys(self) -> list[str]:
            return ["a"]

    class B:
        @hookimpl
        def config_keys(self) -> list[str]:
            return ["b"]

    pm = PluginManager()
    pm.register(A(), name="a")
    pm.register(B(), name="b")

    native = list(pm.pm.hook.config_keys())
    isolated = pm.call_isolated("config_keys", policy="warn_skip")
    assert isolated == native


def test_load_plugins_records_label_for_file_plugin(tmp_path) -> None:
    from folio_docs.plugin import PluginManager

    plugin_file = tmp_path / "myplugin.py"
    plugin_file.write_text(
        "from folio_docs.plugin import hookimpl\n"
        "@hookimpl\n"
        "def config_keys():\n"
        "    return ['x']\n",
        encoding="utf-8",
    )

    pm = PluginManager(base_dir=tmp_path)
    pm.load_plugins(["./myplugin.py"], base_dir=tmp_path)

    assert "./myplugin.py" in pm.plugin_labels.values()


def test_plugin_api_version_constant_defined() -> None:
    from folio_docs.plugin import FOLIO_PLUGIN_API_VERSION

    assert FOLIO_PLUGIN_API_VERSION == "1.1"


def test_plugin_api_version_independent_of_mdx_contract_version() -> None:
    # Distinct symbols in distinct modules; versions bump independently.
    import folio_docs.agent_output.contract as mdx
    import folio_docs.plugin as plugin

    assert hasattr(plugin, "FOLIO_PLUGIN_API_VERSION")
    assert hasattr(mdx, "FOLIO_MDX_CONTRACT_VERSION")
    assert "FOLIO_MDX_CONTRACT_VERSION" not in vars(plugin)


def test_check_plugin_api_version_accepts_match_and_older_minor() -> None:
    from folio_docs.plugin import check_plugin_api_version

    check_plugin_api_version("1.0", "p")  # exact
    check_plugin_api_version("1.0", "p", host_version="1.3")  # host newer -> ok
    check_plugin_api_version(None, "p")  # undeclared -> allowed


def test_check_plugin_api_version_warns_on_newer_minor() -> None:
    import pytest

    from folio_docs.plugin import check_plugin_api_version

    with pytest.warns(UserWarning, match="newplug"):
        check_plugin_api_version("1.4", "newplug", host_version="1.0")


def test_check_plugin_api_version_refuses_major_mismatch_and_malformed() -> None:
    import pytest

    from folio_docs.plugin import check_plugin_api_version

    with pytest.raises(ValueError, match="major"):
        check_plugin_api_version("2.0", "p", host_version="1.0")
    with pytest.raises(ValueError):
        check_plugin_api_version("banana", "p")


def test_load_plugins_refuses_incompatible_major(tmp_path) -> None:
    import pytest

    from folio_docs.plugin import PluginManager

    plugin_file = tmp_path / "futureplugin.py"
    plugin_file.write_text(
        "FOLIO_PLUGIN_API = '2.0'\n"
        "from folio_docs.plugin import hookimpl\n"
        "@hookimpl\n"
        "def config_keys():\n"
        "    return ['z']\n",
        encoding="utf-8",
    )
    pm = PluginManager(base_dir=tmp_path)
    with pytest.raises(RuntimeError, match="futureplugin"):
        pm.load_plugins(["./futureplugin.py"], base_dir=tmp_path)


def test_first_party_plugins_declare_current_api() -> None:
    from folio_docs.plugin import FOLIO_PLUGIN_API_VERSION
    from folio_docs.docs.integrations import landing, openapi, roadmap

    assert landing.FOLIO_PLUGIN_API == FOLIO_PLUGIN_API_VERSION
    assert openapi.FOLIO_PLUGIN_API == FOLIO_PLUGIN_API_VERSION
    assert roadmap.FOLIO_PLUGIN_API == FOLIO_PLUGIN_API_VERSION


def _fake_entry_point(name: str, module, dist_name: str | None = None):
    class FakeDist:
        def __init__(self, dist: str) -> None:
            self.name = dist

    class FakeEntryPoint:
        def __init__(self) -> None:
            self.name = name
            if dist_name is not None:
                self.dist = FakeDist(dist_name)

        def load(self):
            return module

    return FakeEntryPoint()


def test_installed_cli_plugins_register_commands(monkeypatch) -> None:
    import importlib.metadata

    from folio_docs.plugin import load_installed_cli_plugins

    registered: list[object] = []
    app = object()

    def register(cli_app: object) -> None:
        registered.append(cli_app)

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: (
            [_fake_entry_point("agents", register, dist_name="folio-agents")]
            if group == "folio.cli"
            else []
        ),
    )

    assert load_installed_cli_plugins(app) == ["agents"]
    assert registered == [app]


def test_broken_installed_cli_plugin_does_not_break_the_cli(monkeypatch) -> None:
    import importlib.metadata

    from folio_docs.plugin import load_installed_cli_plugins

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: (
            [_fake_entry_point("broken", object(), dist_name="broken-product")]
            if group == "folio.cli"
            else []
        ),
    )

    with pytest.warns(UserWarning, match="broken"):
        assert load_installed_cli_plugins(object()) == []


def test_load_plugins_resolves_named_entry_point(tmp_path, monkeypatch) -> None:
    import importlib.metadata
    from types import ModuleType

    from folio_docs.plugin import PluginManager, hookimpl

    mod = ModuleType("fake_ep_plugin")

    @hookimpl
    def config_keys():
        return ["from_entry_point"]

    mod.config_keys = config_keys

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: (
            [_fake_entry_point("coolplugin", mod)] if group == "folio-docs" else []
        ),
    )

    pm = PluginManager(base_dir=tmp_path)
    pm.load_plugins(["coolplugin"], base_dir=tmp_path)

    results = pm.call_isolated("config_keys", policy="warn_skip")
    assert ["from_entry_point"] in results
    assert "coolplugin" in pm.plugin_labels.values()


def test_check_plugin_api_version_accepts_flexible_forms() -> None:
    import warnings as warnings_module

    from folio_docs.plugin import check_plugin_api_version

    with warnings_module.catch_warnings():
        warnings_module.simplefilter("error")
        check_plugin_api_version("1", "p", host_version="1.0")  # missing minor -> 0
        check_plugin_api_version("1.0.0", "p", host_version="1.0")  # semver
        check_plugin_api_version("1.0.9", "p", host_version="1.0")  # patch ignored
        check_plugin_api_version(1, "p", host_version="1.0")  # bare int major


def test_check_plugin_api_version_semver_minor_still_compared() -> None:
    import pytest

    from folio_docs.plugin import check_plugin_api_version

    with pytest.warns(UserWarning, match="newer"):
        check_plugin_api_version("1.4.2", "p", host_version="1.0")
    with pytest.raises(ValueError, match="major"):
        check_plugin_api_version("2", "p", host_version="1.0")


def test_check_plugin_api_version_rejects_truly_malformed() -> None:
    import pytest

    from folio_docs.plugin import check_plugin_api_version

    for bad in ("banana", "1.2.3.4", "", "1.x"):
        with pytest.raises(ValueError, match="unparseable"):
            check_plugin_api_version(bad, "p")


def test_public_register_enforces_api_version() -> None:
    import pytest

    from folio_docs.plugin import PluginManager

    class FuturePlugin:
        FOLIO_PLUGIN_API = "2.0"

        @hookimpl
        def config_keys(self):
            return ["z"]

    pm = PluginManager()
    with pytest.raises(ValueError, match="major"):
        pm.register(FuturePlugin(), name="futureplug")
    assert pm.call_isolated("config_keys", policy="warn_skip") == []


def test_public_register_accepts_semver_declaration() -> None:
    from folio_docs.plugin import PluginManager

    class SemverPlugin:
        FOLIO_PLUGIN_API = "1.0.0"

        @hookimpl
        def config_keys(self):
            return ["ok"]

    pm = PluginManager()
    pm.register(SemverPlugin(), name="semver")
    assert pm.call_isolated("config_keys", policy="warn_skip") == [["ok"]]


def test_register_rejects_hookwrapper_impls_loudly() -> None:
    import pytest

    from folio_docs.plugin import PluginHookError, PluginManager

    class Wrapper:
        @hookimpl(hookwrapper=True)
        def config_keys(self):
            yield

    pm = PluginManager()
    with pytest.raises(PluginHookError, match="not supported") as excinfo:
        pm.register(Wrapper(), name="wrapperplug")
    assert "wrapperplug" in str(excinfo.value)
    # The offending plugin is not left half-registered.
    assert pm.call_isolated("config_keys", policy="warn_skip") == []


def test_load_plugins_rejects_hookwrapper_file_plugin(tmp_path) -> None:
    import pytest

    from folio_docs.plugin import PluginManager

    plugin_file = tmp_path / "wrapperplugin.py"
    plugin_file.write_text(
        "from folio_docs.plugin import hookimpl\n"
        "@hookimpl(hookwrapper=True)\n"
        "def config_keys():\n"
        "    yield\n",
        encoding="utf-8",
    )
    pm = PluginManager(base_dir=tmp_path)
    with pytest.raises(RuntimeError, match="not supported"):
        pm.load_plugins(["./wrapperplugin.py"], base_dir=tmp_path)


def test_call_isolated_rejects_wrapper_impl_at_dispatch() -> None:
    import pytest

    from folio_docs.plugin import PluginHookError, PluginManager

    class Wrapper:
        @hookimpl(hookwrapper=True)
        def config_keys(self):
            yield

    pm = PluginManager()
    # Bypass the PluginManager.register guard on purpose.
    pm.pm.register(Wrapper(), name="sneaky")
    with pytest.raises(PluginHookError, match="not supported"):
        pm.call_isolated("config_keys", policy="warn_skip")


def test_call_isolated_rejects_unknown_policy() -> None:
    import pytest

    from folio_docs.plugin import PluginManager

    pm = PluginManager()
    with pytest.raises(ValueError, match="unknown policy"):
        pm.call_isolated("config_keys", policy="failfast")


def test_call_isolated_impl_guard_rolls_back_failed_impl_under_warn_skip() -> None:
    from folio_docs.plugin import PluginManager

    class Good:
        @hookimpl
        def emit_assets(self, builder) -> None:
            builder.append("good")

    class Boom:
        @hookimpl
        def emit_assets(self, builder) -> None:
            builder.append("boom-partial")
            raise RuntimeError("boom")

    pm = PluginManager()
    pm.register(Good(), name="good")
    pm.register(Boom(), name="boom")

    state: list[str] = []

    def snapshot():
        saved = list(state)

        def rollback() -> None:
            state[:] = saved

        return rollback

    warnings_seen: list[str] = []
    pm.call_isolated(
        "emit_assets",
        policy="warn_skip",
        on_warn=warnings_seen.append,
        impl_guard=snapshot,
        builder=state,
    )

    # Boom's partial write was rolled back; Good's survived.
    assert state == ["good"]
    assert len(warnings_seen) == 1
    assert "boom" in warnings_seen[0]


def test_call_isolated_impl_guard_no_rollback_under_fail_fast() -> None:
    import pytest

    from folio_docs.plugin import PluginHookError, PluginManager

    class Boom:
        @hookimpl
        def emit_assets(self, builder) -> None:
            builder.append("boom-partial")
            raise RuntimeError("boom")

    pm = PluginManager()
    pm.register(Boom(), name="boom")

    state: list[str] = []
    rollbacks: list[str] = []

    def snapshot():
        return lambda: rollbacks.append("rolled-back")

    with pytest.raises(PluginHookError):
        pm.call_isolated(
            "emit_assets", policy="fail_fast", impl_guard=snapshot, builder=state
        )

    assert rollbacks == []  # exception propagates; no rollback under fail_fast
    assert state == ["boom-partial"]


def test_asset_builder_protocol_matches_site_builder_surface() -> None:
    from folio_docs.plugin import AssetBuilder

    for method in ("read_meta", "register_route", "emitted_routes"):
        assert callable(getattr(AssetBuilder, method))

    from folio_docs.docs.site_builder import SiteBuilder

    for method in ("read_meta", "register_route", "emitted_routes"):
        assert callable(getattr(SiteBuilder, method))


def test_plugin_config_protocol_declares_project_dir() -> None:
    config_hints = get_type_hints(PluginConfig)
    assert config_hints["project_dir"] is str


def test_entry_point_shadowing_importable_module_warns(tmp_path, monkeypatch) -> None:
    import importlib.metadata

    import pytest

    from folio_docs.plugin import PluginManager

    ep_mod = ModuleType("shadowing_ep_plugin")

    @hookimpl
    def config_keys():
        return ["from_entry_point"]

    ep_mod.config_keys = config_keys

    # "json" is always importable, so the entry point shadows a real module.
    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: (
            [_fake_entry_point("json", ep_mod, dist_name="acme-docs")]
            if group == "folio-docs"
            else []
        ),
    )

    pm = PluginManager(base_dir=tmp_path)
    with pytest.warns(UserWarning, match="acme-docs") as record:
        pm.load_plugins(["json"], base_dir=tmp_path)

    messages = [str(w.message) for w in record]
    assert any("json" in m and "entry point" in m for m in messages)
    assert ["from_entry_point"] in pm.call_isolated("config_keys", policy="warn_skip")


def test_duplicate_entry_point_names_resolved_deterministically(
    tmp_path, monkeypatch
) -> None:
    import importlib.metadata

    import pytest

    from folio_docs.plugin import PluginManager

    mod_alpha = ModuleType("alpha_ep_plugin")
    mod_zeta = ModuleType("zeta_ep_plugin")

    @hookimpl
    def alpha_keys():
        return ["from_alpha"]

    @hookimpl
    def zeta_keys():
        return ["from_zeta"]

    mod_alpha.config_keys = alpha_keys
    mod_zeta.config_keys = zeta_keys

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: (
            [
                _fake_entry_point("coolplugin", mod_zeta, dist_name="zeta-dist"),
                _fake_entry_point("coolplugin", mod_alpha, dist_name="alpha-dist"),
            ]
            if group == "folio-docs"
            else []
        ),
    )

    pm = PluginManager(base_dir=tmp_path)
    with pytest.warns(UserWarning, match="alpha-dist") as record:
        pm.load_plugins(["coolplugin"], base_dir=tmp_path)

    messages = " ".join(str(w.message) for w in record)
    assert "zeta-dist" in messages  # both contenders named
    # Sorted by distribution name: alpha-dist wins deterministically.
    results = pm.call_isolated("config_keys", policy="warn_skip")
    assert ["from_alpha"] in results
    assert ["from_zeta"] not in results


def test_unlisted_entry_points_are_not_autoloaded(tmp_path, monkeypatch) -> None:
    import importlib.metadata
    from types import ModuleType

    from folio_docs.plugin import PluginManager, hookimpl

    mod = ModuleType("unlisted_ep_plugin")

    @hookimpl
    def config_keys():
        return ["should_not_load"]

    mod.config_keys = config_keys

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group=None: (
            [_fake_entry_point("coolplugin", mod)] if group == "folio-docs" else []
        ),
    )

    pm = PluginManager(base_dir=tmp_path)
    pm.load_plugins([], base_dir=tmp_path)  # nothing listed -> nothing loads

    assert pm.call_isolated("config_keys", policy="warn_skip") == []


def test_plugin_topic_owns_the_publishing_signal() -> None:
    from folio_docs.plugin import PLUGIN_TOPIC

    assert PLUGIN_TOPIC == "folio-plugin"


def test_publishing_convention_is_the_distribution_metadata() -> None:
    """No sidecar manifest: pyproject.toml is where a plugin declares itself."""
    from pathlib import Path

    from folio_docs.plugin import PLUGIN_TOPIC, PROJECT_NAME

    root = Path(__file__).resolve().parents[1]
    authoring = (root / "docs/guide/plugins/authoring.md").read_text(encoding="utf-8")

    assert "## Publishing a plugin" in authoring
    assert f"[project.entry-points.{PROJECT_NAME}]" in authoring
    assert PLUGIN_TOPIC in authoring
    assert "[tool.folio-docs.plugin]" in authoring
    assert not (root / "folio-plugin.toml").exists()


def test_catalog_metadata_table_is_never_read_by_folio() -> None:
    """`[tool.folio-docs.plugin]` is catalog metadata; the build must ignore it."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sources = (root / "folio").rglob("*.py")

    assert not [
        path.name
        for path in sources
        if "tool.folio" in path.read_text(encoding="utf-8")
    ]


def test_project_plugin_module_level_code_runs_at_cli_load(
    tmp_path, monkeypatch
) -> None:
    """The sharp edge documented in the trust page: listing a plugin runs it.

    Project plugins load while ``folio_docs.cli`` is imported, before any argument
    is parsed, so their module-level code executes on any invocation from the
    project directory (``folio --help`` included).
    """
    import typer

    from folio_docs import cli as cli_module

    marker = tmp_path / "executed.txt"
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "side_effect.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "SideEffect"\n\nplugins:\n  - "./plugins/side_effect.py"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    cli_module._load_project_cli_plugins(typer.Typer())

    assert marker.read_text(encoding="utf-8") == "ran"
