from folio.generator.mdx_writer import module_to_mdx
from folio.generator.xref import build_symbol_index, resolve_type_link
from folio.ir import (
    ArgIR,
    ClassIR,
    DocstringIR,
    FunctionIR,
    ModuleIR,
    ReturnIR,
)


def _make_module(
    name: str,
    classes: list[ClassIR] | None = None,
    functions: list[FunctionIR] | None = None,
) -> ModuleIR:
    return ModuleIR(
        name=name,
        docstring=DocstringIR(short_description=""),
        classes=classes or [],
        functions=functions or [],
        constants=[],
        source_file=f"{name.replace('.', '/')}.py",
    )


def _make_class(
    name: str,
    bases: list[str] | None = None,
    inner_classes: list[ClassIR] | None = None,
) -> ClassIR:
    return ClassIR(
        name=name,
        bases=bases or [],
        decorators=[],
        docstring=DocstringIR(short_description=""),
        methods=[],
        class_vars=[],
        inner_classes=inner_classes or [],
        source_file="test.py",
        line_number=1,
    )


def _make_function(name: str) -> FunctionIR:
    return FunctionIR(
        name=name,
        args=[],
        returns=None,
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description=""),
        is_async=False,
        source_file="test.py",
        line_number=1,
    )


def _sample_modules() -> list[ModuleIR]:
    return [
        _make_module(
            "folio.config",
            classes=[_make_class("Config")],
            functions=[_make_function("load_config")],
        ),
        _make_module(
            "folio.ir",
            classes=[
                _make_class("ModuleIR"),
                _make_class("FunctionIR"),
                _make_class("ClassIR", inner_classes=[_make_class("Meta")]),
            ],
        ),
        _make_module(
            "folio.build",
            functions=[_make_function("run_build")],
        ),
    ]


class TestBuildSymbolIndex:
    def test_indexes_modules(self):
        index = build_symbol_index(_sample_modules())
        assert "folio.config" in index
        assert index["folio.config"] == "/docs/api-reference/folio/config"

    def test_uses_configured_docs_route_base(self):
        index = build_symbol_index(_sample_modules(), docs_route_base="/reference/docs")

        assert index["folio.config"] == "/reference/docs/api-reference/folio/config"
        assert (
            index["folio.config.Config"]
            == "/reference/docs/api-reference/folio/config#config"
        )

    def test_indexes_classes(self):
        index = build_symbol_index(_sample_modules())
        assert "folio.config.Config" in index
        assert index["folio.config.Config"] == "/docs/api-reference/folio/config#config"

    def test_indexes_functions(self):
        index = build_symbol_index(_sample_modules())
        assert "folio.config.load_config" in index
        assert (
            index["folio.config.load_config"]
            == "/docs/api-reference/folio/config#load_config"
        )

    def test_indexes_inner_classes(self):
        index = build_symbol_index(_sample_modules())
        assert "folio.ir.ClassIR.Meta" in index
        assert index["folio.ir.ClassIR.Meta"] == "/docs/api-reference/folio/ir#meta"

    def test_empty_modules(self):
        index = build_symbol_index([])
        assert index == {}


class TestResolveTypeLink:
    def setup_method(self):
        self.index = build_symbol_index(_sample_modules())

    def test_fully_qualified_name(self):
        url = resolve_type_link("folio.config.Config", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_simple_name_in_current_module(self):
        url = resolve_type_link("Config", self.index, "folio.config")
        assert url == "/docs/api-reference/folio/config#config"

    def test_simple_name_search_all_modules(self):
        # Config is unique across all modules, so it should be found
        url = resolve_type_link("Config", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_generic_type_list(self):
        url = resolve_type_link("list[Config]", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_generic_type_optional(self):
        url = resolve_type_link("Optional[Config]", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_union_type_with_none(self):
        url = resolve_type_link("Config | None", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_dict_with_two_known_types_returns_none(self):
        # dict[ModuleIR, Config] has two known types -- ambiguous
        url = resolve_type_link("dict[ModuleIR, Config]", self.index, "folio.build")
        assert url is None

    def test_dict_with_builtin_key(self):
        # dict[str, Config] -- str is builtin, Config is the only candidate
        url = resolve_type_link("dict[str, Config]", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_builtin_type_returns_none(self):
        url = resolve_type_link("str", self.index, "folio.config")
        assert url is None

    def test_none_type_returns_none(self):
        url = resolve_type_link("None", self.index, "folio.config")
        assert url is None

    def test_unknown_type_returns_none(self):
        url = resolve_type_link("SomethingUnknown", self.index, "folio.config")
        assert url is None

    def test_empty_string_returns_none(self):
        url = resolve_type_link("", self.index, "folio.config")
        assert url is None

    def test_list_of_builtin_returns_none(self):
        url = resolve_type_link("list[str]", self.index, "folio.config")
        assert url is None

    def test_nested_generic(self):
        url = resolve_type_link("list[Optional[Config]]", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config#config"

    def test_parent_package_lookup(self):
        # From folio.config, look up FunctionIR (in folio.ir)
        # It won't match folio.config.FunctionIR, but folio.FunctionIR won't match either.
        # It should find it via suffix search since FunctionIR is unique.
        url = resolve_type_link("FunctionIR", self.index, "folio.config")
        assert url == "/docs/api-reference/folio/ir#functionir"

    def test_module_name_as_type(self):
        url = resolve_type_link("folio.config", self.index, "folio.build")
        assert url == "/docs/api-reference/folio/config"

    def test_ambiguous_name_returns_none(self):
        # Create modules where 'Helper' exists in two modules
        modules = [
            _make_module("pkg.a", classes=[_make_class("Helper")]),
            _make_module("pkg.b", classes=[_make_class("Helper")]),
        ]
        index = build_symbol_index(modules)
        url = resolve_type_link("Helper", index, "pkg.c")
        assert url is None

    def test_ambiguous_name_resolved_by_current_module(self):
        # Same name in two modules, but current_module matches one
        modules = [
            _make_module("pkg.a", classes=[_make_class("Helper")]),
            _make_module("pkg.b", classes=[_make_class("Helper")]),
        ]
        index = build_symbol_index(modules)
        url = resolve_type_link("Helper", index, "pkg.a")
        assert url == "/docs/api-reference/pkg/a#helper"


class TestMdxWriterCrossReferences:
    """Integration tests: verify cross-reference links appear in generated MDX."""

    def _build_modules(self):
        config_cls = _make_class("Config")
        config_mod = _make_module("mylib.config", classes=[config_cls])

        use_func = FunctionIR(
            name="process",
            args=[
                ArgIR(
                    name="cfg",
                    type="Config",
                    default=None,
                    description="The config.",
                    kind="regular",
                ),
                ArgIR(
                    name="name",
                    type="str",
                    default=None,
                    description="A name.",
                    kind="regular",
                ),
            ],
            returns=ReturnIR(type="Config", description="Updated config."),
            raises=[],
            decorators=[],
            docstring=DocstringIR(short_description="Process something."),
            is_async=False,
            source_file="test.py",
            line_number=1,
        )
        core_mod = _make_module("mylib.core", functions=[use_func])

        child_cls = ClassIR(
            name="SpecialConfig",
            bases=["Config"],
            decorators=[],
            docstring=DocstringIR(short_description="A special config."),
            methods=[],
            class_vars=[],
            source_file="test.py",
            line_number=1,
        )
        child_mod = _make_module("mylib.special", classes=[child_cls])

        return [config_mod, core_mod, child_mod]

    def test_param_table_includes_href(self):
        modules = self._build_modules()
        index = build_symbol_index(modules)
        core_mod = modules[1]
        mdx = module_to_mdx(core_mod, symbol_index=index)
        # The ParamTable JSON should contain an href for the Config type
        assert '"href": "/docs/api-reference/mylib/config#config"' in mdx

    def test_param_table_no_href_for_builtins(self):
        modules = self._build_modules()
        index = build_symbol_index(modules)
        core_mod = modules[1]
        mdx = module_to_mdx(core_mod, symbol_index=index)
        # The "str" param should NOT have an href
        assert '"type": "str"' in mdx
        # Verify no href appears right after the str type entry
        import json

        # Parse the ParamTable args to check
        param_start = mdx.index("<ParamTable args={") + len("<ParamTable args={")
        param_end = mdx.index("} />", param_start)
        args_json = mdx[param_start:param_end]
        args = json.loads(args_json)
        str_arg = [a for a in args if a["type"] == "str"][0]
        assert "href" not in str_arg

    def test_return_type_linked(self):
        modules = self._build_modules()
        index = build_symbol_index(modules)
        core_mod = modules[1]
        mdx = module_to_mdx(core_mod, symbol_index=index)
        assert "[`Config`](/docs/api-reference/mylib/config#config)" in mdx
        assert "**Returns:**" in mdx

    def test_base_class_linked(self):
        modules = self._build_modules()
        index = build_symbol_index(modules)
        special_mod = modules[2]
        mdx = module_to_mdx(special_mod, symbol_index=index)
        # The ClassOverview should have bases as objects with href
        assert '"href": "/docs/api-reference/mylib/config#config"' in mdx

    def test_no_symbol_index_no_links(self):
        modules = self._build_modules()
        core_mod = modules[1]
        mdx = module_to_mdx(core_mod)
        # Without symbol_index, no href should appear
        assert "href" not in mdx
        assert "**Returns:** `Config`" in mdx

    def test_class_bases_remain_strings_without_index(self):
        modules = self._build_modules()
        special_mod = modules[2]
        mdx = module_to_mdx(special_mod)
        # Without symbol_index, bases should be plain string array
        assert 'bases={["Config"]}' in mdx
