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
| `note` | `--folioh-tone-note-*` | General notes and remarks. |
| `warning` | `--folioh-tone-warning-*` | Important warnings the reader should not miss. |
| `info` | `--folioh-tone-info-*` | Neutral supplementary information. |
| `tip` | `--folioh-tone-tip-*` | Helpful tips and best practices. |
| `check` | `--folioh-tone-check-*` | Success states or confirmation of correct behavior. |
| `danger` | `--folioh-tone-danger-*` | Critical warnings about destructive or breaking behavior. |

Each type reads its tone's `-fill` for the background, `-ink` for the title and
text, and `-accent` for the icon and border. The six tones differ on every
preset; [CSS Variables](../theming/personalization#css-variables) lists their
defaults.

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
