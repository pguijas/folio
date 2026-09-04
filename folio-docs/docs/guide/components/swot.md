# Swot

A four-quadrant SWOT analysis rendered as a color-coded grid: strengths, weaknesses, opportunities, and threats, each with its own accent and marker. Use it for honest product or design assessments that a bulleted list would flatten.

## API

### Swot

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `strengths` | `string[]` | — | Internal, helpful. |
| `weaknesses` | `string[]` | — | Internal, harmful. |
| `opportunities` | `string[]` | — | External, helpful. |
| `threats` | `string[]` | — | External, harmful. |
| `title` | `string` | `"SWOT"` | Header label. |

## Example

<PreviewCode title="Product SWOT" defaultMode="preview">

```mdx
<Swot
  title="Espresso cart — Q3"
  strengths={["Best beans in the district", "Regulars know us by name"]}
  weaknesses={["One grinder", "Cash only"]}
  opportunities={["Office park opening next door"]}
  threats={["Chain opening across the street"]}
/>
```

<Swot
  title="Espresso cart — Q3"
  strengths={["Best beans in the district", "Regulars know us by name"]}
  weaknesses={["One grinder", "Cash only"]}
  opportunities={["Office park opening next door"]}
  threats={["Chain opening across the street"]}
/>

</PreviewCode>
