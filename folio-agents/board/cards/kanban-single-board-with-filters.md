---
title: Kanban is one board with flexible filters
status: released
created: '2026-08-04'
milestone: "0.1"
tags: [plugins, kanban]
artifacts:
  - doc: kanban-references-teardown.md
    label: "Reference teardown: SVAR and ReUI"
---

The public board renders every card in one instance, but the only filter is
a mount-time URL parameter with no visible control: a visitor who lands on a
milestone deep link cannot see the filter, change it, or clear it. Cards also
carry their full body on the board, which buries the column story. The board
becomes: one instance with all cards, an in-page filter system (milestone,
tag, text) that stays in the URL for deep links, cards that show the title
only, and a full card view that opens on click.

## Acceptance criteria
- [x] one board instance renders all cards; filters never produce a second board
- [x] in-page filter controls for milestone, tag, and text, visible and clearable
- [x] active filters are reflected in the URL so deep links keep working
- [x] board cards render the title only
- [x] clicking a card opens the complete card: description, criteria, trail, artifacts, metadata
- [x] keyboard and reduced-motion behavior preserved

## Trail
- 2026-08-04 @claude: carded from owner direction; work starts in this session.
- 2026-08-04 @claude (bb7e54254): filter rail (milestone, tag, text, URL-synced), title-only cards, card dialog with Escape and focus return; component tests pin the new contract, plugin docs updated. Verified on the rebuilt serve; moved in-progress -> in-review.
- 2026-08-04 @claude: owner rejected the visual execution. Four redesign mockups produced for review under design/mockups/kanban/ (folio-editorial, gh-projects, jira, linear + index), all on the real board data and theme tokens, each with working filters and card overlay. Card stays in-review pending the owner's pick.
- 2026-08-04 @claude: owner review of the four: the card-as-popup is the keeper across all of them; the folio-editorial direction (technical plate, rule lines, mono apparatus) is rejected outright for the board UI. Synthesis in design/mockups/kanban/proposal.html — jira lanes and raised cards with a centered popup and metadata sidebar, gh token filters, linear keyboard affordances, folio theme tokens.
- 2026-08-05 @claude (5fb689361): SVAR React Kanban and ReUI Kanban read at the source; verdict is to take neither as a dependency and write the techniques ourselves. Teardown attached as a doc artifact.
- 2026-08-05 @claude (a86d10ba1): shipped. Cards carry a stable uid and every mutation takes it, so the filter gate on drag is gone — a filtered board is operable. Overlay became uid -> {from, to} with a per-entry staleness check; drop placeholder, undo, facet record, aria-live, focus trap, coarse-pointer move buttons, data-slot seams, and the approved skin. 1027 tests green, tsc clean.
- 2026-08-05 @claude (f5fc1b818): adversarial review of the rewrite, 28 findings, 18 refuted, 9 fixed — the facet token parser committed mid-word, the drag payload typed card ids into the filter field, the filter input had no visible focus, repeated announcements were silent, "/" was bound page-wide, the focus trap leaked forward, and touch move buttons covered card titles in the miniatures.
- 2026-08-10 @claude: the board takes the landing's voice. Ten app-like studies were rejected as gaudy; the owner asked for editorial and pointed at the landing, and measuring it showed the board was already speaking the same language with the colour drained out — the column names were the landing's eyebrow at 12px/0.08em in grey instead of 11px/0.14em in the accent. Shipped: a masthead (mono blue eyebrow over a 36px sentence-case headline) replacing the 14px label, no lane fills or lane borders, cards opening with the roadmap step their milestone names, and the type scale cut to the landing's own. Home and Roadmap left the toolbar. Measured at 1440: 10 cards above the fold against 9 before, because dropping the card description the popup already carries paid for the masthead. Studies under design/mockups/board-minimal/.
- 2026-08-07 @claude: technical audit of the shipped board, then every finding fixed. Measured, not guessed: the sticky toolbar ran 83px at desktop but 183px at 360px, so it now holds two rows at every width (facets collapse below md, actions below xl). The live region spoke once per keystroke (six for six characters) and now speaks once the typing settles. The dialog's scrolling body was not a tab stop, so a long trail was unreachable without a mouse. The board behind the open card is inert. `role="list"` no longer holds the empty-state paragraph, which some tools dropped outright. Contrast: the card count sat at 2.3:1 and the milestone label at 4.2:1 in dark. The coarse-pointer pin is gone — it hid every milestone on every phone to serve a control the dialog already carries — and the milestone now steps aside on the same condition that paints the move buttons, which is the keyboard overlap the audit found. Seven font sizes became two on the board surface; the column names moved to the label register so the board's h1 is finally its only heading, at zero added height. Six unicode characters used as icons became drawn marks on ColumnGlyph's 16-unit grid. The hard-coded amber became a real `--warning` token, which no single value could serve in both modes.
- 2026-08-27 @claude: audit: one instance filtering in place with URL-synced controls (kanban-board.tsx:3975), title-only miniatures with the full card in the dialog (kanban-board.tsx:2718-2751), motion-reduce honored (:2211); every criterion holds in the served component
