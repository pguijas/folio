# KanbanBoard

Git-persisted kanban board with drag-and-drop editing, filtering, and card detail dialogs. Requires the kanban plugin active in `docs.yaml`.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `compact` | `boolean` | `false` | Hides the filter bar, card detail dialog, staging card, and URL parameter syncing. For embedding boards in documentation pages. |
| `maxCardsPerColumn` | `number` | — | Caps the number of cards shown per column in embeds. |

## Example

<PreviewCode>

````mdx
<KanbanBoard compact maxCardsPerColumn={2} />
````

<KanbanBoard compact maxCardsPerColumn={2} />

</PreviewCode>

## Theming

Every structural node carries a `data-slot` attribute for styling. Additional attributes mark dynamic state.

| Attribute | Target |
|-----------|--------|
| `data-slot="kanban"` | Root container. |
| `data-slot="kanban-filters"` | Filter bar. |
| `data-slot="kanban-filter-panel"` | Filter composer rail or drawer. |
| `data-slot="kanban-board"` | Board canvas holding all columns. |
| `data-slot="kanban-column"` | Single column container. |
| `data-slot="kanban-column-header"` | Column title and count. |
| `data-slot="kanban-card-list"` | List of cards within a column. |
| `data-slot="kanban-card"` | Individual card tile. |
| `data-slot="kanban-card-dialog"` | Card detail dialog. |
| `data-slot="kanban-artifact-drawer"` | Reading drawer for a published artifact, inside the card dialog. |
| `data-slot="kanban-staging"` | Move staging card shown when moves are pending. |
| `data-column` | Column identifier on column nodes. |
| `data-card` | Card identifier on card nodes. |
| `data-dragging` | Present on cards during drag operations. |

The staging banner and its slot describe the current browser-staged flow; the write-path direction is tracked on the project board.

The board page renders on pure white in light mode. Dark mode and every preset keep their own background.
