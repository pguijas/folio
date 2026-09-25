# BrowserFrame

Browser window chrome around any content: three dots, a mono URL bar, and an optional right-aligned status label. Use it to frame live embeds — roadmap miniatures, rendered components, page excerpts — as the page they ship on, instead of pasting a screenshot.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `url` | `string` | — | Address shown in the mono URL bar. |
| `label` | `string` | — | Optional right-aligned mono label, e.g. `"● LIVE"`. |
| `footer` | `ReactNode` | — | Optional status-bar strip inside the window, under the content: the place for links or actions that belong to the framed content. |
| `children` | `ReactNode` | — | Content rendered inside the window body. |

## Example

````mdx
<BrowserFrame url="pguijas.github.io/folio/docs/plugins/roadmap" label="● LIVE">
  <Roadmap compact maxPhases={4} />
</BrowserFrame>
````

## Notes

- Server-renderable: no client state, safe in any MDX page or generated view.
- `not-prose`-armored: margins are reset so it sits cleanly inside prose content.
- Pairs with `<Roadmap compact />` for landing-page roadmap miniatures.
