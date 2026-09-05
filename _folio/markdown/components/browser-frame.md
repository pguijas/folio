# BrowserFrame

Browser window chrome around any content: three dots, a mono URL bar, and an optional right-aligned status label. Use it to frame live embeds — board miniatures, rendered components, page excerpts — as the page they ship on, instead of pasting a screenshot.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `url` | `string` | — | Address shown in the mono URL bar. |
| `label` | `string` | — | Optional right-aligned mono label, e.g. `"● LIVE"`. |
| `children` | `ReactNode` | — | Content rendered inside the window body. |

## Example

````mdx
<BrowserFrame url="folio-docs.dev/roadmap" label="● LIVE">
  <Roadmap compact maxPhases={4} />
</BrowserFrame>
````

## Notes

- Server-renderable: no client state, safe in any MDX page or generated view.
- `not-prose`-armored: margins are reset so it sits cleanly inside prose content.
- Pairs with `<Roadmap compact />` for Docs landing-page miniatures. Optional products may register their own framed components.
