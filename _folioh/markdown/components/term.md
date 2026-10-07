# Term

A word or API name with its definition one hover away. The term keeps its place in the sentence, marked by a dotted underline, and the definition appears in a small card above it.

## API

### Term

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `def` | `string` | — | The definition, one or two short sentences. |
| `href` | `string` | — | Optional page that explains the term in full. With it the term is a link. |
| `children` | `ReactNode` | — | The term as it reads in the sentence. |

## Example

**Glossary**

```mdx
Folioh writes every page ahead of time, as a <Term def="Static site generation: the HTML for each page is written at build time, not per request.">static export</Term>,
so any static host can serve it. The reference comes from your
<Term def="Comments in the source that document a module, class or function." href="/docs/docstrings">doc comments</Term>.
```

Folioh writes every page ahead of time, as a static export,
so any static host can serve it. The reference comes from your
doc comments.

## Behavior

| Input | What happens |
|-------|--------------|
| Pointer | The definition opens after 300 ms of hover and closes 150 ms after the pointer leaves the term and the card. |
| Keyboard | Tab to the term opens it the same way, Enter toggles it, and Esc closes it. |
| Touch | A tap toggles the definition, and a tap anywhere else closes it. A term with `href` follows the link instead. |
| Screen reader | The definition is read as the term's description. |

## Notes

- `def` is plain text. Keep it short: the card is at most 260 px wide.
- Use `href` when the definition needs more than the card can hold, so touch readers can reach it too.
