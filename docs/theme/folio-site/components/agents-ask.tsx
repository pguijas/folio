import type { ReactNode } from "react"

import { Head } from "@/components/agents-kit"
import { BrandMark } from "@/components/brand-marks"
import { cn } from "@/lib/utils"

/* The prompt is the integration.
 *
 * The section this replaces put five `folio board` verbs beside a terminal,
 * which answers the question "what is the CLI" — a question nobody asked. The
 * subject here is the sentence a person types and the line that exists
 * afterwards, with nothing drawn between them, because there is nothing
 * between them: no client, no API call, no runtime handshake. What crosses the
 * gap is that the agent read `board/SKILL.md`, and the file was already in the
 * checkout.
 *
 * Left column: five asks in the register somebody actually types to an
 * assistant. They are not transcripts and the lead does not claim they are.
 * Right column: the file and the literal edit, and every one of those is
 * verbatim, checked against `origin/board`:
 *
 * 1. `- status: backlog` / `+ status: in-progress` is the diff block shipped
 *    inside SKILL.md itself ("That is the whole move: a one-line diff"), and
 *    `the-board-reads-as-a-tree` really does sit at `status: backlog` today,
 *    so the left side of the diff is the card's current line, not an example.
 * 2. `git show origin/board:folio-agents/board/cards/artifacts-live-beside-their-card.md`,
 *    first of six trail lines. Cut at a word boundary after "404;" with a
 *    visible ellipsis; nothing is reworded.
 * 3. `.../artifact-viewer-becomes-a-workspace.md`, first of four comments. Cut
 *    at the sentence end, ellipsis visible.
 * 4. `.../the-board-takes-the-name-and-absorbs-the-roadmap.md`, its whole
 *    `artifacts:` block, two lines. `panel-verdict.md` is a bare sibling name
 *    and the file is really there beside the card.
 * 5. `<new-slug>.md` and `cards/_TEMPLATE.md` are SKILL.md's own words for the
 *    operation; the two added lines are the template's lines 2 and 3. A
 *    placeholder is the honest thing here — nobody's real card was created in
 *    the session the row describes.
 *
 * The accent is spent on the sigil alone. Five rows of tinted diff rows would
 * have made a traffic light out of a hairline list, and the sigil already says
 * which line is new.
 *
 * The two strips bracket the list and carry the section's other claim: above,
 * nothing was installed, and the file that taught the right-hand column is
 * already in the checkout; below, the edit ends in a commit, so the history is
 * git's problem and not a feature anyone has to run. `4bb5bc0ab` is real and
 * its subject is the trail operation row two shows: `git log --oneline
 * origin/board`.
 *
 * The caption carries the limit, because the drawing would otherwise imply
 * discovery: nothing registers this file, and an agent only reaches it because
 * a line in the repository's instructions or the person opening the session
 * pointed at it. */

interface Change {
  sign: "+" | "-"
  text: string
}

interface Ask {
  ask: string
  file: string
  where: ReactNode
  changes: Change[]
}

const ASKS: Ask[] = [
  {
    ask: "I'm starting on the tree view card.",
    file: "cards/the-board-reads-as-a-tree.md",
    where: <Prose>frontmatter</Prose>,
    changes: [
      { sign: "-", text: "status: backlog" },
      { sign: "+", text: "status: in-progress" },
    ],
  },
  {
    ask: "Before you stop, write down what this session found.",
    file: "cards/artifacts-live-beside-their-card.md",
    where: "## Trail",
    changes: [
      {
        sign: "+",
        text:
          "- 2026-08-20 @claude: found while attaching prototypes — every artifact resolved to a 404; …",
      },
    ],
  },
  {
    ask: "Record my call on the viewer card.",
    file: "cards/artifact-viewer-becomes-a-workspace.md",
    where: "## Comments",
    changes: [
      {
        sign: "+",
        text:
          "- 2026-08-29 @pguijas: Canvas is the center element, filters stay on the left, and the card is a right drawer. …",
      },
    ],
  },
  {
    ask: "Attach the panel's verdict to the rename card.",
    file: "cards/the-board-takes-the-name-and-absorbs-the-roadmap.md",
    where: "artifacts:",
    changes: [
      { sign: "+", text: "  - doc: panel-verdict.md" },
      { sign: "+", text: "    label: Panel verdict" },
    ],
  },
  {
    ask: "Open a card for this so it doesn't get lost.",
    file: "cards/<new-slug>.md",
    where: (
      <>
        <Prose>a copy of</Prose> cards/_TEMPLATE.md
      </>
    ),
    changes: [
      { sign: "+", text: 'title: "Card title"' },
      { sign: "+", text: "status: backlog" },
    ],
  },
]

/** Sans inside a mono line: the file is literal, the word describing where in
 * it the edit lands is not. */
function Prose({ children }: { children: ReactNode }) {
  return <span className="font-sans">{children}</span>
}

const COLUMNS =
  "grid gap-x-10 gap-y-3 lg:grid-cols-[minmax(0,0.42fr)_minmax(0,0.58fr)] lg:gap-x-16"

export function AgentsAsk() {
  return (
    <>
      <Head
        title="You ask for it in plain English,"
        muted="and one line changes in one file."
        lead="There is no client library, no plugin and no API. An agent reads the protocol out of the repository and edits the card itself, so the Folio command is a convenience it can do without. Five ordinary asks, and the line each one leaves in a card file."
      />

      <figure
        className="not-prose m-0 mt-12 min-w-0 sm:mt-14"
        style={{
          fontFeatureSettings: '"liga" 0, "calt" 0',
          fontVariantLigatures: "none",
        }}
        aria-label="Five things a person types to an assistant, each paired with the file the assistant edits and the exact line it writes: a status line moving a card to in-progress, a dated trail line, a dated comment line, two lines in an artifacts block, and a new card file copied from the template. Above them, the file that taught it, folio-agents/board/SKILL.md, which nothing installed; below them, the commit that keeps the change."
      >
        <div className={COLUMNS}>
          <div className="min-w-0">
            <p className="m-0 text-[15px] leading-6 text-foreground">
              Nothing was installed to make this work.
            </p>
            <p className="m-0 mt-3.5 flex flex-wrap items-center gap-x-3 gap-y-2 text-[13px] leading-6 text-muted-foreground">
              <span className="flex items-center gap-2.5 text-foreground/55">
                <BrandMark id="claude" className="size-[16px]" />
                <BrandMark id="codex" className="size-[16px]" />
                <BrandMark id="cursor" className="size-[16px]" />
                <BrandMark id="editor" className="size-[16px]" />
              </span>
              <span className="min-w-0">
                &ldquo;Any agent (Claude Code, Hermes, OpenClaw, a human with an
                editor) follows the same protocol.&rdquo;
              </span>
            </p>
          </div>
          <div className="min-w-0">
            <p className="m-0 flex items-start gap-2 font-mono text-[11.5px] leading-5 break-all text-foreground/75">
              <BrandMark
                id="markdown"
                className="mt-[-1px] size-[19px] shrink-0 text-foreground/55"
              />
              folio-agents/board/SKILL.md
            </p>
            <p className="m-0 mt-1.5 text-[12.5px] leading-5 text-muted-foreground">
              283 lines of Markdown, already in the repository.
            </p>
          </div>
        </div>

        <ul className="m-0 mt-9 list-none divide-y divide-border/60 border-t border-b border-border/60 p-0">
          {ASKS.map((row) => (
            <li key={row.file + row.ask} className={cn(COLUMNS, "py-6 lg:items-baseline")}>
              <p className="m-0 text-[15px] leading-6 text-foreground">
                &ldquo;{row.ask}&rdquo;
              </p>

              <div className="min-w-0">
                <p className="m-0 font-mono text-[11.5px] leading-5 break-words text-foreground/70">
                  {row.file}
                  <span className="whitespace-nowrap text-muted-foreground/80">
                    <span className="mx-1.5 text-border">&middot;</span>
                    {row.where}
                  </span>
                </p>
                <div className="mt-2.5 space-y-[3px]">
                  {row.changes.map((change) => (
                    <p
                      key={change.sign + change.text}
                      className="m-0 flex gap-2 font-mono text-[11.5px] leading-[1.65]"
                    >
                      <span
                        className={cn(
                          "shrink-0",
                          change.sign === "+"
                            ? "text-primary"
                            : "text-destructive"
                        )}
                      >
                        {change.sign}
                      </span>
                      <span
                        className={cn(
                          "min-w-0 break-words whitespace-pre-wrap",
                          change.sign === "+"
                            ? "text-foreground"
                            : "text-muted-foreground"
                        )}
                      >
                        {change.text}
                      </span>
                    </p>
                  ))}
                </div>
              </div>
            </li>
          ))}
        </ul>

        <div className={cn(COLUMNS, "mt-8 lg:items-baseline")}>
          <p className="m-0 text-[15px] leading-6 text-foreground">
            Each of those is one line in one file, and git keeps the history.
          </p>
          <p className="m-0 flex min-w-0 items-start gap-2 font-mono text-[11.5px] leading-5 break-words text-foreground/70">
            <BrandMark
              id="git"
              className="mt-[1px] size-[16px] shrink-0 text-foreground/55"
            />
            <span className="min-w-0">
              4bb5bc0ab board: trail landing-for-the-two-product-family
            </span>
          </p>
        </div>

        <figcaption className={cn(COLUMNS, "mt-9")}>
          <span aria-hidden="true" className="hidden lg:block" />
          <p className="m-0 min-w-0 text-[13px] leading-6 text-muted-foreground">
            &ldquo;Nothing installs this protocol&hellip; today an agent reaches
            this file because something points at it: a line in the
            repository&rsquo;s agent instructions, or whoever opened the
            session.&rdquo;
            <span className="mt-1 block font-mono text-[11px] leading-5 text-muted-foreground/80">
              folio-agents/docs/agents/board/agents.md
            </span>
          </p>
        </figcaption>
      </figure>
    </>
  )
}
