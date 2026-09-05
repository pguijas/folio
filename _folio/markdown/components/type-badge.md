# TypeBadge

A small inline badge for displaying Python type annotations. Renders as a styled badge with monospace font. When an `href` is provided, the badge becomes a link to the type's documentation page. This component is used throughout the auto-generated API reference.

## API

### TypeBadge

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `string` | — | The type annotation text (e.g. `"str"`, `"list[int]"`, `"Optional[Config]"`). |
| `href` | `string` | — | Optional URL to link the badge to a type's documentation page. |

## Example

```mdx
Returns a <TypeBadge type="Config" href="/docs/api-reference/folio_docs/config" /> object.
The timeout parameter accepts <TypeBadge type="float" /> or
<TypeBadge type="None" />.
```

Returns a  containing all connected peers.

The timeout parameter accepts  or .

The configuration uses  for optional settings.
