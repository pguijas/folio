"use client"

import { BrandMark } from "@/components/brand-marks"

import styles from "./agents-hero-chat.module.css"

/* "Ask, and it is published."
 *
 * The Docs landing's heartbeat, one substitution deep. There, a person types
 * `folio serve` into a terminal and the terminal lifts to show the served
 * site. Here, a person asks an assistant for something, the assistant runs
 * `folio board comment`, and the same shutter lifts to show the same address
 * serving the board with that comment already in the card's thread. The
 * argument is the parallel: one product turns a command into a site, the other
 * turns a conversation into a file that outlives the session, and both end at
 * localhost:4321.
 *
 * Everything readable is verbatim.
 *
 * The message is the first of four comments on
 * `folio-agents/board/cards/artifact-viewer-becomes-a-workspace.md`, dated
 * 2026-08-29 and signed @pguijas, read with
 *   git show origin/board:folio-agents/board/cards/artifact-viewer-becomes-a-workspace.md
 *
 * The commands are the CLI's own: `folio board comment CARD_ID TEXT --by NAME
 * --commit` and `folio board check`, from folio_agents/cli_commands.py. So are
 * their echoes. `comment:` prints the entry the writer formatted, leading dash
 * and all (`- {date} @{actor}: {text}`, edit.py:81); `--commit` then prints
 * `committed: board: comment on {card_id}` (ops.py:341, cli_commands.py:129);
 * `check` prints `Board OK: {cards} cards across {columns} columns` (:536),
 * which on this board is 40 across 5.
 *
 * The board under the shutter is the page this repository actually serves. It
 * was read at
 *   localhost:4321/kanban/?q=project:agents&card=artifact-viewer-becomes-a-workspace
 * which returns 200, and it is drawn from that render: the filter field
 * holding the expression, the rail with its status and priority counts and the
 * project select the expression set, two of the five columns, and the card
 * open as a right drawer with its description, its nine ticked criteria, its
 * four comments and its two artifacts. The marks are the board's own, on its
 * own 16-unit pen (kanban-board.tsx:1885-1990).
 *
 * Only three actors have ever written to these files. The one drawn here is
 * Claude, by its own mark, and it is evidence rather than decoration.
 *
 * No JavaScript: the whole timeline is keyframes on one cycle in
 * lab-assist-c.module.css, so it cannot desynchronise and there is nothing to
 * run before hydration. */

/** The owner's comment, whole. The command below quotes it cut, at a word
 * boundary, with the cut marked. */
const MESSAGE =
  "Canvas is the center element, filters stay on the left, and the card is a right drawer. Use small dividing lines, not window-like panels; everything should resize and close."

/** The rail's status counts, as the filtered board prints them: the 40 cards
 * of the agents board, by column. */
const STATUS: Array<[string, number]> = [
  ["Ideas", 9],
  ["Backlog", 8],
  ["In progress", 1],
  ["In review", 1],
  ["Released", 21],
]

/** The two artifacts on the card, in the order the drawer lists them: the
 * label from the frontmatter, then the file it resolves to. */
const ARTIFACTS: Array<[string, string, string]> = [
  ["doc", "Progressive canvas direction", "progressive-canvas-direction.md"],
  [
    "file",
    "Progressive canvas (revised direction)",
    "progressive-canvas.html",
  ],
]

/** The board's own pen: one 16-unit grid, stroke 1.5, so a filter mark and a
 * paperclip carry identical ink. Copied, not imported: this panel is in the
 * site theme and the board ships with the plugin. */
function Glyph({ d, className }: { d: string; className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d={d} />
    </svg>
  )
}

const FILTER_D = "M2.5 4h11M4.5 8h7M6.5 12h3"
const CHEVRON_D = "m4 6 4 4 4-4"
const BUBBLE_D =
  "M14 10a1.33 1.33 0 0 1-1.33 1.33H4.67L2 14V3.33A1.33 1.33 0 0 1 3.33 2h9.34A1.33 1.33 0 0 1 14 3.33z"
const CLIP_D =
  "m14.3 7.4-6.1 6.1a4 4 0 0 1-5.7-5.7l5.7-5.7a2.7 2.7 0 0 1 3.8 3.8L6.3 11.6a1.3 1.3 0 0 1-1.9-1.9l5.7-5.6"
const DOC_D = "M9 2H4.5v12h7V4.5M9 2l2.5 2.5M9 2v2.5h2.5M6.5 9.5h3M6.5 12h3"
const FILE_D = "M9 2H4.5v12h7V4.5M9 2l2.5 2.5M9 2v2.5h2.5"
const CHECK_D = "M3 8.5 6.5 12 13 4.5"
const CLOSE_D = "M12 4 4 12M4 4l8 8"

/** One of the rail's selects, at the value the filtered board shows. */
function Select({ label, value }: { label: string; value: string }) {
  return (
    <>
      <FacetHead>{label}</FacetHead>
      <span className="mt-1.5 flex items-center gap-1 rounded-[5px] border border-border bg-background px-1.5 py-1">
        <span className="min-w-0 flex-1 truncate text-[9.5px] leading-4 text-foreground">
          {value}
        </span>
        <Glyph
          d={CHEVRON_D}
          className="size-[9px] flex-none text-muted-foreground"
        />
      </span>
    </>
  )
}

function FacetRow({ label, count }: { label: string; count: number }) {
  return (
    <span className="flex items-center gap-1.5 py-[2px]">
      <span
        aria-hidden="true"
        className="size-[8px] flex-none rounded-[2px] border border-border"
      />
      <span className="min-w-0 flex-1 truncate text-[9.5px] leading-4 text-muted-foreground">
        {label}
      </span>
      <span className="text-[9px] leading-4 text-muted-foreground/70">
        {count}
      </span>
    </span>
  )
}

function FacetHead({ children }: { children: string }) {
  return (
    <p className="m-0 text-[8px] font-semibold tracking-[0.1em] text-muted-foreground/80 uppercase">
      {children}
    </p>
  )
}

function SectionHead({
  d,
  label,
  count,
  right,
  rule = false,
}: {
  d: string
  label: string
  count?: number
  right?: string
  rule?: boolean
}) {
  return (
    <span
      className={`flex items-center gap-1.5 pb-1 ${rule ? "border-b border-primary/35" : ""}`}
    >
      <Glyph d={d} className="size-[9px] flex-none text-muted-foreground" />
      <span className="flex-1 text-[8px] font-semibold tracking-[0.1em] text-muted-foreground uppercase">
        {label}
        {count !== undefined ? (
          <span className="text-muted-foreground/70"> &middot; {count}</span>
        ) : null}
      </span>
      {right ? (
        <span className="font-mono text-[8.5px] leading-4 text-primary">
          {right}
        </span>
      ) : null}
    </span>
  )
}

function BoardCard({
  title,
  open = false,
  spare = false,
}: {
  title: string
  open?: boolean
  spare?: boolean
}) {
  return (
    <span
      className={`${spare ? `${styles.spare} ` : ""}${
        open
          ? "block rounded-[5px] border border-primary/45 bg-primary/[0.07] px-2 py-1.5 text-[9.5px] leading-[1.4] font-semibold text-foreground"
          : "block rounded-[5px] border border-border bg-background px-2 py-1.5 text-[9.5px] leading-[1.4] text-muted-foreground"
      }`}
    >
      {title}
    </span>
  )
}

function Column({
  name,
  count,
  children,
}: {
  name: string
  count: number
  children: React.ReactNode
}) {
  return (
    <div className="flex min-w-0 flex-col">
      <span className="flex items-baseline justify-between border-b border-border pb-1">
        <span className="text-[8px] font-semibold tracking-[0.1em] text-muted-foreground uppercase">
          {name}
        </span>
        <span className="text-[9px] text-muted-foreground/70">{count}</span>
      </span>
      <span className="mt-2 flex flex-col gap-1.5">{children}</span>
    </div>
  )
}

export function AgentsHeroChat() {
  return (
    <figure
      className={styles.root}
      aria-label="One window. Over it, a conversation: the owner asks for the canvas in the centre, the filters on the left and the card as a right drawer, and the assistant answers by running folio board comment on that card with --commit, printing the comment line the CLI writes and the board: commit it made, then folio board check, which prints Board OK: 40 cards across 5 columns. The conversation then lifts away like a shutter and the window's title changes from the session to the address it published to, revealing the board the build serves there: the filter expression, the rail counting the columns, the columns themselves, and the card open as a right drawer with the same comment now in its thread."
    >
      <div className={styles.window}>
        {/* the strip: the session while the shutter is down, the address it
            published to once it has lifted */}
        <div className={styles.strip}>
          <span className={styles.stripSlot}>
            <span
              className={`${styles.session} font-mono text-[11px] leading-4 text-muted-foreground`}
              aria-hidden="true"
            >
              claude &mdash; ~/folio
            </span>
            <span
              className={`${styles.url} font-mono text-[11px] leading-4 text-muted-foreground`}
            >
              localhost:4321/kanban/?q=project:agents&amp;card=artifact-viewer-becomes-a-workspace
            </span>
          </span>
        </div>

        <div className={styles.stage}>
          {/* ---- the payoff, at rest underneath: the served board -------- */}
          <div className={styles.page}>
            <div className="flex flex-none items-center justify-between border-b border-border px-3 py-2">
              <span className="flex items-center gap-2 text-[11px] font-semibold text-foreground">
                <span
                  aria-hidden="true"
                  className="grid size-[17px] place-items-center rounded-[5px] bg-primary font-mono text-[8px] font-semibold text-primary-foreground"
                >
                  fo
                </span>
                Folio
              </span>
              <span className="text-[10px] text-muted-foreground">
                Documentation
              </span>
            </div>

            <div className={styles.board}>
              {/* the filter rail */}
              <div
                className={`${styles.rail} min-w-0 flex-col border-r border-border bg-muted/30 px-2.5 py-2.5`}
                aria-hidden="true"
              >
                <FacetHead>Status</FacetHead>
                <span className="mt-1 flex flex-col">
                  {STATUS.map(([label, count]) => (
                    <FacetRow key={label} label={label} count={count} />
                  ))}
                </span>

                <span className="my-2 block h-px bg-border" />
                <FacetHead>Priority</FacetHead>
                <span className="mt-1 flex flex-col">
                  <FacetRow label="high" count={7} />
                </span>

                <span className="my-2 block h-px bg-border" />
                <Select label="Project" value="agents" />
                <span className="mt-2.5 block" />
                <Select label="Type" value="any" />

                <span className="mt-auto pt-3 text-[9px] leading-4 text-muted-foreground underline underline-offset-2">
                  Clear the filter
                </span>
              </div>

              {/* the board itself */}
              <div
                className={`${styles.cols} min-w-0 flex-col px-3 py-2.5`}
                aria-hidden="true"
              >
                <span
                  className={`${styles.glint} flex items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1`}
                >
                  <Glyph
                    d={FILTER_D}
                    className="size-[10px] flex-none text-muted-foreground"
                  />
                  <span className="min-w-0 flex-1 truncate font-mono text-[9.5px] leading-4 text-foreground">
                    project:agents
                  </span>
                  <Glyph
                    d={CLOSE_D}
                    className="size-[9px] flex-none text-muted-foreground"
                  />
                  <kbd className="rounded border border-border bg-card px-1 font-mono text-[8px] leading-4 text-muted-foreground">
                    /
                  </kbd>
                </span>

                <div className="mt-3 grid min-h-0 flex-1 grid-cols-2 gap-3">
                  <Column name="Backlog" count={8}>
                    <BoardCard title="The board reads as a tree" />
                    <BoardCard title="A parent says what it breaks into" />
                    <BoardCard title="The table draws one row per card" />
                    <BoardCard title="The tree filters without re-rooting" />
                    <BoardCard title="A parent cycle fails the build" spare />
                  </Column>

                  <Column name="Released" count={21}>
                    <BoardCard
                      title="Artifact viewer becomes a workspace"
                      open
                    />
                    <BoardCard title="Cards carry comments" />
                    <BoardCard title="The card dialog reads like a mail" />
                    <BoardCard title="Artifacts live beside their card" />
                    <BoardCard title="Artifacts read from the canvas" spare />
                  </Column>
                </div>
              </div>

              {/* the card, open */}
              <div
                className={`${styles.drawer} flex min-w-0 flex-col border-l border-border px-3 py-2.5`}
              >
                <span className="flex items-start justify-between gap-2">
                  <span className="text-[11.5px] leading-[1.35] font-semibold text-foreground">
                    Artifact viewer becomes a workspace
                  </span>
                  <kbd className="mt-px flex-none rounded border border-border bg-card px-1 font-mono text-[8px] leading-4 text-muted-foreground">
                    Esc
                  </kbd>
                </span>

                <p className="mt-1.5 mb-0 text-[9px] leading-[1.45] text-muted-foreground">
                  Opening a card should leave floating layers behind and turn
                  the kanban into one &hellip;
                </p>

                <span className="mt-2.5 block">
                  <SectionHead
                    d={CHECK_D}
                    label="Acceptance criteria"
                    right="9 / 9"
                    rule
                  />
                </span>

                <span className="mt-2.5 block">
                  <SectionHead d={BUBBLE_D} label="Comments" count={4} />
                </span>

                {/* the line the conversation left: in the thread at rest, lit
                    for a moment once the shutter is off it */}
                <span className="relative mt-1 block border-l border-border py-1 pl-2">
                  <span
                    aria-hidden="true"
                    className={`${styles.fresh} absolute inset-y-0 right-0 -left-px border-l-2 border-primary bg-primary/[0.07]`}
                  />
                  <span className="relative block font-mono text-[8.5px] leading-4 text-muted-foreground">
                    2026-08-29 @pguijas
                  </span>
                  <span className="relative mt-0.5 block text-[9px] leading-[1.5] text-foreground">
                    {MESSAGE}
                  </span>
                </span>

                <span
                  aria-hidden="true"
                  className="mt-1.5 flex items-center gap-1 pl-2"
                >
                  {[0, 1, 2].map((n) => (
                    <span
                      key={n}
                      className="size-[3px] rounded-full bg-muted-foreground/45"
                    />
                  ))}
                </span>

                <span className="mt-auto block pt-2.5">
                  <SectionHead d={CLIP_D} label="Artifacts" count={2} />
                </span>
                <span className="mt-1.5 flex flex-col gap-1">
                  {ARTIFACTS.map(([kind, label, file]) => (
                    <span
                      key={file}
                      className="flex min-w-0 items-center gap-1.5 rounded-[5px] border border-border bg-background px-1.5 py-1"
                    >
                      <Glyph
                        d={kind === "doc" ? DOC_D : FILE_D}
                        className="size-[11px] flex-none text-muted-foreground"
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[9px] leading-[1.3] font-semibold text-foreground">
                          {label}
                        </span>
                        <span className="block truncate font-mono text-[8px] leading-[1.4] text-muted-foreground">
                          {file}
                        </span>
                      </span>
                    </span>
                  ))}
                </span>
              </div>
            </div>
          </div>

          {/* ---- the shutter: the conversation --------------------------- */}
          <div className={styles.shutter} aria-hidden="true">
            <div className={styles.human}>
              <p
                className={`${styles.bubble} m-0 text-[13.5px] leading-[1.6] text-foreground`}
              >
                {MESSAGE}
              </p>
            </div>

            <div className={styles.agent}>
              <BrandMark
                id="claude"
                className={`${styles.mark} mt-[3px] size-[20px] text-primary`}
              />
              <div className={`${styles.run} font-mono`}>
                <span className={`${styles.line} ${styles.l0}`}>
                  <span className="text-muted-foreground">$ </span>
                  <span
                    className={`${styles.typed} font-semibold text-foreground`}
                  >
                    folio board comment artifact-viewer-becomes-a-workspace \
                  </span>
                  <span className={styles.caretSlot}>
                    <span className={styles.caret} />
                  </span>
                </span>
                <span
                  className={`${styles.line} ${styles.l1} font-semibold text-foreground`}
                >
                  {
                    '    "Canvas is the center element, filters stay on the left, and …" \\'
                  }
                </span>
                <span
                  className={`${styles.line} ${styles.l2} font-semibold text-foreground`}
                >
                  {"    --by pguijas --commit"}
                </span>

                <span className={`${styles.line} ${styles.l3} ${styles.gap}`}>
                  <span className="font-semibold text-primary">comment:</span>
                  <span className="text-muted-foreground">
                    {
                      " - 2026-08-29 @pguijas: Canvas is the center element, filters …"
                    }
                  </span>
                </span>
                <span className={`${styles.line} ${styles.l4}`}>
                  <span className="font-semibold text-primary">committed:</span>
                  <span className="text-muted-foreground">
                    {" board: comment on artifact-viewer-becomes-a-workspace"}
                  </span>
                </span>

                <span className={`${styles.line} ${styles.l5} ${styles.gap}`}>
                  <span className="text-muted-foreground">$ </span>
                  <span className="font-semibold text-foreground">
                    folio board check
                  </span>
                </span>
                <span className={`${styles.line} ${styles.l6}`}>
                  <span className="font-semibold text-primary">Board OK:</span>
                  <span className="text-muted-foreground">
                    {" 40 cards across 5 columns"}
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </figure>
  )
}
