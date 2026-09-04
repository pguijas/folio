# Reading an artifact from the canvas — four prototypes compared

Built 2026-08-24 to answer one question: a card can attach what it produced,
but reading it means leaving the board, either for a compiled page under
`/docs` wearing documentation chrome or for a raw file in a new tab. Four
layouts were built in full against the real 44-card board and verified
adversarially in a headless browser. The sibling note
`where-card-pages-publish.md` answers the other half of the owner's
verdict; this document takes its conclusion as given and says so where a
prototype argued against it.

The demo path every variant had to survive is the card
`the-board-reads-as-a-tree`: one long markdown document and five HTML
prototypes built for a full 1440px window. That card decided more of this
comparison than any principle did.

## Reading overlay

**What it argues.** Reading is a mode you enter deliberately. The artifact
takes the viewport over a dimmed rim of board; two native dialogs stack in
the top layer, the mail below and the reader above, and Esc unwinds exactly
one level with focus returned to the element that opened what just closed.

**Strongest.** It is the only in-place variant that gives the demo card's
artifacts the room they were made for: the document reads at a 66ch measure
and the prototypes embed near the width they were designed at. The
implementation leans on the platform — `showModal()` supplies the backdrop,
the inert canvas and per-level Esc, and the script's own work is
bookkeeping. It is also the only in-place variant that applies the URL on
hash change, not only at load; the board reader page's URL is alive too,
but reading there has left the canvas.

**Where it fails.** It is modal. You cannot read and scan the columns at
once, and comparing two artifacts means closing one to open the other.
Focus inside an embedded prototype takes the keys with it, an honest limit
of opaque-origin `file://` iframes. The URL keys artifacts by target
basename, which collides the day a card attaches two files with the same
name. Wheel input over the dimmed rim still scrolls the board behind, and
card descriptions render as plain text, markdown punctuation and all.

**Verification.** Passed. The pass found nothing the notes panel had not
already admitted, which is worth stating as credit; the one issue logged is
the shared data gap covered below.

## Reading rail

**What it argues.** Reading and the board share the screen. The artifact
opens as a right rail, `clamp(500px, 44vw, 680px)`, beside columns that stay
fully live; the card dialog collapses into the rail's crumb so only one
reading surface exists at a time.

**Strongest.** It is the only variant where "readable from the canvas" is
literally true while reading: the columns stay interactive, the card being
read is marked on the board, the filter keeps working, and when the filter
hides the very card whose artifact is open, closing the rail still lands
focus somewhere sensible. The housekeeping is careful: the closed rail is
inert and its iframe is parked on `about:blank`.

**Where it fails.** Half a screen is a poor page, and the builder's own
numbers say so: the comparison document reads in roughly a 45%-viewport
measure, and prototypes built for 1440px embed at about 600px, so the rail
under-sells exactly the artifacts the demo card compares. The compressed
board keeps two or three columns in view and grows a horizontal scrollbar;
two scroll regions share one wheel. Board, dialog and rail together have
more state corners than one modal, and the corners are reachable: the
dialog can sit beside the rail showing a different card, with Tab trapped
in the dialog while the rail stays click-reachable. The `[` and `]`
shortcuts die inside the embedded iframe, and Open full for the document
points at the compiled `/docs` page, served site only.

**Verification.** Passed on fresh loads. It found what the notes do not
say: there is no `hashchange` listener, so the URL is honoured only at
load, and a deep link restores rail and crumb but not the dialog, by design
but undeclared.

## Dialog reader

**What it argues.** Everything about a card, including what it produced,
reads in one surface. The mail dialog widens into letter and reading pane;
the band stays on the left with the open attachment marked, so there is no
second place to learn and no second layer to unwind.

**Strongest.** The least new geometry of the four: one dialog, no extra
layer, no change to the page behind it. Band position stays visible while
reading. It is the only variant that renders card prose with a small
markdown pass, and it handles the closed-door rule most exactly: Open full
is absent for the markdown artifact rather than pointing anywhere dead.

**Where it fails.** The reading pane never gets more than about two thirds
of a 1440px screen because the compressed letter keeps 340px, so the five
embedded prototypes render at a width nobody uses them at; Open full is the
admission. The modal blocks the canvas it claims to preserve, and the
letter reshapes the moment a reader opens, so the surface stays one but
does not stay still. Focus inside the iframe eats Esc and the arrows;
ArrowLeft and ArrowRight always walk the band while reading, stealing
horizontal scrolling from wide code blocks; and Chrome's close-watcher
grouping can let a rapid second Esc close the whole dialog.

**Verification.** Passed on fresh loads, with the same undeclared load-only
URL as the rail. One thing no notes panel carries: the URL names the
artifact by band index (`&a=1`), so a pasted link silently changes meaning
if the card ever reorders its artifacts; the overlay's basename and the
page's slug both survive a reorder.

## Board reader page

**What it argues.** An artifact's URL is a board page:
`/kanban/<card>/<artifact>`, board chrome, a reading column, the card's
other artifacts in a rail. Opening is a real navigation; Back unwinds
perfectly. The route model in the script's header comment is the most
considered of the four: pushState per level, replaceState per band step, a
depth counter in `history.state` so Esc never backs out of the app, and a
slug grammar that tries the target's stem, then its filename, then its
index on collision.

**What happened.** The builder's session died mid-file: the script stopped
at line 329, the IIFE never closed, and nothing ran. The back half was
written afterwards: the dialog, the reader page and the navigation, built
against the completed HTML and CSS and the route model in the script's own
header, then verified like the others.

**Verification.** Passed, and the route model holds up. One press of Esc is
one history entry when the history is in-app, and a written parent state
when it is not, so a deep link never backs out of the app. Band steps and
rail switches replace in place, so Back never replays a reading session; a
fresh load of the route restores the page; the closed door is a div marked
"path only". It adopts the dialog reader's rule and hides Open full for the
markdown artifact rather than pointing at a page `file://` cannot serve.

**Where it fails.** Reading leaves the canvas entirely, which its own notes
admit, and the route it wants is the one option (b) of
`where-card-pages-publish.md` already costed out and rejected: a second
catch-all outside `/docs`, with search, sitemap, mirrors and link
validation rebuilt around it. Complete and verified, it still argues
against the sibling note's conclusion.

## The cuts

**What the reader keeps seeing.** Only the rail keeps a live board. The
overlay keeps a dimmed inert rim, the dialog reader the same canvas behind a
backdrop, the page nothing. What the residual board is worth is the real
question: with the rail it buys real work and costs half the reading
surface; with the overlay it buys only the sense of not having left, and
costs nothing.

**The Esc stack.** The overlay has two levels enforced by the platform: Esc
arrives as `cancel` on the topmost dialog only, so one press is always one
level. The dialog reader has two levels enforced by hand inside one dialog,
and Chrome's Esc grouping can eat one. The rail has up to three presses
from its deepest corner. The page's Esc is Back when the history is in-app
and a written parent state when it is not, one press per level, verified.

**What the URL means.** All four write the reading position; they disagree
on what the words are. The overlay writes card id plus artifact basename,
applied on load and on hash change. The rail writes the artifact target plus
the filter, load only. The dialog reader writes card id plus band index,
load only, and an index is the weakest name of the three. The page writes a
route with real history, the only variant where Back means something and the
only grammar that survives both a duplicate filename and a reorder.

**What is left for the compiled page.** Every notes panel overreached here.
The overlay says a deep link no longer needs the compiled page; the rail
demotes it to the Open full target, "indexed nowhere"; the dialog reader
says it can go entirely; the page variant retires it into a redirect. All
four contradict `where-card-pages-publish.md`, and this document sides with
the note. The compiled page keeps the jobs a canvas reader cannot do: the
durable address, the search hit, the llms.txt line, the markdown mirror. It
loses only the sidebar seat and the human reading. The rail's own Open
full is the demonstration: a long document eventually wants a full window
with a stable address, and that address already exists.

**Cost in the real component.** The board is one client component,
`template/components/kanban-board.tsx`, and the card dialog already exists
in it. The overlay is a second dialog element inside that component; the
dialog reader is a width state and a second pane inside the existing dialog;
the rail is layout, the component's root becoming a two-pane stage that
touches the board's own scrolling and width logic. None of the three needs a
route. The page needs a real route under `/kanban`, which is the option (b)
bill; it is a build-system decision disguised as a layout.

**A shared gap, not a variant defect.** The brief requires that tables read
well, and the document every variant demos contains none: verified
identically in the source markdown, the compiled page and `reader-data.js`.
Every variant's table CSS was proven only by injecting a probe table.
Whichever variant ships should be re-checked against a document that
actually has tables.

## Recommendation

**Reading overlay**, as the primary, paired with the compiled page exactly
as the sibling note leaves it: the overlay is where a human reads from the
canvas, and the delisted `/docs/kanban/<id>/<stem>/` page stays the durable
full-window address that deep links, search and agents land on. That pairing
is a combination, but not of two prototypes; the second half already exists.

The reason is the demo card. This board attaches long documents and
full-width prototypes, and both want the whole viewport. The rail preserved
the canvas and under-sold the artifacts; the dialog reader preserved the
surface and cramped the reading; the page preserved the URL and lost the
canvas. The overlay preserved the thing being read, and reading was the
point. It is also the cheapest implementation in the real component and the
only in-place variant whose URL is alive rather than load-only; the page's
URL is alive too, but it is not on the canvas. Reading two artifacts
side by side is the one need it cannot meet, and the answer to that is the
compiled page in a second window, not a rail.

Taken from the losing variants: the board reader page's slug grammar
replaces the overlay's bare basename in the URL; the dialog reader's rule of
hiding Open full when there is nothing full to open, and its small markdown
pass for card prose; the rail's focus rule for when the card that owns the
reading has been filtered off the board.

Left for the builders: the load-only URLs of the rail and the dialog reader
are worth a line in whichever card carries the product work, because the
real board already treats its URL as live.
