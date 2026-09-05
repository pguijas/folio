# DeprecationNotice

A styled banner indicating that a class, function, or module is deprecated. Displays a red "Deprecated" badge with version information and guidance on what to use instead. This component is typically auto-generated when a docstring contains a `Deprecated:` section.

## API

### DeprecationNotice

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `since` | `string` | — | Version when the deprecation was introduced (e.g. `"1.5.0"`). |
| `alternative` | `string` | — | Name of the replacement to use. Rendered in a `<code>` element with "Use ... instead." phrasing. |
| `message` | `string` | — | Custom deprecation message. |

The rendered card shows:
- A red "Deprecated" badge
- "since X.X.X" in muted text (if `since` is provided)
- The custom message (if provided)
- "Use `alternative` instead." (if `alternative` is provided)

## Example

```mdx
<DeprecationNotice
  since="2.0.0"
  alternative="FederatedNode"
  message="This class will be removed in v3.0."
/>
```

Minimal usage with just a version:

```mdx
<DeprecationNotice since="1.5.0" />
```
