# folio_docs.docs.integrations.landing 

First-party Folio Docs landing integration.

The landing feature ships as a **default plugin** (see ``DEFAULT_PLUGINS`` in
``folio/plugin.py``): it is loaded for every build and stays inert until a
``landing:`` key appears in docs.yaml. ``configure()`` is the single owner of
the key — core ``folio_docs/config.py`` no longer parses it — and populates the
``Config.landing_*`` fields consumed downstream by the core template injector.

Ownership seam (why there is no ``register_extensions``/``emit_assets`` here):
the rendered page intentionally stays in the bundled template
(``template/app/page.tsx`` + ``template/components/landing*.tsx``), specialized
by marker replacement in ``TemplateConfigInjector._inject_landing_page`` during
``SiteBuilder.prepare()``. That injection runs *before* any plugin emission
hook, and the disabled-path fallback (docs index at ``/``) plus the coupled
``__DOCS_INDEX_CANONICAL_PATH__`` / ``__INCLUDE_DOCS_INDEX__`` markers must be
written even when this plugin is inert, so no public hook can take that
emission over without breaking the documented template contract
(``docs/guide/theming/custom-templates.md``). The plugin therefore owns the
config surface; the injector reads the fields this hook sets at
``load_config`` time, which happens before ``prepare()``.

## Functions

### `config_keys` 

```python
def config_keys() -> list[str]
```

**Returns:** `list[str]` - 

### `configure` 

```python
def configure(config: Any, raw_config: dict[str, Any]) -> None
```

**Returns:** `None` - 

### `landing_enabled` 

```python
def landing_enabled(raw_landing: Any) -> bool
```

`landing: <bool>` shorthand, `enabled:` subkey (default true), else true.

**Returns:** `bool` - 

### `landing_hero_variant` 

```python
def landing_hero_variant(raw_variant: Any) -> str
```

**Returns:** `str` - 

### `landing_sections` 

```python
def landing_sections(raw_sections: Any) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_string` 

```python
def _string(value: Any, default: str = '') -> str
```

**Returns:** `str` - 

### `_safe_section_href` 

```python
def _safe_section_href(raw_value: Any, path: str, default: str) -> str
```

A config href validated by the shared scheme policy, or ``default``.

Landing sections are presentational, so unlike kanban card links an
unsafe or malformed href degrades to the default with a warning instead
of failing the build.

**Returns:** `str` - 

### `_normalize_heading_fields` 

```python
def _normalize_heading_fields(section: dict[str, Any]) -> None
```

Coerce shared heading fields in place: non-strings degrade to absent.

**Returns:** `None` - 

### `_normalize_stage` 

```python
def _normalize_stage(section: dict[str, Any]) -> None
```

Coerce the optional ``stage`` label in place: blank degrades to absent.

Any section (and the hero) may carry a short stage label ("The
mechanism"); the template numbers staged blocks at render time, so the
plugin only guarantees a non-empty stripped string. Non-string or
whitespace-only values delete the key, and the section renders without a
stage rail exactly as before.

**Returns:** `None` - 

### `_normalize_actions` 

```python
def _normalize_actions(section: dict[str, Any]) -> None
```

Coerce the optional ``actions`` list in place.

``actions`` is shared across section types rather than owned by one, so
normalizing it per type left ``cta`` unguarded: an entry without ``href``
reached the template and crashed the prerender on
``action.href.startsWith``. An action needs a title and a usable href;
anything else drops with a warning, like every other malformed row.

**Returns:** `None` - 

### `_normalize_hero_notice` 

```python
def _normalize_hero_notice(raw_notice: Any) -> dict[str, Any]
```

The hero's announcement chip: configured messages plus a link.

`text` is one plain string, or a list of up to three that the chip cycles
through (pure CSS in the template; reduced motion pins the first). Still
nothing derived — every message is written in docs.yaml. A notice without
usable text degrades to absent; the link passes the same href scheme
policy as every other configured link.

**Returns:** `dict[str, Any]` - 

### `_normalize_boards_section` 

```python
def _normalize_boards_section(section: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_normalize_mechanism_section` 

```python
def _normalize_mechanism_section(section: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_normalize_statement_section` 

```python
def _normalize_statement_section(section: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_labeled_entries` 

```python
def _labeled_entries(raw_entries: Any, key: str, *, allow_icon: bool = False) -> list[dict[str, str]]
```

Clean a list of ``{key, detail}`` mappings; entries without ``key`` drop.

**Returns:** `list[dict[str, str]]` - 

### `_normalize_harness_section` 

```python
def _normalize_harness_section(section: dict[str, Any]) -> dict[str, Any]
```

The two product surfaces plus the meta-harness relationship.

The bundled template owns useful defaults, so omitted lists stay empty and
trigger that copy there. Config can replace every label without introducing
a new vocabulary or implying that Folio controls the harnesses it wraps.

**Returns:** `dict[str, Any]` - 

### `_normalize_funnel_section` 

```python
def _normalize_funnel_section(section: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_normalize_features_section` 

```python
def _normalize_features_section(section: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_normalize_cells_section` 

```python
def _normalize_cells_section(section: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_warn_builtin_comparison` 

```python
def _warn_builtin_comparison(source: str) -> None
```

**Returns:** `None` - 

### `_comparison_value` 

```python
def _comparison_value(raw_value: Any) -> bool | str
```

One matrix cell: yes (``True``), no (``False``) or partial (``"~"``).

An unrecognized value reads as partial rather than as a yes or a no, so a
malformed cell never invents a claim about a named tool. YAML parses a
bare ``~`` as null, so ``values: [true, ~]`` arrives here as ``None`` and
lands on partial, which is what the tilde means in the table anyway.

**Returns:** `bool | str` - 

### `_comparison_tools` 

```python
def _comparison_tools(raw_tools: Any) -> list[str]
```

The column names; blanks and non-strings drop.

**Returns:** `list[str]` - 

### `_comparison_rows` 

```python
def _comparison_rows(raw_rows: Any, tool_count: int) -> list[dict[str, Any]]
```

Rows carrying exactly one value per tool; anything else drops.

A row whose value count disagrees with ``tools`` would slide every cell
under the wrong column, so it is dropped with a warning instead of being
padded into a claim nobody wrote.

**Returns:** `list[dict[str, Any]]` - 

### `_comparison_table` 

```python
def _comparison_table(raw_table: Any) -> dict[str, Any]
```

``{caption, tools, rows}`` from a config mapping, or ``{}`` if unusable.

**Returns:** `dict[str, Any]` - 

### `landing_comparison` 

```python
def landing_comparison(raw_comparison: Any) -> bool | dict[str, Any]
```

Normalize ``landing.comparison``: the project's own table, or the bool.

Returns ``{caption, tools, rows}`` for a configured table, ``True`` for
the deprecated bool that renders Folio's bundled matrix, and ``False``
when the key is off, absent, or leaves nothing to render.

**Returns:** `bool | dict[str, Any]` - 

### `_normalize_comparison_section` 

```python
def _normalize_comparison_section(section: dict[str, Any]) -> dict[str, Any]
```

A comparison section carrying the project's own table.

The table sits on the section under the same keys as ``landing.comparison``
(``caption``, ``tools``, ``rows``). A section without a usable table keeps
rendering the deprecated built-in matrix, so the keys are dropped rather
than handed to the template as an empty shell.

**Returns:** `dict[str, Any]` - 

### `_mapping` 

```python
def _mapping(value: Any) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `normalize_landing` 

```python
def normalize_landing(raw_landing: Any) -> dict[str, Any]
```

Normalize a raw ``landing:`` section into its canonical mapping.

Accepts the bool shorthand (``landing: false``) and tolerates non-mapping
values anywhere in the tree (they degrade to defaults). Defaults mirror
the pre-plugin core parser exactly: hero variant ``docs-map``, primary CTA
``Get Started``/``/docs``, empty secondary CTA, empty install/feature/
section lists, and the comparison section off unless the project fills in
its own table.

**Returns:** `dict[str, Any]` -
