# folio_docs.branding 

## Functions

### `_center_text` 

```python
def _center_text(line: str, width: int | None) -> str
```

**Returns:** `str` - 

### `folio_news_item` 

```python
def folio_news_item(elapsed_seconds: float = 0, *, interval: float = 1.0) -> str
```

**Returns:** `str` - 

### `current_folio_news_item` 

```python
def current_folio_news_item() -> str
```

**Returns:** `str` - 

### `folio_news_line` 

```python
def folio_news_line(*, width: int | None = None, news_item: str | None = None) -> str
```

**Returns:** `str` - 

### `folio_banner` 

```python
def folio_banner(version: str = '', *, width: int | None = None, news_item: str | None = None, include_news: bool = True) -> str
```

**Returns:** `str` -
