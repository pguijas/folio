# Folio Docs

Folio Docs reads Python source and Markdown guides, then builds the static site
people use: API reference, prose pages, navigation, search, theming, and deployable
HTML. It never imports the package it documents.

```bash
uv add folio-docs
uv run folio init
uv run folio serve
```

`folio build` and `folio serve` are the Docs command groups. The package,
version, and release process do not depend on Folio for Agents; when Agents is
installed, it adds `folio board` to the same CLI.

## Code boundary

Documentation generation lives in `folio_docs`:

- `SiteBuilder` owns the generated content workspace and search index.
- The MDX writer, sidebar, template workspace, theme support, and Next runtime
  live beside it.
- Parsing, IR, configuration, plugins, and orchestration are owned by Folio
  Docs and ship in the same wheel.

The old `folio` namespace is not retained. Integrations use `folio_docs` and
the public plugin contracts.

## Agent-readable output

Folio Docs itself writes the Markdown mirror for every generated page, the LLM
indexes, and the published authoring contract. These are documentation output,
not a runtime dependency on Folio for Agents.

Continue with the [quick start](./quickstart).
