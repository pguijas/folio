# folio_agents.integrations.kanban 

Optional Folio Docs adapter for the ``kanban:`` configuration key.

The board is git-persisted: its committed cardfiles are the source of truth.
In the browser, cards can be dragged between columns; moves are stored as a
localStorage overlay keyed to the committed board, and the exports produce
ready-to-commit move commands that close the loop. Columns are loaded from
a cardfile directory named by ``kanban.source`` or from the independent
canvases in ``kanban.sources``. ``kanban.ref`` can resolve those directories
through a managed Git worktree. The ``kanban.routes.public`` setting accepts
a path to choose where the board view is published (``"/"`` for the front
page).

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

### `_resolve_card_paths` 

```python
def _resolve_card_paths(kanban: dict[str, Any]) -> None
```

Fill each card's ``file``: where it lives, as a project-relative path.

A path, never a URL. This used to be two hosting-provider links —
``{repo}/blob/...`` for the path chip and ``{repo}/edit/...`` behind the
dialog's pen — so "edit this card" navigated to a web editor nobody edits
in, and to the wrong place entirely for a board that is not on that
provider. Artifact and trail refs were resolved the same way.

The board is operated locally, through the CLI and an editor, so the honest
answer to "where do I change this" is the path itself. Rendering it is the
reader's job; a static page cannot open an editor and should not pretend
otherwise.

**Returns:** `None` - 

### `_card_dir_for_card` 

```python
def _card_dir_for_card(kanban: dict[str, Any], card: dict[str, Any]) -> str
```

**Returns:** `str` - 

### `_docs_route_base` 

```python
def _docs_route_base(config: Any) -> str
```

Where content pages are served from, defaulting like the builder does.

**Returns:** `str` - 

### `_resolve_artifact_hrefs` 

```python
def _resolve_artifact_hrefs(kanban: dict[str, Any], *, docs_route_base: str, project_dir: Path, doc_sources: list[Path] | tuple[Path, ...] = (), warn_unreachable: bool = False) -> None
```

Give an artifact that names a published page or file somewhere to open.

A card may keep a directory of its own next to its markdown file —
``board/cards/<id>.md`` and ``board/cards/<id>/`` — and what is in it is
that card's own output: the prototype a decision was made on, the document
that compared them. ``emit_assets`` publishes that directory, so a ``doc:``
or ``file:`` artifact pointing into it becomes a link instead of a path the
reader has to go find. The whole directory is published, not only the
attached files, because those files reference each other: a prototype page
without its stylesheet opens as nothing.

Markdown resolves to the page it was built into, not to the file. It went
through the same parser and MDX writer as every documentation page, so
there is a real page to send the reader to, and sending them to the source
instead would be handing over an unstyled download of something the site
already renders. The same reasoning covers a ``doc:`` naming a file under
a docs source: the site publishes exactly that page, so the artifact links
to it.

Everywhere else, an artifact keeps the empty href it had and renders as
the path it is. Attaching a file is not a licence to publish an arbitrary
part of the repository — only what a card owns or the docs already
publish opens. Under ``warn_unreachable`` (configure's one pass, so a
build says it once) a ``doc:`` whose file exists but whose page nothing
publishes warns, naming the card and the target as written: a ``doc:``
promised a page, and the promise did not hold.

**Returns:** `None` - 

### `_docs_source_route` 

```python
def _docs_source_route(target: Path, doc_sources) -> str | None
```

The content route a docs source builds for ``target``, or ``None``.

The route rule is ``source_route``, the one ``parse_markdown_directory``
applies to every docs source — one rule, imported, so the two can never
drift. ``.md`` only: that is all a docs source reads.

**Returns:** `str | None` - 

### `_doc_source_dirs` 

```python
def _doc_source_dirs(config: Any, project_dir: Path) -> list[Path]
```

Docs source directories as resolved absolute paths.

``config.doc_sources`` is relative before ``resolve_paths`` runs and
absolute after; resolving against the project directory accepts both.

**Returns:** `list[Path]` - 

### `_owned_card_artifact` 

```python
def _owned_card_artifact(project_dir: Path, *, card_dir: str, card_id: str, target: str) -> Path | None
```

Return a safe card-relative target, or ``None`` when it is not owned.

**Returns:** `Path | None` - 

### `register_extensions` 

```python
def register_extensions(registry: Any, config: Any) -> None
```

**Returns:** `None` - 

### `collect_docs` 

```python
def collect_docs(config: Any) -> list[PluginDocument]
```

Contribute card-owned Markdown to Folio's core document pipeline.

**Returns:** [`list[PluginDocument]`](/docs/api-reference/folio_docs/plugin#plugindocument) - 

### `_iter_card_docs` 

```python
def _iter_card_docs(kanban: dict[str, Any], *, project_dir: Path)
```

Yield ``(card, source, route)`` for every markdown file a card owns.

One iteration feeds both ``collect_docs`` and the generated card index,
so the pages a card contributes and the pages its index lists cannot
drift apart.

### `watch_paths` 

```python
def watch_paths(config: Any) -> list[str]
```

The serve watcher asks what to watch beyond code and docs: a cardfile

board answers with its directory, so a card edited mid-serve reaches the
served board without a restart.

**Returns:** `list[str]` - 

### `on_watched_change` 

```python
def on_watched_change(builder: Any, config: Any, path: str, change: str) -> bool
```

Reload the board from disk when anything under it changes.

The whole board reloads rather than one card: membership, ordering, and
the column set all live across files, and a full load is the same work
the build does. A half-saved card raises out of ``normalize_kanban``;
the watcher's isolation degrades that to a warning and the next save
lands cleanly. Card-directory documents republish as raw assets here;
their compiled pages still come from a full build. The section is
reconstructed from ``config.extra``, not re-read from ``docs.yaml`` —
the config file is not watched, so config edits mid-serve still take a
restart.

**Returns:** `bool` - 

### `emit_assets` 

```python
def emit_assets(builder: Any, config: Any) -> None
```

**Returns:** `None` - 

### `_sync_board_page` 

```python
def _sync_board_page(builder: Any, kanban: dict[str, Any]) -> None
```

Write or refresh the generated board page at ``kanban/index``.

**Returns:** `None` - 

### `_sync_card_index_pages` 

```python
def _sync_card_index_pages(builder: Any, kanban: dict[str, Any], *, project_dir: Path, route_base: str, docs_route_on: bool) -> None
```

Keep every folder route above a card's documents resolvable.

A card's documents compile below its own folder route, and a folder whose
children exist is a URL readers will try — trimmed by hand or reached from
a breadcrumb. When the card ships no ``index.md``/``README.md`` of its
own, a marker-tagged index listing the card's documents fills the hole;
when it does, or when the documents are gone on a warm build, the
generated page steps aside. User-authored pages (no marker) are never
touched, matching the board page's contract one level down.

The ``kanban/cards/`` folder itself resolves to a directory of the
publishing cards. With the board's own docs page turned off the
``kanban/`` folder is a hole of the same kind, so ``kanban/index``
forwards to the public board when one exists and repeats the directory
when none does — a listing, not the board the configuration said no to.
With no documents at all the plugin's generated pages come down and the
namespace is silent, exactly as before.

**Returns:** `None` - 

### `_folders_above` 

```python
def _folders_above(routes: set[str], *, root: str) -> list[str]
```

Every folder route between a document and ``root``, nearest last.

``kanban/cards/one-card/sub/report`` contributes
``kanban/cards/one-card/sub`` and ``kanban/cards/one-card``; ``root``
itself is the caller's business and is never yielded.

**Returns:** `list[str]` - 

### `_user_owns_route` 

```python
def _user_owns_route(builder: Any, route: str) -> bool
```

Whether a page the plugin did not generate sits at ``route``.

An unreadable page counts as user-authored: when its content is unknown
the only safe reading is that it is not ours to shadow.

**Returns:** `bool` - 

### `_remove_stale_card_indexes` 

```python
def _remove_stale_card_indexes(builder: Any, *, keep: dict[str, str]) -> None
```

Drop generated card indexes whose card stopped publishing documents.

**Returns:** `None` - 

### `card_index_mdx` 

```python
def card_index_mdx(card: dict[str, Any], docs: list[tuple[Path, str]], *, route_base: str, status_title: str = '', project_root: Path | None = None, subtree: str | None = None) -> str
```

The folder page for a card's published output: tiles, not a list.

The card root gets the card's own voice — its status line, the first
paragraph of its description, and one tile per document and artifact. A
subtree folder stays lean: the documents below it, nothing else.

**Returns:** `str` - 

### `kanban_redirect_mdx` 

```python
def kanban_redirect_mdx(kanban: dict[str, Any], *, route_base: str) -> str
```

The parent folder page when the board lives at a public route.

Card documents compile below ``kanban/`` but are read from the board, so
the folder forwards there instead of indexing them. The target is written
relative to the folder's own depth — the page is served under the docs
route base, and a site base path must survive — and RedirectPage carries
query and hash across, the same contract the ``/kanban`` forwarder keeps.

**Returns:** `str` - 

### `kanban_directory_mdx` 

```python
def kanban_directory_mdx(kanban: dict[str, Any], docs_by_card: dict[str, dict[str, Any]], *, route_base: str) -> str
```

A folder page of one tile per publishing card.

Two routes use it. ``kanban/cards/index`` whenever anything publishes:
the documents compile below ``cards/``, so the folder resolves to what
it holds — what each card is about, straight from the card's own
description. And ``kanban/index`` when the board is published nowhere at
all, rather than the board component the configuration declined; with a
public route that folder forwards to the board instead
(:func:`kanban_redirect_mdx`).

**Returns:** `str` - 

### `_jsx_attr` 

```python
def _jsx_attr(value: str) -> str
```

Make a string safe inside a double-quoted MDX component attribute.

**Returns:** `str` - 

### `_plain_excerpt` 

```python
def _plain_excerpt(markdown_text: str, *, limit: int) -> str
```

The first paragraph as plain prose: markup off, one line, capped.

**Returns:** `str` - 

### `_doc_title` 

```python
def _doc_title(source: Path) -> str
```

The document's first heading, for a link that says what it opens.

**Returns:** `str` - 

### `_doc_excerpt` 

```python
def _doc_excerpt(source: Path) -> str
```

The document's first prose paragraph, flattened for a tile.

**Returns:** `str` - 

### `_publish_card_assets` 

```python
def _publish_card_assets(builder: Any, kanban: dict[str, Any], *, project_dir: Path) -> None
```

Publish each card's own directory under ``/_folio/kanban/``.

Everything in ``board/cards/<id>/`` goes up as it is on disk: the whole
directory, because the files in it reference each other and an attached
page without its stylesheet is not the page.

Markdown is the exception, and it is the point. A ``.md`` sibling is not a
file to download, it is a page the project wrote, so it goes through the
same pipeline every documentation page goes through — parsed, compiled to
MDX, themed, in the search index and in ``llms.txt``. It is still copied
here as source too, because a relative link from a prototype to it has to
resolve, and because the raw file is what an agent reads.

Two things never travel. A dotfile or dot-directory is session scratch by
convention (``.verify/`` full of screenshots is what prompted the rule),
and a symlink is refused rather than followed, so a link out of the
project cannot publish a file the project does not contain.

**Returns:** `None` - 

### `_iter_card_files` 

```python
def _iter_card_files(kanban: dict[str, Any], *, project_dir: Path)
```

Yield safe, visible files from directories owned by known cards.

### `_path_has_symlink` 

```python
def _path_has_symlink(root: Path, target: Path) -> bool
```

Whether a target path traverses any symlink below ``root``.

**Returns:** `bool` - 

### `_card_page_route` 

```python
def _card_page_route(card_id: str, relative: Path) -> str
```

Content route for one markdown file in a card's directory.

**Returns:** `str` - 

### `_read_page` 

```python
def _read_page(builder: Any, route: str) -> str | None
```

The page content on disk, or None when the builder cannot read pages.

**Returns:** `str | None` - 

### `_remove_generated_page` 

```python
def _remove_generated_page(builder: Any) -> None
```

Remove the plugin's own marker-tagged docs page, if one persists.

Only a page carrying the generated-page marker is removed; when the
builder cannot read or remove pages nothing happens (better a stale
plugin page than a deleted user page).

**Returns:** `None` - 

### `_remove_marker_page` 

```python
def _remove_marker_page(builder: Any, route: str) -> None
```

Remove one page, and only when it carries the generated-page marker.

**Returns:** `None` - 

### `_normalize_route_value` 

```python
def _normalize_route_value(value: Any) -> bool | str
```

Normalize a route value: bool stays bool, string becomes "/"-prefixed path, else bool().

**Returns:** `bool | str` - 

### `normalize_kanban` 

```python
def normalize_kanban(raw_kanban: Any, *, project_dir: Path) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_resolve_card_icons` 

```python
def _resolve_card_icons(columns: list[dict[str, Any]], icons: dict[str, str]) -> None
```

Stamp each card with the icon of its first mapped tag.

Resolution happens after every normalization pass because
``_normalize_card`` rebuilds card dicts from scratch: the icon is
derived data, like paths and artifact hrefs, never trusted from input.

**Returns:** `None` - 

### `_normalize_columns` 

```python
def _normalize_columns(raw_columns: list[Any]) -> list[dict[str, Any]]
```

Normalize columns and enforce board-wide unique card ids.

Cardfile boards get uniqueness for free (one file per id); duplicates
appearing elsewhere (synthesized ids, manual conflicts) are suffixed and
warned about rather than dropped.

**Returns:** `list[dict[str, Any]]` - 

### `_load_source_columns` 

```python
def _load_source_columns(raw_source: Any, *, source_root: Path, project_dir: Path, artifact_root: Path | None = None) -> tuple[list[Any], str, dict[str, str]]
```

Columns (and board title) from a cardfile board directory.

A cardfile board is a directory containing ``board.yaml`` + one Markdown
file per card under ``cards/`` (see ``kanban_board``). Any problem — a
non-string path, a path naming a file instead of a directory, or a missing
board directory — raises ``ValueError`` naming the resolved path.
``configure`` is dispatched fail-fast, so the build stops loudly instead
of shipping an empty or wrong board.

**Returns:** `tuple[list[Any], str, dict[str, str]]` - 

### `_load_multiple_sources` 

```python
def _load_multiple_sources(raw_sources: Any, *, source_root: Path, project_dir: Path) -> tuple[list[dict[str, Any]], str, dict[str, str], dict[str, str]]
```

Merge product-owned boards into one project-aware browser projection.

A card's own ``track`` is a workstream inside its product and is left
alone; the product it came from lands in ``project``. The two were one
field until now, and the merge silently overwrote whatever a card had
written with the name of its source.

**Returns:** `tuple[list[dict[str, Any]], str, dict[str, str], dict[str, str]]` - 

### `_rebase_artifact_targets` 

```python
def _rebase_artifact_targets(columns: list[dict[str, Any]], *, source_root: Path, project_dir: Path) -> None
```

Translate a product-relative artifact path into the host worktree.

**Returns:** `None` - 

### `_canonical_card_dir` 

```python
def _canonical_card_dir(path: Path, *, project_dir: Path) -> str
```

Canonical project-relative board directory, with no symlink traversal.

**Returns:** `str` - 

### `_normalize_column` 

```python
def _normalize_column(raw_column: Any, index: int) -> dict[str, Any] | None
```

**Returns:** `dict[str, Any] | None` - 

### `_normalize_card` 

```python
def _normalize_card(raw_card: Any, *, column_title: str) -> dict[str, Any] | None
```

**Returns:** `dict[str, Any] | None` - 

### `_normalize_artifacts` 

```python
def _normalize_artifacts(raw_artifacts: Any, *, column_title: str, title: str) -> list[dict[str, Any]]
```

Typed artifact refs -&gt; ``{kind, target, display, label, href}``.

Accepts both the committed one-line form (``- doc: research/x.md``) and
the already-normalized form, so re-normalization is idempotent. ``url``
targets go through the shared href scheme policy (fail-fast on
``javascript:``/``data:``); repo-relative kinds get their href filled in
by ``configure`` once the project repo URL is known. ``display`` is the
target as the author wrote it, set by the board loader; where it is
absent (a project plugin's override) the target is what was written.

**Returns:** `list[dict[str, Any]]` - 

### `_normalize_criteria` 

```python
def _normalize_criteria(raw_criteria: Any) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_normalize_trail` 

```python
def _normalize_trail(raw_trail: Any) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_normalize_comments` 

```python
def _normalize_comments(raw_comments: Any) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_safe_link` 

```python
def _safe_link(raw_link: Any, *, column_title: str, title: str) -> str
```

Sanitize a card link with the same scheme rules as other hrefs.

Delegates to the shared href validator (http(s)/mailto or a scheme-less
relative path); anything else — ``javascript:``, ``data:``, ... — raises,
which fails the build loudly under configure's fail-fast dispatch.

**Returns:** `str` - 

### `active_kanban` 

```python
def active_kanban(config: Any) -> dict[str, Any] | None
```

The normalized kanban config, or None when the plugin is inactive.

The plugin loads for every build (it is a default plugin) but only a
``board:`` section in docs.yaml — surfaced as ``config.extra["kanban"]``
by configure() — activates its output.

**Returns:** `dict[str, Any] | None` - 

### `get_kanban` 

```python
def get_kanban(config: Any) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `get_columns` 

```python
def get_columns(config: Any) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `docs_page_mdx` 

```python
def docs_page_mdx(kanban: dict[str, Any]) -> str
```

**Returns:** `str` - 

### `_escape_mdx_text` 

```python
def _escape_mdx_text(value: str) -> str
```

Backslash-escape characters MDX treats as syntax in body text.

**Returns:** `str` -
