# StatStrip

A row of big numbers with labels — the fastest way to make scale legible. Values are strings, so units and symbols render exactly as written.

## API

### StatStrip

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `stats` | `{ value, label, detail? }[]` | — | One entry per number. |

## Example

<PreviewCode title="Project stats" defaultMode="preview">

```mdx
<StatStrip
  stats={[
    { value: "94", label: "pages", detail: "generated per build" },
    { value: "40", label: "components" },
    { value: "867", label: "tests", detail: "green before every merge" },
  ]}
/>
```

<StatStrip
  stats={[
    { value: "94", label: "pages", detail: "generated per build" },
    { value: "40", label: "components" },
    { value: "867", label: "tests", detail: "green before every merge" },
  ]}
/>

</PreviewCode>
