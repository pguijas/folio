# Checklist

A readiness list with explicit states. Use it for prerequisites, deployment checks, and release gates.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | Optional checklist title. |
| `items` | `ChecklistItem[]` | — | Rows to render. |

`ChecklistItem` supports `label`, `description`, and `state`. State can be `done`, `warn`, or `todo`.

## Example

```mdx
<Checklist
  title="Before you build"
  items={[
    { label: "Python 3.10+", state: "done" },
    { label: "docs.yaml exists", state: "todo" },
  ]}
/>
```
