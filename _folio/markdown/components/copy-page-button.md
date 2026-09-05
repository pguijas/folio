# Page Actions

Folio renders a compact `Ask AI` page-actions button above every documentation page. It is meant for source-heavy docs: copy the current page, or send the current page context to ChatGPT without adding extra setup.

## PageActionsButton

A single outline menu button that includes Copy page, View Markdown, a ChatGPT-only assistant action, and MCP JSON actions. The ChatGPT row uses the bundled brand icon and opens ChatGPT with a short `Read from ...` prompt using the current page's Markdown URL, including configured deploy base paths. MCP copies a JSON page-context payload for local tooling.

### PageActionsButton

This component takes no props.

```mdx
<PageActionsButton />
```

## CopyPageButton

A standalone copy-only button. It remains available for custom MDX pages, but the default docs layout uses `PageActionsButton`.

### CopyPageButton

This component takes no props.

```mdx
<CopyPageButton />
```

## Layout

**Layout Component**

  PageActionsButton is rendered by the theme layout above every documentation page.
