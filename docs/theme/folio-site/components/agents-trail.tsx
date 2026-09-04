import { BrandMark } from "@/components/brand-marks"
import { Dot, Frame, Head, Path } from "@/components/agents-kit"
import { cn } from "@/lib/utils"

/* One card, read down its own history.
 *
 * Everything printed here is `folio-agents/board/cards/artifacts-live-beside-
 * their-card.md` on branch `board`, read with `git show`. The frontmatter block
 * gives the title, the status, the created date, the type, the size and the
 * milestone. The six rows are that card's `## Trail`, verbatim and complete:
 * nothing is cut, so no ellipsis is needed. Each source line is written
 * `- <date> @<actor>[ (<ref>)]: <text>`, which is why a row can carry a date
 * column, an actor column and a branch without any of it being rewritten — the
 * card already stores it that way.
 *
 * The left column is time, not decoration. A row's own height is set by its
 * text, but the space between two rows is set by the days between them, at a
 * fixed pixels-per-day (`--day`). So the 22 August that nobody touched and the
 * five days between 24 and 29 August are drawn as the voids they were, and the
 * two lines written on 20 August sit flush against each other. The rule is
 * solid through a row and dashed through a gap: solid means the file was
 * written, dashed means it sat there.
 *
 * Mono is literal text only — the path, the dates, the handles, the branch
 * names, the frontmatter values. The trail prose, the durations in the gutter
 * and the counts underneath are sans, because none of those are things you
 * could type.
 *
 * The two marks are evidence, not badges: Claude wrote four of these lines and
 * Codex wrote two, and the repository says so. Nothing else is implied. */

type Line = {
  /** Days since the line above. Drives the height of the gap above the row. */
  gap: number
  date: string
  mark: "claude" | "codex"
  handle: string
  /** The branch or release the card records for that line, where it records one. */
  ref?: string
  text: string
}

const TRAIL: Line[] = [
  {
    gap: 0,
    date: "2026-08-20",
    mark: "claude",
    handle: "@claude",
    text: "found while attaching prototypes — every artifact resolved to a 404; owner directed the docs asset model, one abstraction level up",
  },
  {
    gap: 0,
    date: "2026-08-20",
    mark: "claude",
    handle: "@claude",
    text: "repo links removed board-wide, so the 404 is gone and only reachability is left; shape B placed by hand on the epic, A vs B still open",
  },
  {
    gap: 1,
    date: "2026-08-21",
    mark: "claude",
    handle: "@claude",
    text: "shape B shipped — card directories publish at /_folio/kanban/<id>/ and card-local artifacts open; markdown still served as source, artifacts: still hand-listed",
  },
  {
    gap: 2,
    date: "2026-08-23",
    mark: "codex",
    handle: "@codex",
    ref: "feat/artifact-board-poc",
    text: "card Markdown and MDX now enter Folio's normal document pipeline; raw bundles remain intact, and ownership, symlink, collision, base-path, and warm-cleanup cases are pinned by tests",
  },
  {
    gap: 1,
    date: "2026-08-24",
    mark: "claude",
    handle: "@claude",
    text: "every folder route above a published card document now resolves — a marker-tagged card index (its own index.md/README.md wins), a directory page at kanban/ when routes.docs is off, swept by marker through the new list_pages; found when /docs/kanban/<id>/ crashed the dev server under output: export",
  },
  {
    gap: 5,
    date: "2026-08-29",
    mark: "codex",
    handle: "@codex",
    ref: "release/0.3.0",
    text: "all criteria verified on the release branch; reclassified as the 0.3 plugin/artifact pipeline it already ships with.",
  },
]

/** Where the whole board stands, under the one card. */
const TOTALS: Array<{ mark?: "claude" | "codex"; handle: string; count: string }> =
  [
    { mark: "claude", handle: "@claude", count: "79" },
    { mark: "codex", handle: "@codex", count: "19" },
    { handle: "@pguijas", count: "13" },
  ]

/* The gutter, shared by the rows and by the gaps between them, so the rule
   stays on one x for the whole height of the figure. */
function Gutter({
  children,
  className,
}: {
  children?: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        "relative w-20 shrink-0 pr-3 text-right sm:w-[5.25rem] sm:pr-4",
        className
      )}
    >
      {children}
    </div>
  )
}

/** The days the file sat untouched, drawn to the same scale as every other
 * gap: `--day` tall per day, and a dashed rule where a solid one would mean
 * somebody was working. */
function Gap({ days }: { days: number }) {
  return (
    <div
      className="flex"
      style={{ height: `calc(var(--day) * ${days})` }}
      aria-hidden="true"
    >
      <Gutter className="flex items-center justify-end">
        <span className="hidden text-[10.5px] leading-none text-muted-foreground/80 tabular-nums sm:inline">
          {days} {days === 1 ? "day" : "days"}
        </span>
        <span className="absolute inset-y-0 right-0 border-l border-dashed border-border" />
      </Gutter>
    </div>
  )
}

function Entry({
  line,
  first,
  last,
}: {
  line: Line
  first: boolean
  last: boolean
}) {
  return (
    <div className="flex min-w-0">
      <Gutter>
        <span className="font-mono text-[10.5px] leading-[1.6] text-muted-foreground sm:text-[11px]">
          {line.date}
        </span>
        {/* Solid while the file was being written. */}
        <span
          className={cn(
            "absolute right-0 w-px bg-border",
            first ? "top-[9px]" : "top-0",
            last ? "h-[9px]" : "bottom-0"
          )}
          aria-hidden="true"
        />
        <span
          className={cn(
            "absolute -right-[3px] top-[6px] size-[7px] rounded-full ring-4 ring-background",
            last ? "bg-primary" : "bg-foreground/70"
          )}
          aria-hidden="true"
        />
      </Gutter>

      <div className="grid min-w-0 flex-1 grid-cols-1 gap-x-6 pb-4 pl-4 sm:grid-cols-[10.5rem_minmax(0,1fr)] sm:pl-5">
        <div className="min-w-0">
          <p className="m-0 flex items-center gap-2">
            <BrandMark
              id={line.mark}
              className="size-[17px] shrink-0 text-foreground"
            />
            <span className="truncate font-mono text-[12.5px] leading-[1.5] font-medium text-foreground">
              {line.handle}
            </span>
          </p>
          {line.ref ? (
            <p className="m-0 mt-1.5 flex items-center gap-2 text-muted-foreground">
              <BrandMark id="git" className="size-[14px] shrink-0 opacity-70" />
              <span className="truncate font-mono text-[10.5px] leading-[1.5]">
                {line.ref}
              </span>
            </p>
          ) : null}
        </div>

        <p className="col-start-1 m-0 mt-2 min-w-0 max-w-[47rem] text-[13.5px] leading-[1.65] text-foreground sm:col-start-2 sm:mt-0">
          {line.text}
        </p>
      </div>
    </div>
  )
}

export function AgentsTrail() {
  return (
    <div>
      <Head
        title="One card's trail, six sessions long,"
        muted="written by two tools across ten days."
        lead="The map's ## Trail row, opened on one card: one line per session. These six lines are unedited."
      />

      <figure
        className="m-0 mt-12 sm:mt-14"
        aria-label="The trail of the card artifacts-live-beside-their-card.md, released, on branch board. Six dated lines run down a time axis from 20 August 2026 to 29 August 2026. Claude Code wrote 20 August twice, 21 August and 24 August. Codex wrote 23 August on branch feat/artifact-board-poc and 29 August on release/0.3.0. The axis is solid through each line and dashed through the days nobody wrote, including the five days between 24 and 29 August. Across the whole board there are 111 trail lines on 38 cards: 79 by @claude, 19 by @codex, 13 by @pguijas."
      >
        <Frame
          title={
            <span className="flex items-center gap-2">
              <BrandMark
                id="markdown"
                className="size-[16px] shrink-0 text-muted-foreground"
              />
              <span className="truncate">
                <span className="hidden text-muted-foreground/70 sm:inline">
                  folio-agents/board/cards/
                </span>
                <span className="text-foreground">
                  artifacts-live-beside-their-card.md
                </span>
              </span>
            </span>
          }
          right={<span className="font-sans">on branch board</span>}
          bodyClassName="px-0 py-0 font-sans text-[13.5px] leading-normal text-foreground"
        >
          <div className="border-b border-border/60 px-5 py-5 sm:px-7">
            <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
              <h3 className="m-0 min-w-0 text-[17px] leading-[1.3] font-semibold text-foreground">
                Artifacts live beside their card
              </h3>
              <p className="m-0 flex shrink-0 items-center gap-2 text-[12.5px] leading-5 font-medium text-primary">
                <span
                  aria-hidden="true"
                  className="size-[6px] rounded-full bg-primary"
                />
                released
              </p>
            </div>
            <p className="m-0 mt-2.5 text-[11.5px] leading-5 text-muted-foreground tabular-nums">
              created <Path>2026-08-20</Path>
              <Dot />
              type <Path>feature</Path>
              <Dot />
              size <Path>L</Path>
              <Dot />
              milestone <Path>0.1</Path>
              <Dot />
              15 of 15 acceptance criteria ticked
            </p>
          </div>

          <div className="px-5 py-6 [--day:11px] sm:px-7 sm:py-7 sm:[--day:24px]">
            <p className="m-0 mb-5 font-mono text-[11px] leading-none text-muted-foreground/70">
              ## Trail
            </p>
            {TRAIL.map((line, index) => (
              <div key={line.date + line.text.slice(0, 24)}>
                {index > 0 && line.gap > 0 ? <Gap days={line.gap} /> : null}
                <Entry
                  line={line}
                  first={index === 0}
                  last={index === TRAIL.length - 1}
                />
              </div>
            ))}
          </div>
        </Frame>

        <figcaption className="mt-6 flex flex-wrap items-baseline justify-between gap-x-10 gap-y-3 border-t border-border/60 pt-5">
          <p className="m-0 text-[13px] leading-6 text-muted-foreground">
            Six of the{" "}
            <span className="font-medium text-foreground tabular-nums">111</span>{" "}
            trail lines the board carries, across{" "}
            <span className="font-medium text-foreground tabular-nums">38</span>{" "}
            cards.
          </p>
          <ul className="m-0 flex list-none flex-wrap items-center gap-x-7 gap-y-2 p-0">
            {TOTALS.map((actor) => (
              <li
                key={actor.handle}
                className="flex items-center gap-2 text-[13px] leading-6"
              >
                {actor.mark ? (
                  <BrandMark
                    id={actor.mark}
                    className="size-[16px] shrink-0 text-muted-foreground"
                  />
                ) : (
                  <span
                    aria-hidden="true"
                    className="size-[16px] shrink-0"
                  />
                )}
                <span className="font-mono text-[12px] text-muted-foreground">
                  {actor.handle}
                </span>
                <span className="font-medium text-foreground tabular-nums">
                  {actor.count}
                </span>
              </li>
            ))}
          </ul>
        </figcaption>
      </figure>
    </div>
  )
}
