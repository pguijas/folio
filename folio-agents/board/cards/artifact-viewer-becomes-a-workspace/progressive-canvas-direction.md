# Progressive artifact canvas

## Objective

Replace the current dialog and artifact overlay with one continuous kanban
workspace. Each selection adds its next context without obscuring or replacing
the context that produced it.

## Confirmed direction

The logical and document order is:

1. Filters refine the board.
2. The canvas presents the board.
3. Selecting a card opens the card after the canvas.
4. Selecting an artifact opens the artifact after the card.

On a very wide viewport, "after" means farther right. When that horizontal
chain no longer fits, the artifact continues below the canvas and card. At a
narrower width, card and artifact both continue downward. The responsive
layout changes placement, never reading or keyboard order.

Surfaces share hairline boundaries rather than appearing as framed windows.
Filters, card, and artifact remain closable and resizable. Closing the artifact
returns to the card. Closing the card also closes its artifact because a child
surface cannot outlive its context. Filters remain independent.

The artifact offers a full-screen mode. Exiting it restores the complete
progressive chain and its sizes.

## Product mapping

Keep the current artifact rendering contract:

- A compiled document is fetched from the page Folio already emitted and its
  article body is reused.
- A raw HTML or file artifact stays inside a sandboxed iframe.
- An unpublished target remains plain text rather than becoming a dead reader.

Change the page composition:

- The filter panel becomes the first resizable rail.
- The board remains the central canvas and keeps its scroll and drag state.
- The card dialog becomes the next in-flow surface.
- The artifact drawer becomes the final in-flow surface.
- Card, artifact, open surfaces, and sizes are restored from the URL or local
  layout state without changing their semantic order.

## Open choice

The structure is confirmed. Stage 2 needs one owner confirmation that the
responsive breakpoint behavior in the rendered prototype is close enough to
integrate. Exact breakpoint values and default sizes should be tuned against
the real Folio docs during implementation, not treated as product constants
from the standalone candidate.

## Validation state

The standalone prototype covers the wide rightward chain, the laptop layout
with the artifact below, a narrower downward sequence, pointer and keyboard
resizing, progressive close behavior, document and prototype artifacts, URL
updates, theme switching, and full-screen entry/exit. Its inline script passes
`node --check`; the board passes `folio kanban check`; the Folio build and dev
server complete; and the prototype, compiled direction, and filtered board
URLs return HTTP 200. Visual automation remains unavailable in this session,
so owner review is the remaining Stage 1 validation.
