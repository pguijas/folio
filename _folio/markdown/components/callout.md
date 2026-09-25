# Callout

Highlighted message blocks for notes, warnings, tips, and other important information. Each type has its own icon; the colors come from the theme tokens below.

## API

### Callout

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `"note" \| "warning" \| "info" \| "tip" \| "check" \| "danger"` | `"info"` | The visual style of the callout. |
| `title` | `string` | — | Optional bold title displayed above the content. |
| `children` | `ReactNode` | — | The callout body content. |

### Available Types

| Type | Color token | Use for |
|------|-------|---------|
| `note` | `--primary` | General notes and remarks. |
| `warning` | `--warning` | Important warnings the reader should not miss. |
| `info` | `--muted` | Neutral supplementary information. |
| `tip` | `--primary` | Helpful tips and best practices. |
| `check` | `--primary` | Success states or confirmation of correct behavior. |
| `danger` | `--destructive` | Critical warnings about destructive or breaking behavior. |

`note`, `tip` and `check` share the `--primary` color and differ by icon.

## Example

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

<Callout type="check" title="All tests passing">
  The test suite completed successfully with 100% coverage.
</Callout>

<Callout type="danger" title="Breaking Change">
  The `legacy_mode` parameter was removed in v2.0.
</Callout>

<Callout type="info">
  This is a neutral informational message with no title.
</Callout>
```

**Python 3.10+**

  This library requires Python 3.10 or later.

  This function modifies the input array in place.

**Performance**

  Use batch mode for datasets larger than 10,000 rows.

**All tests passing**

  The test suite completed successfully with 100% coverage.

**Breaking Change**

  The `legacy_mode` parameter was removed in v2.0.

  This is a neutral informational message with no title.
