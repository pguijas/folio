# BeforeAfter

Show two related code snippets side by side. It works well for migration notes, config changes, and generated output comparisons.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `before` | `string` | — | Left code snippet. |
| `after` | `string` | — | Right code snippet. |
| `beforeLabel` | `string` | `"Before"` | Left label. |
| `afterLabel` | `string` | `"After"` | Right label. |
| `language` | `string` | — | Accepted and ignored. |

## Example

<PreviewCode>

```mdx
<BeforeAfter
  before={`.. note:: Install Folioh first.`}
  after={`<Callout type="note">Install Folioh first.</Callout>`}
  beforeLabel="RST"
  afterLabel="MDX"
/>
```

<BeforeAfter
  before={`.. note:: Install Folioh first.`}
  after={`<Callout type="note">
  Install Folioh first.
</Callout>`}
  beforeLabel="RST"
  afterLabel="MDX"
/>

</PreviewCode>
