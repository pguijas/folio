# CompareMatrix

A comparison matrix with check / dash / partial cells and a highlighted "us" column. Use it where the honest answer is a grid, not three paragraphs of prose.

## API

### CompareMatrix

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `tools` | `string[]` | — | Column headers. |
| `rows` | `{ feature, values, note? }[]` | — | One row per capability; values are `true` (check), `false` (dash), `"~"` (partial), or free text. |
| `caption` | `string` | — | Label above the feature column. |
| `highlight` | `number` | `0` | Index of the emphasized column. |

## Example

**Tool comparison**

```mdx
<CompareMatrix
  caption="Capability"
  tools={["Espresso cart", "Chain café", "Vending machine"]}
  rows={[
    { feature: "Knows your order", values: [true, "~", false] },
    { feature: "Open at 6am", values: [false, true, true] },
    { feature: "Latte art", values: [true, "~", false], note: "the swan is negotiable" },
  ]}
/>
```
