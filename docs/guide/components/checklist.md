# Checklist

A readiness list with explicit states. Use it for prerequisites, deployment checks, and release gates.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | Optional checklist title. |
| `items` | `ChecklistItem[]` | — | Rows to render. |

`ChecklistItem` supports `label`, `description`, and `state`. State can be `done`, `warn`, or `todo`.

## Example

<PreviewCode>

```mdx
<Checklist
  title="Before you build"
  items={[
    { label: "Node.js 20.19+", state: "done" },
    { label: "docs.yaml exists", state: "todo" },
  ]}
/>
```

<Checklist
  title="Before you build"
  items={[
    { label: "Node.js 20.19+ and pnpm 10", description: "Required by folio build and folio serve.", state: "done" },
    { label: "docs.yaml exists", description: "Run folio init if it is missing.", state: "todo" },
    { label: "No stale output committed", description: "Keep .build/ and _site/ out of source control unless your deployment needs them.", state: "warn" },
  ]}
/>

</PreviewCode>
