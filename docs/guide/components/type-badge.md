# TypeBadge

A small inline badge for displaying Python type annotations. Renders as a styled badge with monospace font. When an `href` is provided, the badge becomes a link to the type's documentation page. This component is used throughout the auto-generated API reference.

## API

### TypeBadge

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `string` | — | The type annotation text (e.g. `"str"`, `"list[int]"`, `"Optional[Config]"`). |
| `href` | `string` | — | Optional URL to link the badge to a type's documentation page. |

## Example

<PreviewCode>

```mdx
Returns a <TypeBadge type="Config" href="/docs/api-reference/folio/config" /> object.
The timeout parameter accepts <TypeBadge type="float" /> or
<TypeBadge type="None" />.
```

Returns a <TypeBadge type="list[Node]" /> containing all connected peers.

The timeout parameter accepts <TypeBadge type="float" /> or <TypeBadge type="None" />.

The configuration uses <TypeBadge type="Optional[Config]" /> for optional settings.

</PreviewCode>
