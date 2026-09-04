import type { ReactNode } from "react"

import { Head } from "@/components/agents-kit"
import { BrandMark, type BrandId } from "@/components/brand-marks"
import { cn } from "@/lib/utils"

/* The store half of the claim: one map of where everything goes, and what
 * each place is for.
 *
 * Left column: the real directory, indented the way the filesystem indents it,
 * with the file-type mark on the rows that are files. Right column: the
 * purpose, then the count. The purpose column is the argument, and it has to
 * read straight down on its own — cover the paths and you still learn what is
 * being proposed. A tree without that column is a `tree` dump, and a `tree`
 * dump is not a proposal.
 *
 * Five of the rows are not files at all. `frontmatter`, `artifacts:` and the
 * three `##` sections live INSIDE one card file, so they sit in the one
 * hairline window on the figure, the kit's shape for a file opened. "There is
 * a place for each kind of thing inside one file" is half of what is being
 * claimed, and a flat indent would have made those sections look like siblings
 * of the card rather than its contents. They carry no file-type mark, because
 * they are not files. The window is full-bleed rather than inset so the three
 * columns keep one set of gridlines from the first row to the last; depth is
 * carried by the label's own indent, which is where a filesystem carries it.
 *
 * The one accent does one job: the `<id>` stem, in the card's filename and
 * again in the directory beside it. Nothing joins those two — no field, no
 * link, no registry. The shared stem IS the join, which is the mechanism at
 * loader.py:494 set as type.
 *
 * The arithmetic closes, and it is meant to: board.yaml and SKILL.md are 2,
 * the top level of cards/ is 41, the seven workspaces hold 41, and the store
 * is 84. _TEMPLATE.md is on the figure for that reason and for one more — it
 * is the only row that shows a rule instead of a place. Nothing marks it as
 * not-a-card except the underscore in its name (loader.py:186).
 *
 * Every count measured on `origin/board`, at the tree that branch carries:
 *
 *   git ls-tree -r --long origin/board -- folio-agents/board
 *     -> 84 blobs, 1013335 bytes summed; SKILL.md is 12843 of them
 *   board.yaml            -> 5 columns; in-progress and in-review carry limit: 3
 *   cards/ top level      -> 41 .md and 7 directories, 48 entries
 *   cards/*.md            -> 41, less _TEMPLATE.md = 40 cards
 *   SKILL.md              -> 283 lines, 12,843 bytes ("1 file" was a count of
 *                            the row it was written on)
 *   frontmatter           -> docs/agents/board/formats.md documents 16 keys an
 *                            author writes and the loader reads (`project` is
 *                            excluded there: it is assigned, never authored);
 *                            13 of the 16 are set by at least one card here
 *   artifacts:            -> 20 entries over the 40 cards. 18 of them (11
 *                            file:, 7 doc:) name a file that is already in the
 *                            card's own directory and add a label to it; 2 are
 *                            url:. No card on this board carries a pr: or an
 *                            api: entry, so the row leads with the case that
 *                            is nine tenths of it.
 *   ## Acceptance criteria-> 250 checkboxes, 139 with an x
 *   ## Comments           -> 27 bullet lines on 18 cards (the template's
 *                            Comments section is commented out, so the
 *                            template is not one of them)
 *   ## Trail              -> 111 bullet lines on 38 cards
 *   cards/<id>/           -> 7 directories, 41 files inside them
 *
 * "curation is placement" is verbatim from docs/agents/board/agents.md and
 * "a comment argues, the trail records" verbatim from cards/_TEMPLATE.md.
 * Neither is reworded, because both are better than anything written for a
 * landing page. */

type Count = { main: string; sub?: string }

type Line = {
  /** The literal path, or the name of a region inside a file. */
  label: ReactNode
  depth: number
  /** Files carry their type mark. Directories and regions do not. */
  mark?: BrandId
  purpose: ReactNode
  count?: Count
  /** Drawn under the count, where a caption sits under a figure. */
  chart?: ReactNode
  /** Quieter: true of the row that is on the figure to explain an arithmetic. */
  aside?: boolean
}

const CARDS = 40

/* "16 fields, 13 ever set" is a shape, not a pair of numbers, so the row draws
 * it: one column per field the loader reads, height is the share of the forty
 * cards that set it. Recounted from the card files on `origin/board`, each
 * field counted where a card sets it to something the loader would keep, which
 * is the test at folio_agents/loader.py:270.
 *
 * The empty track is drawn behind every column, so `link`, `order` and `track`
 * read as three fields nothing uses rather than as three columns that failed
 * to render. Those three are the reason the chart is here: the format defines
 * more than this board needs, and the shortfall is visible instead of stated.
 * No bar takes the accent — the accent on this figure is spent on the `<id>`
 * stem and is not shared. */
const FIELD_USAGE: Array<{ name: string; n: number }> = [
  { name: "title", n: 40 },
  { name: "status", n: 40 },
  { name: "created", n: 40 },
  { name: "tags", n: 40 },
  { name: "milestone", n: 37 },
  { name: "type", n: 36 },
  { name: "size", n: 23 },
  { name: "source", n: 22 },
  { name: "parent", n: 10 },
  { name: "artifacts", n: 9 },
  { name: "assignee", n: 9 },
  { name: "priority", n: 7 },
  { name: "blocked_by", n: 5 },
  { name: "link", n: 0 },
  { name: "order", n: 0 },
  { name: "track", n: 0 },
]

function FieldUsage() {
  return (
    <span
      aria-hidden="true"
      className="mt-1 mb-2 flex h-[26px] w-full max-w-[13rem] items-end gap-[3px] sm:mt-0 sm:mb-2.5"
    >
      {FIELD_USAGE.map((field) => (
        <span
          key={field.name}
          className="flex h-full flex-1 items-end rounded-[1.5px] bg-muted-foreground/15 dark:bg-foreground/[0.09]"
        >
          <span
            className="block w-full rounded-[1.5px] bg-muted-foreground/45 dark:bg-foreground/55"
            style={{ height: `${(field.n / CARDS) * 100}%` }}
          />
        </span>
      ))}
    </span>
  )
}

/** The card id: the one thing on this figure the accent is spent on. */
function Id() {
  return <span className="text-primary">&lt;id&gt;</span>
}

const ABOVE: Line[] = [
  {
    label: "board.yaml",
    depth: 1,
    mark: "yaml",
    purpose: "the columns work moves through, and how many cards may sit in one at a time",
    count: { main: "5 columns", sub: "2 capped at 3" },
  },
  {
    label: "SKILL.md",
    depth: 1,
    mark: "markdown",
    purpose: "the protocol, kept in the repository beside the data it governs",
    count: { main: "283 lines", sub: "12,843 bytes" },
  },
  {
    label: "cards/",
    depth: 1,
    purpose:
      "one flat directory with no index in it. Status is a field on a card, not a folder",
    count: { main: "48 entries", sub: "41 files, 7 directories" },
  },
  {
    label: "_TEMPLATE.md",
    depth: 2,
    mark: "markdown",
    purpose:
      "the shape of a new card. The leading underscore is the whole reason it is not one",
    count: { main: "1 file" },
    aside: true,
  },
]

/** The window. Row one is the file; the rest are inside it. */
const FILE_HEAD: Line = {
  label: (
    <>
      <Id />
      .md
    </>
  ),
  depth: 2,
  mark: "markdown",
  purpose: "one card is one file, and the filename stem is its permanent id",
  count: { main: "40 cards" },
}

const INSIDE: Line[] = [
  {
    label: <span className="font-sans">frontmatter</span>,
    depth: 3,
    purpose: "the machine state, the part a build reads without parsing prose",
    count: { main: "16 fields", sub: "13 ever set" },
    chart: <FieldUsage />,
  },
  {
    label: "artifacts:",
    depth: 4,
    purpose:
      "a label for a file already sitting in the directory, plus the things that are not files at all and so have no directory to sit in",
    count: { main: "20 entries", sub: "18 files, 2 URLs" },
  },
  {
    label: "## Acceptance criteria",
    depth: 3,
    purpose: "what done means, written in boxes rather than in prose",
    count: { main: "250 boxes", sub: "139 ticked" },
  },
  {
    label: "## Comments",
    depth: 3,
    purpose: "the conversation. A comment argues, the trail records",
    count: { main: "27 lines", sub: "18 cards" },
  },
  {
    label: "## Trail",
    depth: 3,
    purpose: "one line per session, appended at the end, oldest first",
    count: { main: "111 lines", sub: "38 cards" },
  },
]

const BELOW: Line[] = [
  {
    label: (
      <>
        <Id />/
      </>
    ),
    depth: 2,
    purpose:
      "what the session produced. Every file at its top level is an artifact, derived, so curation is placement",
    count: { main: "7 workspaces", sub: "41 files" },
  },
]

const STEP = 17

const GRID =
  "grid grid-cols-1 gap-x-8 px-3 sm:grid-cols-[minmax(0,17rem)_minmax(0,1fr)_minmax(0,13rem)] sm:px-4"

function Marked({
  line,
  tone,
}: {
  line: Pick<Line, "depth" | "mark" | "label">
  tone?: string
}) {
  return (
    <div
      className="flex min-w-0 items-start gap-2 pl-[calc(var(--ind)*0.55)] sm:pl-[var(--ind)]"
      style={{ ["--ind" as string]: `${line.depth * STEP}px` }}
    >
      <span className="flex h-5 w-[17px] shrink-0 items-center">
        {line.mark ? (
          <BrandMark
            id={line.mark}
            className={cn("size-[15px]", tone ?? "text-muted-foreground/70")}
          />
        ) : null}
      </span>
      <span
        className="min-w-0 font-mono text-[12.5px] leading-5 break-words text-foreground/85"
        style={{
          fontFeatureSettings: '"liga" 0, "calt" 0',
          fontVariantLigatures: "none",
        }}
      >
        {line.label}
      </span>
    </div>
  )
}

function Measurement({ count, strong }: { count?: Count; strong?: boolean }) {
  if (!count) return <span className="hidden sm:block" />
  return (
    <p className="m-0 pb-3.5 text-[12px] leading-5 text-muted-foreground tabular-nums sm:py-3.5 sm:text-right">
      <span className={strong ? "text-foreground" : "text-foreground/80"}>
        {count.main}
      </span>
      {count.sub ? (
        <>
          <span className="mx-1.5 text-muted-foreground/45">&middot;</span>
          {count.sub}
        </>
      ) : null}
    </p>
  )
}

function MapRow({ line, last = false }: { line: Line; last?: boolean }) {
  return (
    <div className={cn(GRID, !last && "border-b border-border/50")}>
      <div className="pt-3.5 pb-1 sm:py-3.5">
        <Marked
          line={line}
          tone={line.aside ? "text-muted-foreground/45" : undefined}
        />
      </div>
      <p
        className={cn(
          "m-0 pb-1 text-[14.5px] leading-[1.5] sm:py-3.5",
          line.aside ? "text-muted-foreground" : "text-foreground"
        )}
      >
        {line.purpose}
      </p>
      <Measurement count={line.count} />
    </div>
  )
}

export function AgentsStoreMap() {
  return (
    <>
      <Head
        title="The format says where things go,"
        muted="so there is nothing to configure."
        lead="Each line below is a place, and what the place is for is written beside it. The counts are this board today."
      />

      <figure
        className="not-prose m-0 mt-11 min-w-0 sm:mt-14"
        aria-label="A map of the board directory. folio-agents/board holds board.yaml, which declares five columns with two capped at three; SKILL.md, the protocol, 283 lines and 12,843 bytes; and cards, a flat directory of 48 entries. Inside cards: _TEMPLATE.md, kept off the board by its leading underscore; and one file per card, 40 of them. Inside one card file: frontmatter, sixteen fields the format defines and thirteen ever set here, drawn as a column per field; holding an artifacts block of twenty entries, eighteen of them naming a file in the card's own directory and two a URL; Acceptance criteria, 250 boxes with 139 ticked; Comments, 27 lines on 18 cards; Trail, 111 lines on 38 cards. Beside the card file, a directory sharing its id holds what the session produced, 41 files across 7 workspaces. The whole store is 84 files and 1,013,335 bytes in git."
      >
        <div className={cn(GRID, "border-t border-border/60 pt-4 pb-3")}>
          <p className="m-0 flex min-w-0 items-center gap-2">
            <span aria-hidden="true" className="h-5 w-[17px] shrink-0" />
            <span className="font-mono text-[12.5px] leading-5 text-muted-foreground">
              folio-agents/board/
            </span>
          </p>
        </div>

        {ABOVE.map((line, index) => (
          <MapRow key={index} line={line} last={index === ABOVE.length - 1} />
        ))}

        {/* One file, opened. The hairline window is the kit's shape for a file,
            and it is the only box on the figure because it is the only thing
            here with an inside. A row list has no inside; a file does. */}
        <div className="my-2 overflow-hidden rounded-lg border border-border/70 bg-card dark:bg-muted/60">
          <div
            className={cn(
              GRID,
              "border-b border-border/60 bg-muted/40 dark:bg-muted/25"
            )}
          >
            <div className="pt-3.5 pb-1 sm:py-3.5">
              <Marked line={FILE_HEAD} tone="text-foreground/60" />
            </div>
            <p className="m-0 pb-1 text-[14.5px] leading-[1.5] font-medium text-foreground sm:py-3.5">
              {FILE_HEAD.purpose}
            </p>
            <Measurement count={FILE_HEAD.count} strong />
          </div>

          {INSIDE.map((line, index) => (
            <div
              key={index}
              className={cn(
                GRID,
                index < INSIDE.length - 1 && "border-b border-border/40"
              )}
            >
              <div className="pt-3 pb-1 sm:py-3">
                <Marked line={line} />
              </div>
              <p className="m-0 pb-1 text-[14.5px] leading-[1.5] text-foreground sm:py-3">
                {line.purpose}
              </p>
              <div className="flex flex-col pb-3 sm:items-end sm:py-3">
                {line.chart}
                <p className="m-0 text-[12px] leading-5 text-muted-foreground tabular-nums sm:text-right">
                  <span className="text-foreground/80">{line.count?.main}</span>
                  {line.count?.sub ? (
                    <>
                      <span className="mx-1.5 text-muted-foreground/45">
                        &middot;
                      </span>
                      {line.count.sub}
                    </>
                  ) : null}
                </p>
              </div>
            </div>
          ))}
        </div>

        {BELOW.map((line, index) => (
          <MapRow key={index} line={line} last />
        ))}

        <div className={cn(GRID, "border-t border-border pt-4 pb-4 sm:pt-5 sm:pb-5")}>
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-5 w-[17px] shrink-0 items-center">
              <BrandMark id="git" className="size-[15px] text-foreground/60" />
            </span>
            <span className="font-mono text-[12.5px] leading-5 text-foreground/85">
              folio-agents/board/
            </span>
          </div>
          <p className="m-0 mt-1 text-[14.5px] leading-[1.5] text-muted-foreground sm:mt-0">
            everything above, in git
          </p>
          <p className="m-0 mt-1 text-[12.5px] leading-5 text-muted-foreground tabular-nums sm:mt-0 sm:text-right">
            <span className="text-foreground">84 files</span>
            <span className="mx-1.5 text-muted-foreground/45">&middot;</span>
            1,013,335 bytes
          </p>
        </div>
      </figure>
    </>
  )
}
