# DocPreview

Use `DocPreview` when a guide needs to show a generated documentation route or a small generated example instead of describing the result with another code block. It renders a responsive iframe with a short caption, a source view with a collapsible file drawer for the focused source file, a line-numbered code preview, and direct links to the page and source file.

```mdx
<DocPreview
  title="Guide page preview"
  src="/docs/quickstart/"
  description="Show a built page directly in the guide so readers can inspect the output before building their own project."
  height={460}
/>
```

For tutorial examples, place a complete Folio project under `docs/examples/<name>/` with its own `docs.yaml`, `docs/`, and optional `src/` files. The docs build runs Folio for that project, serves the generated static output at `/_folio/examples/<name>/`, and shows the exact source files that produced it. `folio build` always builds the examples; `folio serve` builds them only with `--previews`, because each one is a full nested site, and a `DocPreview` whose example is not built says so in its place.

```mdx
<DocPreview
  title="Generated docs site"
  example="generated-site"
  description="A tiny docs site generated from a real example project."
  height={360}
/>
```
