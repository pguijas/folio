# PreviewCode

Pair a rendered component example with the exact MDX source that produced it. Use `PreviewCode` for component catalog examples so readers can inspect the result first and switch to the code without scrolling through a duplicated section.

## API

### PreviewCode

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | Optional heading shown above the preview/code switcher. |
| `description` | `string` | — | Optional short context for the example. |
| `defaultMode` | `"preview" \| "code"` | `"preview"` | Initial tab. |
| `children` | `ReactNode` | — | Include one fenced code block plus the rendered preview content. |

## Example

**Callout example**

```mdx
<Callout type="tip" title="Use real output">
  Prefer generated pages, command output, and source snippets over abstract placeholders.
</Callout>
```

**Use real output**

  Prefer generated pages, command output, and source snippets over abstract placeholders.
