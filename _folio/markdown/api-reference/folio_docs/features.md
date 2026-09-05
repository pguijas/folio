# folio_docs.features 

## Functions

### `_experimental_features` 

```python
def _experimental_features(env: Mapping[str, str] | None = None) -> frozenset[str]
```

Feature names enabled via the FOLIO_EXPERIMENTAL environment variable.

**Returns:** `frozenset[str]` - 

### `is_feature_enabled` 

```python
def is_feature_enabled(feature: str, env: Mapping[str, str] | None = None) -> bool
```

**Returns:** `bool` - 

### `experimental_feature_state` 

```python
def experimental_feature_state(env: Mapping[str, str] | None = None) -> str
```

**Returns:** `str` - 

### `disabled_doc_feature_for_route` 

```python
def disabled_doc_feature_for_route(route: str, env: Mapping[str, str] | None = None) -> str | None
```

Feature gating ``route``, or ``None`` when the page may be published.

A route stays gated only while its feature is off, so a feature enabled
through ``FOLIO_EXPERIMENTAL`` publishes its pages instead of leaving
them out of navigation, search, and the llms output.

**Returns:** `str | None` - 

### `disabled_api_feature_for_module` 

```python
def disabled_api_feature_for_module(module_name: str, env: Mapping[str, str] | None = None) -> str | None
```

Feature gating ``module_name``'s API pages, or ``None`` when publishable.

Membership in the map is itself the gate — unlike ``is_feature_enabled``,
which only gates names listed in ``MVP_DISABLED_FEATURES``. Only naming the
feature in ``FOLIO_EXPERIMENTAL`` publishes the module.

**Returns:** `str | None` - 

### `disabled_feature_message` 

```python
def disabled_feature_message(feature: str) -> str
```

**Returns:** `str` -
