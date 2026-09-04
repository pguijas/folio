# HookMap

Visualize an extension lifecycle with stage names, hook names, and short descriptions.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | `"Extension lifecycle"` | Panel title. |
| `hooks` | `HookMapItem[]` | — | Ordered lifecycle rows. |

`HookMapItem` supports `stage`, `hook`, and `description`.

## Example

<PreviewCode>

```mdx
<HookMap
  hooks={[
    { stage: "Lint", hook: "run_linters", description: "Check formatting and static analysis before tests." },
    { stage: "Deploy", hook: "publish_site", description: "Upload the built output to the hosting provider." },
  ]}
/>
```

<HookMap
  hooks={[
    { stage: "Lint", hook: "run_linters", description: "Check formatting and static analysis before tests." },
    { stage: "Test", hook: "run_tests", description: "Execute the project test suite with coverage enabled." },
    { stage: "Build", hook: "build_artifacts", description: "Build distributable artifacts from the verified sources." },
    { stage: "Deploy", hook: "publish_site", description: "Upload the built output to the hosting provider." },
  ]}
/>

</PreviewCode>
