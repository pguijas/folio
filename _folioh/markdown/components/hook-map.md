# HookMap

Visualize an extension lifecycle with stage names, hook names, and short descriptions.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | `"Extension lifecycle"` | Panel title. |
| `hooks` | `HookMapItem[]` | — | Ordered lifecycle rows. |

`HookMapItem` supports `stage`, `hook`, and `description`.

## Example

```mdx
<HookMap
  hooks={[
    { stage: "Lint", hook: "run_linters", description: "Check formatting and static analysis before tests." },
    { stage: "Deploy", hook: "publish_site", description: "Upload the built output to the hosting provider." },
  ]}
/>
```
