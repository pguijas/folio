# ExampleTabs

Tabbed panels for showing multiple code examples for the same concept, such as basic vs. advanced usage or different input formats. Each tab displays its code as a plain, unhighlighted block. For highlighted tabs, use [CodeGroup](/docs/components/code-group) with fenced code blocks.

## API

### ExampleTabs

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `examples` | `Example[]` | — | Array of example objects. |

### Example object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | `string` | — | Tab label text. |
| `code` | `string` | — | The code string to display. |
| `language` | `string` | `"python"` | Sets the `language-*` class on the code element; the code is not highlighted. |

## Example

```mdx
<ExampleTabs examples={[
  {
    label: "Basic",
    code: "node = Node()\nnode.start()",
    language: "python"
  },
  {
    label: "With Config",
    code: "node = Node(config=Config(port=9090))\nnode.start(rounds=10)",
    language: "python"
  },
  {
    label: "Async",
    code: "async def main():\n    node = Node()\n    await node.start_async()",
    language: "python"
  }
]} />
```
