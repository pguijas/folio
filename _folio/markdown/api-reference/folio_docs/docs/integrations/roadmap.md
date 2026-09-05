# folio_docs.docs.integrations.roadmap 

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

### `register_extensions` 

```python
def register_extensions(registry: Any, config: Any) -> None
```

**Returns:** `None` - 

### `emit_assets` 

```python
def emit_assets(builder: Any, config: Any) -> None
```

Compatibility hook for generated docs pages.

Public routes and data modules are emitted through register_extensions().

**Returns:** `None` - 

### `board_href` 

```python
def board_href(board_path: str, depth: int) -> str
```

Href to the public board from a view ``depth`` segments below the root.

The roadmap sits at /roadmap, so ``depth`` is 1 today. It is a parameter
rather than a constant because the caller knows the route and this helper
does not, and a hard-coded single ``../`` was already wrong once.

**Returns:** `str` - 

### `project_keys` 

```python
def project_keys(phases: Any) -> list[str]
```

Distinct project values, in the order their first phase appears.

A phase without a ``project`` belongs to the default one, which is what
the Roadmap component groups it under too.

**Returns:** `list[str]` - 

### `ordered_project_keys` 

```python
def ordered_project_keys(phases: Any, projects: dict[str, dict[str, str]]) -> list[str]
```

Project keys that have phases, in the order the page should show them.

Project order is visible state — the order the groups are drawn in — so
``projects:`` declaration order in docs.yaml is the authority. A key that
has phases but no ``projects:`` entry keeps its first-appearance order,
after the declared ones. Declared keys with no phases are left out: there
is nothing to draw.

**Returns:** `list[str]` - 

### `project_block` 

```python
def project_block(roadmap: dict[str, Any]) -> dict[str, dict[str, str]]
```

``{key: {label, description}}`` for the projects the page will draw.

A project with any configured field is included; one with none is left
out entirely, because the component already falls back to the key. The
filter is on "has any field" rather than "has a label" so a project
described but not labelled still reaches the page.

**Returns:** `dict[str, dict[str, str]]` - 

### `normalize_projects` 

```python
def normalize_projects(raw_projects: Any) -> dict[str, dict[str, str]]
```

**Returns:** `dict[str, dict[str, str]]` - 

### `empty_roadmap` 

```python
def empty_roadmap() -> dict[str, Any]
```

An inert roadmap carrying every key a normalized one has.

Callers index the result (``roadmap["description"]``), so the empty
shape and the parsed shape have to agree on their keys; they drifted
once already.

**Returns:** `dict[str, Any]` - 

### `normalize_roadmap` 

```python
def normalize_roadmap(raw_roadmap: Any) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `active_roadmap` 

```python
def active_roadmap(config: Any) -> dict[str, Any] | None
```

The normalized roadmap config, or None when the plugin is inactive.

The plugin loads for every build (it is a default plugin) but only a
``roadmap:`` section in docs.yaml — surfaced as ``config.extra["roadmap"]``
by configure() — activates its output.

**Returns:** `dict[str, Any] | None` - 

### `get_roadmap` 

```python
def get_roadmap(config: Any) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `get_phases` 

```python
def get_phases(config: Any) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `docs_page_mdx` 

```python
def docs_page_mdx() -> str
```

**Returns:** `str` - 

### `register_cli` 

```python
def register_cli(app: Any) -> None
```

**Returns:** `None` -
