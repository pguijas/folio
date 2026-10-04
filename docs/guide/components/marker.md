# Marker

A labelled divider: a short line of small text between two dashed rules. Use it to break a long guide into parts ("Advanced", "Since 0.4", "Optional") without adding a heading to the table of contents.

## API

### Marker

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `tone` | `"ok" \| "danger"` | — | Colors the label: `ok` for a supported or finished part, `danger` for a part that breaks or removes something. Without it the label is muted. |
| `children` | `ReactNode` | — | The label. |

## Example

<PreviewCode title="Dividers" defaultMode="preview">

```mdx
<Marker>Advanced</Marker>

<Marker tone="ok">Stable since 0.3</Marker>

<Marker tone="danger">Removed in 0.4</Marker>
```

<Marker>Advanced</Marker>

<Marker tone="ok">Stable since 0.3</Marker>

<Marker tone="danger">Removed in 0.4</Marker>

</PreviewCode>

## Notes

- The label is plain text for screen readers; the rules are drawn with CSS and are not announced.
- A marker is not a heading, so it never appears in the table of contents or the page outline. Use a heading when the part needs a link.
- Server-renderable.
