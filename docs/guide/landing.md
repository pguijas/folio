# Landing Page

*Configure the optional homepage that appears before the documentation app.*

<Callout type="warning" title="Beta feature">
  The landing page is disabled in this release while deep visual personalization stabilizes. These notes are kept for future work and are not included in generated public docs.
</Callout>

Folio starts as a docs-first site. When you want a public entry point, enable the
landing page in `docs.yaml` and keep the docs under `/docs/`.

```yaml
landing:
  enabled: true
  hero:
    headline: "Your project"
    description: "Generated API reference and guides from your Python source."
  cta:
    primary:
      text: "Read the docs"
      link: "/docs"
    secondary:
      text: "View source"
      link: "https://github.com/you/project"
```

Use the landing page for project positioning, install commands, and links to the
most important documentation routes. Keep detailed tutorials, configuration
reference, and API content in the docs section.

## Recommended Structure

- **Hero**: project name, one-sentence value proposition, and primary docs link.
- **Install**: the shortest command sequence that gets users to a local preview.
- **Proof**: links to generated API pages, guides, examples, or release notes.
- **CTA**: a final link to `/docs` or the quickstart guide.

The generated landing page uses the same theme tokens, navigation, search
metadata, and static export path as the rest of the site.

## Comparison Section

Setting `landing.comparison: true` adds a feature matrix that compares Folio
with other documentation tools (Sphinx, MkDocs, pdoc, and others). It is off by
default because the table is Folio-branded marketing content — enable it only
if that fits your project's landing page.

```yaml
landing:
  comparison: true
```
