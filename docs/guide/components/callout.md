# Callout

Highlighted message blocks for notes, warnings, tips, and other important information. Each type has a distinct color and icon to help readers quickly identify the nature of the message.

## API

### Callout

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `"note" \| "warning" \| "info" \| "tip" \| "check" \| "danger"` | `"info"` | The visual style of the callout. |
| `title` | `string` | — | Optional bold title displayed above the content. |
| `children` | `ReactNode` | — | The callout body content. |

### Available Types

| Type | Color | Use for |
|------|-------|---------|
| `note` | Blue | General notes and remarks. |
| `warning` | `--warning` (ochre) | Important warnings the reader should not miss. |
| `info` | Slate | Neutral supplementary information. |
| `tip` | Emerald | Helpful tips and best practices. |
| `check` | Green | Success states or confirmation of correct behavior. |
| `danger` | Red | Critical warnings about destructive or breaking behavior. |

## Example

<PreviewCode>

```mdx
<Callout type="note" title="Python 3.10+">
  This library requires Python 3.10 or later.
</Callout>

<Callout type="warning">
  This function modifies the input array in place.
</Callout>

<Callout type="tip" title="Performance">
  Use batch mode for datasets larger than 10,000 rows.
</Callout>

<Callout type="danger" title="Breaking Change">
  The `legacy_mode` parameter was removed in v2.0.
</Callout>
```

<Callout type="note" title="Python 3.10+">
  This library requires Python 3.10 or later.
</Callout>

<Callout type="warning">
  This function modifies the input array in place.
</Callout>

<Callout type="tip" title="Performance">
  Use batch mode for datasets larger than 10,000 rows.
</Callout>

<Callout type="check" title="All tests passing">
  The test suite completed successfully with 100% coverage.
</Callout>

<Callout type="danger" title="Breaking Change">
  The `legacy_mode` parameter was removed in v2.0.
</Callout>

<Callout type="info">
  This is a neutral informational message with no title.
</Callout>

</PreviewCode>
