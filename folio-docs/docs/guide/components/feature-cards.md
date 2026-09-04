# FeatureCard and CardGrid

Cards for feature overviews, landing pages, and link grids. `FeatureCard` renders a single card with a named icon, title, description, and optional link. `CardGrid` arranges multiple cards in a responsive grid layout.

## API

### FeatureCard

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | The card heading. |
| `description` | `string` | — | Short description text displayed below the title. |
| `icon` | `string` | — | Optional named icon displayed above the title. Common tokens include `install`, `run`, `quickstart`, `workflow`, `network`, `topology`, `analytics`, `settings`, `monitor`, `api`, `code`, `server`, `warning`, and `community`. Unknown values fall back to text rendering for backwards compatibility. |
| `href` | `string` | — | Optional URL. When set, the card becomes a clickable link with a hover effect. |

### CardGrid

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `columns` | `2 \| 3 \| 4` | `3` | Number of columns on large screens. The grid is always 1 column on mobile and 2 on tablet. |
| `children` | `ReactNode` | — | One or more `<FeatureCard>` elements (or any content). |

## Example

Three-column grid with named icons:

<PreviewCode>

```mdx
<CardGrid columns={3}>
  <FeatureCard
    title="Auto API Reference"
    description="Extracts documentation from your Python source code automatically."
    icon="api"
    href="/docs/docstrings"
  />
  <FeatureCard
    title="Modern UI"
    description="Dark mode, search, and responsive layout out of the box."
    icon="settings"
  />
  <FeatureCard
    title="LLM Output"
    description="Generate llms.txt and llms-full.txt for AI assistants."
    icon="ai"
    href="/docs/configuration#llm-output"
  />
</CardGrid>
```

<CardGrid columns={3}>
  <FeatureCard
    title="Auto API Reference"
    description="Extracts documentation from your Python source code automatically."
    icon="api"
    href="/docs/docstrings"
  />
  <FeatureCard
    title="Modern UI"
    description="Dark mode, search, and responsive layout out of the box."
    icon="settings"
  />
  <FeatureCard
    title="LLM Output"
    description="Generate llms.txt and llms-full.txt for AI assistants."
    icon="ai"
    href="/docs/configuration#llm-output"
  />
</CardGrid>

</PreviewCode>

Two-column grid without icons:

<PreviewCode>

```mdx
<CardGrid columns={2}>
  <FeatureCard
    title="Getting Started"
    description="Install Folio and build your first documentation site."
    href="/docs/quickstart"
  />
  <FeatureCard
    title="Configuration"
    description="Customize your site with docs.yaml options."
    href="/docs/configuration"
  />
</CardGrid>
```

<CardGrid columns={2}>
  <FeatureCard
    title="Getting Started"
    description="Install Folio and build your first documentation site."
    href="/docs/quickstart"
  />
  <FeatureCard
    title="Configuration"
    description="Customize your site with docs.yaml options."
    href="/docs/configuration"
  />
</CardGrid>

</PreviewCode>
