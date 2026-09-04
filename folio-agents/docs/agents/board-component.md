# KanbanBoard

Optional Folio Docs canvas for a Folio for Agents board, with filtering,
staged drag-and-drop, and a progressive public workspace.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `compact` | `boolean` | `false` | Hides the filter bar, card detail dialog, staging card, and URL parameter syncing. For embedding boards in documentation pages. |
| `maxCardsPerColumn` | `number` | — | Caps the number of cards shown per column in embeds. |

## Example

<PreviewCode
  defaultMode="code"
  description="Activate the kanban plugin with your own source to render this preview."
>

```mdx
<KanbanBoard compact maxCardsPerColumn={2} />
```

</PreviewCode>

The standalone CLI reads the board configured by `board.source` in
`agents.yaml`. The optional Folio Docs adapter reads `kanban.source` in
`docs.yaml`. Folio's own operational board lives on its independent `board`
branch, so this release documentation shows the invocation without coupling
the code release to that board's update cycle.

## Progressive workspace

The public board keeps one continuous surface order: filters, canvas, selected
card, selected artifact. Selecting something adds its context after its parent;
it never covers the canvas. A wide viewport continues the chain to the right.
When the chain no longer fits, the card or artifact continues below without
changing document or keyboard order.

Each hairline between surfaces is a resizer. Drag it, use its arrow keys, or
double-click it to restore the default. Closing the artifact returns to the
card; closing the card also closes its artifact. Filters close independently.
The URL carries `?card=` and `?artifact=`, and a readable artifact can enter and
leave the browser's native full-screen mode.

Open context is reading space, not a preview. The card starts at `760px` in its
active dimension and the artifact at `1040px` wide or `900px` high. Resizing
cannot reduce the card below `440px` wide or `420px` high, nor the artifact
below `560px` wide or `480px` high. The card continues below through `1535px`,
the artifact through `2559px`, and only larger viewports use all four surfaces
in one row.

Boards embedded inside documentation keep the modal card and artifact drawer.

## Theming

Every structural node carries a `data-slot` attribute for styling. Additional attributes mark dynamic state.

| Attribute | Target |
|-----------|--------|
| `data-slot="kanban"` | Root container. |
| `data-slot="kanban-filters"` | Filter bar. |
| `data-slot="kanban-filter-panel"` | Filter composer rail or drawer. |
| `data-slot="kanban-workspace"` | Responsive layout owner for the public canvas. |
| `data-slot="kanban-workspace-divider"` | Keyboard- and pointer-resizable separator between workspace surfaces. |
| `data-slot="kanban-canvas-shell"` | Toolbar and board canvas surface. |
| `data-slot="kanban-board"` | Board canvas holding all columns. |
| `data-slot="kanban-column"` | Single column container. |
| `data-slot="kanban-column-header"` | Column title and count. |
| `data-slot="kanban-card-list"` | List of cards within a column. |
| `data-slot="kanban-card"` | Individual card tile. |
| `data-slot="kanban-card-dialog"` | Card detail dialog. |
| `data-slot="kanban-card-panel"` | Selected card in the public workspace. |
| `data-slot="kanban-artifact-drawer"` | Reading drawer for a published artifact, inside the card dialog. |
| `data-slot="kanban-artifact-reader"` | Selected artifact in the public workspace. |
| `data-slot="kanban-staging"` | Move staging card shown when moves are pending. |
| `data-workspace-surface` | Surface identity (`canvas`, `card`, or `artifact`) in the public workspace. |
| `data-column` | Column identifier on column nodes. |
| `data-card` | Card identifier on card nodes. |
| `data-dragging` | Present on cards during drag operations. |

The staging banner and its slot describe the current browser-staged flow; the write-path direction is tracked on the project board.

The board page renders on pure white in light mode. Dark mode and every preset keep their own background.
