# Page Actions

Folio renders a compact `Ask AI` page-actions button above every documentation page. It is meant for source-heavy docs: copy the current page, or send the current page context to ChatGPT without adding extra setup.

## PageActionsButton

A single outline menu button that includes Copy page, View Markdown, a ChatGPT-only assistant action, and MCP JSON actions. The ChatGPT row uses the bundled brand icon and opens ChatGPT with a short `Read from ...` prompt using the current page's Markdown URL, including configured deploy base paths. MCP copies a JSON page-context payload for local tooling.

It takes no author-facing props, and it is not an MDX component: the docs page layout renders it and passes it the page's Markdown mirror, so a page cannot place, move or remove it.

<Callout type="info" title="Layout Component">
  PageActionsButton is rendered by the docs page layout above every documentation page. The button at the top of this page is the live example.
</Callout>
