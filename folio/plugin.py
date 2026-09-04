from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import importlib.util
import warnings
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypeAlias

import pluggy

from folio.extensions import ExtensionRegistry

PROJECT_NAME = "folio"

# GitHub topic a published plugin repository carries. It is the whole
# publishing convention: the plugin catalog on the roadmap will discover
# plugins by this topic and nothing else, so the string lives here once and
# the docs quote it from this constant.
PLUGIN_TOPIC = "folio-plugin"

# Version of the Python plugin hook API. Independent of
# FOLIO_MDX_CONTRACT_VERSION (which versions the emitted TS/MDX contract).
# Bump the major when a hook signature changes incompatibly; the minor when
# hooks are added in a backward-compatible way.
FOLIO_PLUGIN_API_VERSION = "1.1"

hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)

# First-party plugins loaded into every PluginManager before any explicit
# `plugins:` entries from docs.yaml. Default plugins are always available but
# stay inert until their config key appears in docs.yaml (e.g. the roadmap
# plugin does nothing without a `roadmap:` section, the landing plugin
# nothing without `landing:`). Releasing another first-party plugin as a
# default is a one-line addition here.
DEFAULT_PLUGINS: tuple[str, ...] = (
    "folio.plugins.roadmap",
    "folio.plugins.kanban",
    "folio.plugins.landing",
)


def user_plugin_names(plugin_names: object) -> list[str]:
    """Validated ``plugins:`` entries with default plugins removed.

    ``None`` (an empty ``plugins:`` key) means no entries. Any other non-list
    value — e.g. the common YAML mistake ``plugins: my_plugin`` instead of a
    one-item list — raises ``ValueError`` so the misconfiguration fails the
    build loudly instead of silently skipping the user's plugins. Entries
    naming a default plugin are dropped: defaults are always registered
    exactly once, via :meth:`PluginManager.load_default_plugins`.
    """
    if plugin_names is None:
        return []
    if not isinstance(plugin_names, (list, tuple)):
        raise ValueError(
            "plugins: must be a YAML list of plugin names, got "
            f"{type(plugin_names).__name__}: {plugin_names!r}"
        )
    return [name for name in plugin_names if name not in DEFAULT_PLUGINS]


def plugins_with_defaults(plugin_names: Iterable[str] | None) -> list[str]:
    """Default plugins first, then user entries, deduplicated.

    A project explicitly listing a default plugin in `plugins:` must not
    register it twice, so user entries that name a default plugin are dropped.
    A non-list ``plugins:`` value raises ``ValueError`` (see
    :func:`user_plugin_names`).
    """
    return [*DEFAULT_PLUGINS, *user_plugin_names(plugin_names)]


_WRAPPER_UNSUPPORTED_MESSAGE = (
    "hookwrapper hookimpls are not supported by folio's isolated dispatch"
)

HookPolicy: TypeAlias = Literal["fail_fast", "warn_skip"]
_HOOK_POLICIES = ("fail_fast", "warn_skip")


def _parse_api_version(value: object) -> tuple[int, int]:
    """Parse an API version into ``(major, minor)``.

    Accepts ``"1"``, ``"1.0"``, ``"1.0.0"``, or a bare int major; a missing
    minor defaults to 0 and any patch component is ignored. Raises
    ``ValueError`` on anything else.
    """
    parts = str(value).split(".")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"expected MAJOR[.MINOR[.PATCH]], got {value!r}")
    numbers = [int(part) for part in parts]
    minor = numbers[1] if len(numbers) > 1 else 0
    return numbers[0], minor


def check_plugin_api_version(
    declared: str | int | None,
    plugin_name: str,
    *,
    host_version: str = FOLIO_PLUGIN_API_VERSION,
) -> None:
    """Validate a plugin's declared target API version against the host.

    Refuses (raises ``ValueError``) on an incompatible major or an unparseable
    version; warns when the plugin targets a newer minor than the host; allows
    a missing declaration or an older/equal minor.
    """
    if declared is None:
        return

    try:
        host_major, host_minor = _parse_api_version(host_version)
        plugin_major, plugin_minor = _parse_api_version(declared)
    except (ValueError, TypeError):
        raise ValueError(
            f"Plugin '{plugin_name}' declares an unparseable "
            f"FOLIO_PLUGIN_API version: {declared!r} "
            f"(expected MAJOR, MAJOR.MINOR, or MAJOR.MINOR.PATCH)"
        ) from None

    if plugin_major != host_major:
        raise ValueError(
            f"Plugin '{plugin_name}' targets incompatible plugin API major "
            f"{declared} (host {host_version})"
        )
    if plugin_minor > host_minor:
        warnings.warn(
            f"Plugin '{plugin_name}' targets plugin API {declared}, newer than "
            f"host {host_version}; some features may be unavailable"
        )


ConfigScalar: TypeAlias = str | int | float | bool | None
ConfigValue: TypeAlias = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]
RawConfig: TypeAlias = Mapping[str, ConfigValue]
ConfigExtra: TypeAlias = MutableMapping[str, ConfigValue]
ConfigKeyNames: TypeAlias = list[str] | tuple[str, ...]


class PluginConfig(Protocol):
    project_name: str
    version: str
    output_dir: str
    project_dir: str
    extra: ConfigExtra


@dataclass(frozen=True)
class PluginDocument:
    """A Markdown source contributed to Folio's normal document pipeline.

    ``unlisted`` delists the page from the docs sidebar and nothing else: it
    still compiles at its route and enters search, the sitemap, ``llms.txt``,
    and the Markdown mirrors. For plugin output that answers to a URL without
    belonging to the documentation's own table of contents.
    """

    source: Path
    route: str
    unlisted: bool = False


def normalize_config_key_names(result: object) -> ConfigKeyNames:
    if not isinstance(result, (list, tuple)):
        raise TypeError("config_keys() must return a list or tuple of strings")
    if not all(isinstance(key, str) for key in result):
        raise TypeError("config_keys() must return only string keys")
    return result


class FolioPlugin(Protocol):
    """Namespace scanned by pluggy for decorated hook implementations."""

    def __dir__(self) -> Iterable[str]: ...


class AssetBuilder(Protocol):
    build_dir: Path
    output_dir: Path

    def page_exists(self, route: str) -> bool: ...

    def read_page(self, route: str) -> str: ...

    def write_page(self, route: str, content: str) -> None: ...

    def remove_page(self, route: str) -> None: ...

    def list_pages(self, prefix: str) -> list[str]: ...

    def register_route(self, route: str) -> None: ...

    def copy_static_asset(self, relative: str, source: Path) -> None: ...

    def remove_static_tree(self, relative: str) -> None: ...

    def emitted_routes(self) -> set[str]: ...

    def write_meta(self, directory: str, meta_json: str) -> None: ...

    def read_meta(self, directory: str) -> str: ...

    def write_llm_files(
        self, llms_txt: str | None = None, llms_full_txt: str | None = None
    ) -> None: ...


class HookSpec:
    @hookspec
    def config_keys(self) -> ConfigKeyNames: ...

    @hookspec
    def configure(self, config: PluginConfig, raw_config: RawConfig) -> None: ...

    @hookspec
    def register_extensions(
        self,
        registry: ExtensionRegistry,
        config: PluginConfig,
    ) -> None: ...

    @hookspec
    def register_components(self, registry: ExtensionRegistry) -> None: ...

    @hookspec
    def collect_docs(self, config: PluginConfig) -> Iterable[PluginDocument]: ...

    @hookspec
    def post_build(self, site_dir: str) -> None: ...

    @hookspec
    def emit_assets(self, builder: AssetBuilder, config: PluginConfig) -> None: ...

    @hookspec
    def watch_paths(self, config: PluginConfig) -> Iterable[str]: ...

    @hookspec
    def on_watched_change(
        self,
        builder: AssetBuilder,
        config: PluginConfig,
        path: str,
        change: str,
    ) -> bool: ...

    @hookspec
    def register_cli(self, app: object) -> None: ...


class PluginHookError(Exception):
    """A plugin raised while a fail-fast hook was being dispatched.

    Carries the user-facing plugin label and the hook name so the top-level
    build error attributes the failure to the offending plugin.
    """

    def __init__(
        self, plugin_label: str, hook_name: str, original: BaseException
    ) -> None:
        self.plugin_label = plugin_label
        self.hook_name = hook_name
        self.original = original
        super().__init__(
            f"Plugin '{plugin_label}' failed in hook '{hook_name}': {original}"
        )


class PluginManager:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.pm = pluggy.PluginManager(PROJECT_NAME)
        self.pm.add_hookspecs(HookSpec)
        self.base_dir = base_dir.resolve() if base_dir else None
        # canonical pluggy name -> user-facing config string (for attribution)
        self.plugin_labels: dict[str, str] = {}

    def register(self, plugin: FolioPlugin, name: str | None = None) -> str | None:
        label = name or getattr(plugin, "__name__", None) or type(plugin).__name__
        check_plugin_api_version(getattr(plugin, "FOLIO_PLUGIN_API", None), label)
        canonical = self.pm.register(plugin, name=name)
        self._reject_wrapper_hookimpls(plugin, label)
        return canonical

    def call_isolated(
        self,
        hook_name: str,
        *,
        policy: HookPolicy = "fail_fast",
        on_warn: Callable[[str], None] | None = None,
        impl_guard: Callable[[], Callable[[], None]] | None = None,
        **kwargs: object,
    ) -> list[object]:
        """Dispatch a hook one implementation at a time with failure isolation.

        ``policy='fail_fast'`` re-raises the first failure as a
        :class:`PluginHookError` (use for config/registration hooks where a
        broken plugin would silently corrupt output). ``policy='warn_skip'``
        reports the failure via ``on_warn`` (or :mod:`warnings`) and continues
        (use for asset-emit/finalization hooks). Results are returned in the
        same order pluggy's broadcast would produce.

        ``impl_guard``, when given, is called immediately before each hookimpl
        runs and returns a rollback callable; if that impl raises under
        ``warn_skip``, the rollback is invoked before continuing. Under
        ``fail_fast`` the exception propagates and no rollback runs.
        """
        if policy not in _HOOK_POLICIES:
            raise ValueError(
                f"call_isolated: unknown policy {policy!r}; "
                f"expected one of {_HOOK_POLICIES}"
            )
        caller = getattr(self.pm.hook, hook_name)
        results: list[object] = []
        for impl in reversed(caller.get_hookimpls()):
            if getattr(impl, "hookwrapper", False) or getattr(impl, "wrapper", False):
                raise PluginHookError(
                    self._plugin_label(impl),
                    hook_name,
                    TypeError(_WRAPPER_UNSUPPORTED_MESSAGE),
                )
            filtered = {k: v for k, v in kwargs.items() if k in impl.argnames}
            rollback = impl_guard() if impl_guard is not None else None
            try:
                result = impl.function(**filtered)
            except Exception as exc:
                label = self._plugin_label(impl)
                if policy == "fail_fast":
                    raise PluginHookError(label, hook_name, exc) from exc
                if rollback is not None:
                    rollback()
                message = (
                    f"Plugin '{label}' failed in hook '{hook_name}': {exc} (skipped)"
                )
                if on_warn is not None:
                    on_warn(message)
                else:
                    warnings.warn(message)
                continue
            if result is not None:
                results.append(result)
        return results

    def _reject_wrapper_hookimpls(self, plugin: object, label: str) -> None:
        """Refuse hookwrapper/wrapper hookimpls loudly at registration time.

        folio's :meth:`call_isolated` invokes each hookimpl as a plain
        function, which would silently turn a pluggy wrapper into a no-op
        (an un-started generator). Fail at load instead.
        """
        for caller in self.pm.get_hookcallers(plugin) or []:
            for impl in caller.get_hookimpls():
                if impl.plugin is not plugin:
                    continue
                if getattr(impl, "hookwrapper", False) or getattr(
                    impl, "wrapper", False
                ):
                    self.pm.unregister(plugin)
                    raise PluginHookError(
                        label,
                        caller.name,
                        TypeError(_WRAPPER_UNSUPPORTED_MESSAGE),
                    )

    def _plugin_label(self, impl: object) -> str:
        plugin = getattr(impl, "plugin", None)
        name: str | None = None
        try:
            name = self.pm.get_name(plugin)
        except Exception:
            name = getattr(impl, "plugin_name", None)
        if name is None:
            return repr(plugin)
        return self.plugin_labels.get(name, name)

    def load_default_plugins(self) -> None:
        """Register the first-party :data:`DEFAULT_PLUGINS`.

        Bundled defaults are imported directly by module path — never through
        the ``folio`` entry-point lookup used for ``plugins:`` entries — so an
        installed distribution declaring an entry point named after a default
        plugin (e.g. ``folio.plugins.landing``) can never shadow the
        first-party module. A default plugin that fails to load degrades to a
        warning instead of raising: builds and CLI startup of projects that
        never asked for the plugin must not break because of it.
        """
        for name in DEFAULT_PLUGINS:
            try:
                mod = importlib.import_module(name)
                self._register_plugin_module(mod, name)
            except Exception as exc:
                warnings.warn(f"Skipping default plugin '{name}': {exc}")

    def load_plugins(
        self, plugin_names: list[str], base_dir: Path | None = None
    ) -> None:
        root = (base_dir or self.base_dir or Path.cwd()).resolve()
        for name in plugin_names:
            try:
                if _is_file_plugin(name):
                    plugin_path = Path(name)
                    if not plugin_path.is_absolute():
                        plugin_path = root / plugin_path
                    plugin_path = plugin_path.resolve()
                    if not plugin_path.is_relative_to(root):
                        raise ValueError(
                            f"Plugin path '{name}' resolves outside the project directory"
                        )
                    if not plugin_path.is_file():
                        raise FileNotFoundError(plugin_path)
                    module_name = _module_name_for_path(plugin_path)
                    spec = importlib.util.spec_from_file_location(
                        module_name, str(plugin_path)
                    )
                    if spec is None or spec.loader is None:
                        raise RuntimeError(f"Cannot load plugin file: {plugin_path}")
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self._register_plugin_module(mod, name)
                else:
                    entry_point = _find_entry_point(name)
                    if entry_point is not None:
                        if _module_is_importable(name):
                            dist = _entry_point_dist_name(entry_point) or (
                                "<unknown distribution>"
                            )
                            warnings.warn(
                                f"Plugin name '{name}' matches both the installed "
                                f"entry point from distribution '{dist}' and an "
                                f"importable module '{name}'; loading the entry point",
                                UserWarning,
                            )
                        mod = entry_point.load()
                    else:
                        mod = importlib.import_module(name)
                    self._register_plugin_module(mod, name)
            except Exception as e:
                raise RuntimeError(f"Failed to load plugin '{name}': {e}") from e

    def _register_plugin_module(self, mod: object, name: str) -> None:
        check_plugin_api_version(getattr(mod, "FOLIO_PLUGIN_API", None), name)
        canonical = self.pm.register(mod)
        if canonical:
            self.plugin_labels[canonical] = name
        self._reject_wrapper_hookimpls(mod, name)


def _find_entry_point(name: str) -> object | None:
    """Return the installed ``folio`` entry point matching ``name``, if any.

    Entry-point plugins are only loaded when explicitly listed in ``plugins:``
    (opt-in); installed packages are never auto-activated without consent.
    When multiple installed distributions declare the same entry-point name,
    the one from the alphabetically first distribution wins (deterministic)
    and a ``UserWarning`` names all contenders.
    """
    try:
        entry_points = importlib.metadata.entry_points(group=PROJECT_NAME)
    except TypeError:  # pragma: no cover - Python < 3.10 selection API
        entry_points = importlib.metadata.entry_points().get(PROJECT_NAME, [])
    matches = [entry_point for entry_point in entry_points if entry_point.name == name]
    if not matches:
        return None
    if len(matches) > 1:
        matches.sort(key=_entry_point_dist_name)
        contenders = ", ".join(
            _entry_point_dist_name(entry_point) or "<unknown distribution>"
            for entry_point in matches
        )
        chosen = _entry_point_dist_name(matches[0]) or "<unknown distribution>"
        warnings.warn(
            f"Multiple installed distributions declare a folio entry point "
            f"named '{name}' ({contenders}); using the one from '{chosen}'",
            UserWarning,
        )
    return matches[0]


def _entry_point_dist_name(entry_point: object) -> str:
    dist = getattr(entry_point, "dist", None)
    return getattr(dist, "name", "") or ""


def _module_is_importable(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _is_file_plugin(name: str) -> bool:
    return name.startswith(("./", "../", "/")) or name.endswith(".py")


def _module_name_for_path(path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    return f"{PROJECT_NAME}_local_plugin_{digest}"
