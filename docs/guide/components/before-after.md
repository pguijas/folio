# BeforeAfter

Show two related code snippets side by side. It works well for migration notes, config changes, and generated output comparisons.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `before` | `string` | — | Left code snippet. |
| `after` | `string` | — | Right code snippet. |
| `beforeLabel` | `string` | `"Before"` | Left label. |
| `afterLabel` | `string` | `"After"` | Right label. |
| `language` | `string` | — | Reserved for future syntax-label use. |

## Example

<PreviewCode>

```mdx
<BeforeAfter
  before={`.. note:: Install Folio first.`}
  after={`<Callout type="note">Install Folio first.</Callout>`}
  beforeLabel="RST"
  afterLabel="MDX"
/>
```

<BeforeAfter
  before={`.. note:: Install Folio first.`}
  after={`<Callout type="note">
  Install Folio first.
</Callout>`}
  beforeLabel="RST"
  afterLabel="MDX"
/>

</PreviewCode>
