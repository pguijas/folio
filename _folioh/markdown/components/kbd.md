# Kbd

A key the reader presses, drawn as a small keycap inside the sentence. Use it for shortcuts and key names. A bare `<kbd>` tag written in a page draws the same way.

## API

### Kbd

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | The key label, e.g. `Esc` or `⌘`. |

## Example

**Shortcuts**

```mdx
Press <Kbd>⌘</Kbd> <Kbd>K</Kbd> on macOS or <Kbd>Ctrl</Kbd> <Kbd>K</Kbd>
elsewhere to jump to search. <kbd>Esc</kbd> leaves it.
```

Press ⌘ K on macOS or Ctrl K
elsewhere to jump to search. <kbd>Esc</kbd> leaves it.

## Notes

- One key per `Kbd`. Write a chord as keys side by side.
- The label scales with the text around it, so a key in a heading stays in proportion, and it never drops below 10 px in small text.
- Server-renderable: it renders one `<kbd>` element.
