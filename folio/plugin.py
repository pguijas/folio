from __future__ import annotations

import hashlib
import importlib
import importlib.util
from collections.abc import Iterable, Mapping, MutableMapping
from pathlib import Path
from typing import Protocol, TypeAlias

import pluggy

from folio.extensions import ExtensionRegistry

PROJECT_NAME = "folio"

hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)

ConfigScalar: TypeAlias = str | int | float | bool | None
ConfigValue: TypeAlias = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]
RawConfig: TypeAlias = Mapping[str, ConfigValue]
ConfigExtra: TypeAlias = MutableMapping[str, ConfigValue]
ConfigKeyNames: TypeAlias = list[str] | tuple[str, ...]


class PluginConfig(Protocol):
    project_name: str
    version: str
    output_dir: str
    extra: ConfigExtra


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

    def write_page(self, route: str, content: str) -> None: ...

    def write_meta(self, directory: str, meta_json: str) -> None: ...

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
    def post_build(self, site_dir: str) -> None: ...

    @hookspec
    def emit_assets(self, builder: AssetBuilder, config: PluginConfig) -> None: ...


class PluginManager:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.pm = pluggy.PluginManager(PROJECT_NAME)
        self.pm.add_hookspecs(HookSpec)
        self.base_dir = base_dir.resolve() if base_dir else None

    def register(self, plugin: FolioPlugin) -> None:
        self.pm.register(plugin)

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
                    self.pm.register(mod)
                else:
                    mod = importlib.import_module(name)
                    self.pm.register(mod)
            except Exception as e:
                raise RuntimeError(f"Failed to load plugin '{name}': {e}") from e


def _is_file_plugin(name: str) -> bool:
    return name.startswith(("./", "../", "/")) or name.endswith(".py")


def _module_name_for_path(path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    return f"{PROJECT_NAME}_local_plugin_{digest}"
