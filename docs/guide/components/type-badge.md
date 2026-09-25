# TypeBadge

A small inline badge for displaying a type annotation. Renders as a styled badge with monospace font. When an `href` is provided, the badge becomes a link to the type's documentation page. Every type in a generated parameter table is one.

## API

### TypeBadge

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `string` | — | The type annotation text (e.g. `"str"`, `"list[int]"`, `"Optional[Config]"`). |
| `href` | `string` | — | Optional URL to link the badge to a type's documentation page. |

## Example

<PreviewCode>

```mdx
Returns a <TypeBadge type="Config" href="/docs/configuration" /> object.
The timeout parameter accepts <TypeBadge type="float" /> or
<TypeBadge type="None" />.
```

Returns a <TypeBadge type="Config" href="/docs/configuration" /> object.
The timeout parameter accepts <TypeBadge type="float" /> or
<TypeBadge type="None" />.

</PreviewCode>
