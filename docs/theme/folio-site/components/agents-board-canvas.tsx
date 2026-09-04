import type { ReactNode } from "react"

import { Dot, Head, Meta } from "@/components/agents-kit"

/* Folio's own agents board, drawn at landing scale.
 *
 * This is the page's last body section and it carries its own heading, because
 * without one it read as the roadmap's illustration. The claim it makes is not
 * "here is the board": it is that a column is a reading. `status` is one field
 * in a card's frontmatter, `board.yaml` names the five buckets, and grouping by
 * that field is all a column is. Nothing below is stored anywhere but in the
 * same forty Markdown files the rest of the page has been reading.
 *
 * Every title, status, milestone, type, size, assignee and blocker below was
 * read out of `folio-agents/board/cards/` on the `board` branch, and the
 * column set with its two WIP limits of 3 is `board.yaml` verbatim. The status
 * tally over the forty card files is ideas 9, backlog 8, in-progress 1,
 * in-review 1, released 21, so the residue counts are what each column is
 * holding back rather than a round number. Fifteen of the forty are drawn:
 * enough that the board reads as a board, few enough to stay legible here.
 *
 * The drawing is one hairline object with hairlines between the columns. A
 * card is a title and a quiet line of chips under it, separated from the next
 * card by space and not by a box, because forty small boxes inside five boxes
 * inside one box is the shape this page is getting away from.
 *
 * Mono is spent on the three things here that are literal text: the path in
 * the header, the card ids a blocked card names, and the command and its reply
 * in the foot. Counts, column names, types, sizes and the milestone numeral
 * are description, so they are sans with tabular figures. */

type BoardCard = {
  title: string
  milestone?: string
  type?: string
  size?: string
  /** `assignee` is a scalar or a list in the frontmatter; both come in here as
   * the names in order. */
  assignees?: string[]
  /** Every id in `blocked_by`, printed in full. The line clamps at three
   * lines, so an ellipsis appears only where the column really runs out of
   * room, which at full width it does not. */
  blockedBy?: string[]
}

type BoardColumn = {
  title: string
  /** The real number of cards with this status. */
  count: number
  /** From `board.yaml`. Only the two middle columns declare one. */
  limit?: number
  cards: BoardCard[]
}

const columns: BoardColumn[] = [
  {
    title: "Ideas",
    count: 9,
    cards: [
      {
        title: "Browser edits for a git-backed board",
        milestone: "0.2",
        type: "feature",
        size: "L",
      },
      { title: "Project OS technical plan", milestone: "0.2", type: "plan" },
      {
        title: "How a published board accepts a change",
        milestone: "0.2",
        type: "plan",
      },
      { title: "A network for agent harnesses" },
    ],
  },
  {
    title: "Backlog",
    count: 8,
    cards: [
      {
        title: "Folio board: the rename and the merge",
        milestone: "0.2",
        type: "feature",
        size: "XL",
        blockedBy: ["the-board-takes-the-name-and-absorbs-the-roadmap"],
      },
      {
        title: "The board reads as a tree",
        milestone: "0.2",
        type: "feature",
        size: "XL",
      },
      {
        title: "The table draws one row per card",
        milestone: "0.2",
        type: "feature",
        size: "L",
        blockedBy: ["the-table-is-a-second-view", "a-parent-cycle-fails-the-build"],
      },
      {
        title: "A parent cycle fails the build",
        milestone: "0.2",
        type: "bug",
        size: "S",
      },
    ],
  },
  {
    title: "In progress",
    count: 1,
    limit: 3,
    cards: [
      {
        title: "Folio for Agents 0.1 release",
        milestone: "0.1",
        type: "release",
        size: "L",
        assignees: ["codex"],
      },
    ],
  },
  {
    title: "In review",
    count: 1,
    limit: 3,
    cards: [
      {
        title: "Folio for Agents release cadence",
        milestone: "0.1",
        type: "release",
        size: "L",
      },
    ],
  },
  {
    title: "Released",
    count: 21,
    cards: [
      {
        title: "Artifacts live beside their card",
        milestone: "0.1",
        type: "feature",
        size: "L",
      },
      {
        title: "Artifacts read from the canvas",
        milestone: "0.1",
        type: "feature",
        size: "L",
      },
      {
        title: "The card dialog reads like a mail",
        milestone: "0.1",
        type: "feature",
        size: "M",
        assignees: ["claude"],
      },
      { title: "folio serve watches the board", milestone: "0.1", type: "bug" },
      {
        title: "Cards carry assignees, a source, and a size",
        milestone: "0.1",
        type: "feature",
        size: "L",
        assignees: ["peter", "claude"],
      },
    ],
  },
]

/** The thin separator inside a chip line. Quieter than the text it divides. */
function Sep() {
  return (
    <span aria-hidden="true" className="text-border">
      &middot;
    </span>
  )
}

function Card({ card }: { card: BoardCard }) {
  const chips: ReactNode[] = []
  if (card.milestone) {
    chips.push(
      <span key="milestone" className="text-foreground">
        {card.milestone}
      </span>
    )
  }
  if (card.type) chips.push(<span key="type">{card.type}</span>)
  if (card.size) {
    chips.push(
      <span key="size" className="tabular-nums">
        {card.size}
      </span>
    )
  }
  if (card.assignees?.length) {
    chips.push(
      <span key="assignee" className="text-primary">
        {card.assignees.map((name) => `@${name}`).join(" ")}
      </span>
    )
  }

  return (
    <article className="min-w-0">
      <p className="m-0 text-[12.5px] leading-[1.4] font-medium text-balance text-foreground lg:text-[13.5px]">
        {card.title}
      </p>
      {chips.length ? (
        <p className="m-0 mt-1.5 flex flex-wrap items-center gap-x-1.5 text-[10.5px] leading-[1.6] text-muted-foreground tabular-nums">
          {chips.map((chip, index) => (
            <span key={index} className="flex items-center gap-x-1.5">
              {index > 0 ? <Sep /> : null}
              {chip}
            </span>
          ))}
        </p>
      ) : null}
      {card.blockedBy?.length ? (
        <p className="m-0 mt-1.5 line-clamp-3 text-[10.5px] leading-[1.5] text-muted-foreground">
          blocked by{" "}
          {/* The ids are the card filenames, so they stay mono; the two
              words in front of them are not. */}
          <span className="font-mono text-[10px]">
            {card.blockedBy.join(", ")}
          </span>
        </p>
      ) : null}
    </article>
  )
}

export function AgentsBoardCanvas() {
  return (
    <>
      <Head
        title="The board is one reading of these files,"
        muted="not the product."
        lead="Status is one field in a card's frontmatter. A column is what a reader makes of that field, so the board below is the same forty Markdown files the rest of this page describes, grouped by it."
      />

      <figure
        /* The board wants 900px of inner width, which no phone has. Rather
           than cut it off inside a rounded corner, where the cut reads as the
           end of the object, it runs to the edge of the screen below `lg` and
           takes its rounding and its side rules back once it fits. */
        className="not-prose mt-12 mb-0 -mx-6 overflow-hidden border-y border-border/70 bg-card sm:mt-14 lg:mx-0 lg:rounded-xl lg:border-x"
        aria-label="Folio's agents board on the board branch. 40 cards across five columns: Ideas 9, Backlog 8, In progress 1 against a limit of 3, In review 1 against a limit of 3, Released 21. Fifteen cards are drawn with their milestone, type, size, assignee and blockers, and each column prints the count it is holding back."
      >
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-border/60 px-4 py-3.5 sm:px-5">
          <p className="m-0 flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="text-[13.5px] leading-5 font-semibold text-foreground">
              Folio for Agents
            </span>
            <span className="font-mono text-[11px] leading-5 text-muted-foreground">
              folio-agents/board/cards/
            </span>
          </p>
          <p className="m-0 text-[11.5px] leading-5 text-muted-foreground tabular-nums">
            40 cards &middot; 5 columns
          </p>
        </div>

        {/* The board is wider than a phone. It scrolls sideways instead of
            being cropped: clipping it hid three of the five columns. */}
        <div className="overflow-x-auto">
          {/* The two WIP-limited columns hold one card each, so they take
              less width than the three that are full. */}
          <div
            className="grid min-w-[900px] divide-x divide-border/60"
            style={{
              gridTemplateColumns: "1fr 1fr 0.78fr 0.78fr 1fr",
            }}
          >
            {columns.map((column) => (
              <div key={column.title} className="flex min-w-0 flex-col">
                <div className="flex items-baseline justify-between gap-2 px-3 pt-3.5 pb-3 lg:px-4">
                  <span className="truncate text-[12.5px] leading-5 font-semibold tracking-tight text-foreground">
                    {column.title}
                  </span>
                  <span
                    className={`shrink-0 text-[11px] leading-5 font-medium tabular-nums ${
                      column.limit ? "text-primary" : "text-muted-foreground"
                    }`}
                  >
                    {column.limit
                      ? `${column.count}/${column.limit}`
                      : column.count}
                  </span>
                </div>
                <div className="flex flex-1 flex-col gap-y-5 px-3 pt-1 pb-3.5 lg:px-4">
                  {column.cards.map((card) => (
                    <Card key={card.title} card={card} />
                  ))}
                  {/* Room the column is declared to have and is not using.
                      It sits at the foot of the column so the two limited
                      columns line up with each other and with the counts the
                      other three print there. */}
                  {column.limit ? (
                    <div className="mt-auto flex flex-col gap-y-2.5 pt-3">
                      {Array.from({ length: column.limit - column.count }).map(
                        (_, slot) => (
                          <span
                            key={slot}
                            aria-hidden="true"
                            className="h-11 shrink-0 rounded-md border border-dashed border-border/70"
                          />
                        )
                      )}
                    </div>
                  ) : null}
                  {column.count > column.cards.length ? (
                    <p className="m-0 mt-auto border-t border-border/60 pt-3 text-[10.5px] leading-5 text-muted-foreground tabular-nums">
                      + {column.count - column.cards.length} more
                    </p>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-1.5 border-t border-border/60 px-4 py-3 font-mono text-[11px] leading-5 sm:px-5">
          <span className="text-muted-foreground">
            <span className="text-primary">$</span> folio board check
          </span>
          <span className="text-foreground">
            Board OK: 40 cards across 5 columns
          </span>
        </div>
      </figure>

      <Meta className="mt-4">
        origin/board
        <Dot />
        15 of 40 cards drawn
      </Meta>
    </>
  )
}
