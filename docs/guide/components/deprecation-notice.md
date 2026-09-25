# DeprecationNotice

A styled banner indicating that a class, function, or module is deprecated. Displays a red "Deprecated" badge with version information and guidance on what to use instead. Generated API pages do not write this component: a docstring's `Deprecated:` section or a JSDoc `@deprecated` tag renders as a **Deprecated:** paragraph. Use it by hand in the pages you write.

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

<PreviewCode>

```mdx
<DeprecationNotice
  since="2.0.0"
  alternative="FederatedNode"
  message="This class will be removed in v3.0."
/>
```

<DeprecationNotice
  since="2.0.0"
  alternative="FederatedNode"
  message="This class will be removed in v3.0."
/>

</PreviewCode>

Minimal usage with just a version:

<PreviewCode>

```mdx
<DeprecationNotice since="1.5.0" />
```

<DeprecationNotice since="1.5.0" />

</PreviewCode>
