import { BrandMark } from "@/components/brand-marks"
import { Dot, Frame, Head, Meta, Path } from "@/components/agents-kit"
import { cn } from "@/lib/utils"

/* The directory is the record.
 *
 * One workspace on eighteen rows, and three columns that are three different
 * sources for the same row. There is no arrow anywhere in this figure because
 * there is no step between the columns: the file, its kind and its label are
 * one row because they are one file.
 *
 * Column one is `git ls-tree -l origin/board:folio-agents/board/cards/
 * the-board-reads-as-a-tree/` — eighteen blobs and their real byte sizes, in
 * the order `sorted(Path.iterdir())` returns them. That sort is why the five
 * prototypes fall into runs of three; the hairline in the gutter is reading
 * the sort, not imposing a grouping. board-data.js, brief.md and
 * prototypes-compared.md stand alone because nothing shares their stem.
 *
 * Column two is what line 504 produces. The code is
 * `folio-agents/folio_agents/loader.py`, line 497 and lines 501 to 504, exact
 * including indentation, which is why the gutter carries the real line
 * numbers: this is an excerpt of a file, not a paraphrase of one. The
 * markdown mark sits on the only two rows line 504 sends to `doc` — brief.md
 * and prototypes-compared.md. That is the one brand mark on the page and it
 * is doing the suffix rule's job. Nothing here implies a tool, a partner or
 * an integration.
 *
 * There is no route column. The published name is the filename on all
 * eighteen rows, so a column of it would spend a third of the width printing
 * one sentence eighteen times. The sentence sits under the table instead, and
 * the routes were checked rather than drawn.
 *
 * Column three is the card's frontmatter, and it is empty twelve times. Six
 * `doc:`/`file:` entries name a sibling and land a label on the derived
 * entry; the other twelve files are written down nowhere and are on the card
 * anyway. kanban.py:977-978 is why an unlabelled entry still reads: the tile
 * falls back to `display.rsplit("/", 1)[-1]`, the bare filename, which is
 * column one.
 *
 * Every route was checked before it was printed: all eighteen of
 * /_folio/kanban/the-board-reads-as-a-tree/<file> answer 200, and
 * tree-table.html answers with the file's own 7,500 bytes. */

/** The rule in its own words, then the rule. loader.py:497 and 501-504,
 * verbatim, original indentation. 498 to 500 are the symlink guard and the
 * empty list, and the row between marks where they were cut. */
const RULE: Array<{ n?: number; text?: string; cut?: true }> = [
  {
    n: 497,
    text: `    """One artifact per visible regular file at the directory's top level."""`,
  },
  { cut: true },
  { n: 501, text: "    for path in sorted(sibling_dir.iterdir()):" },
  {
    n: 502,
    text: '        if path.name.startswith((".", "_")) or path.is_symlink() or not path.is_file():',
  },
  { n: 503, text: "            continue" },
  {
    n: 504,
    text: '        kind = "doc" if path.suffix.lower() in (".md", ".mdx") else "file"',
  },
]

type Entry = {
  /** Bytes, from `git ls-tree -l`. */
  size: number
  name: string
  /** What line 504 makes of the suffix. */
  kind: "doc" | "file"
  /** The label the card's frontmatter writes, on the six that have one. */
  label?: string
}

/* Name-sorted, complete, nothing cut. The runs are the sort's own doing. */
const GROUPS: Entry[][] = [
  [{ size: 99245, name: "board-data.js", kind: "file" }],
  [
    { size: 21609, name: "board-inline-expansion.css", kind: "file" },
    {
      size: 7042,
      name: "board-inline-expansion.html",
      kind: "file",
      label: "Inline expansion (rejected)",
    },
    { size: 33222, name: "board-inline-expansion.js", kind: "file" },
  ],
  [{ size: 7312, name: "brief.md", kind: "doc" }],
  [
    { size: 25490, name: "document-outline.css", kind: "file" },
    {
      size: 8459,
      name: "document-outline.html",
      kind: "file",
      label: "Document outline (rejected)",
    },
    { size: 37086, name: "document-outline.js", kind: "file" },
  ],
  [
    { size: 18997, name: "epic-swimlanes.css", kind: "file" },
    {
      size: 6975,
      name: "epic-swimlanes.html",
      kind: "file",
      label: "Epic swimlanes (rejected)",
    },
    { size: 24489, name: "epic-swimlanes.js", kind: "file" },
  ],
  [
    {
      size: 7692,
      name: "prototypes-compared.md",
      kind: "doc",
      label: "Five layouts compared",
    },
  ],
  [
    { size: 23798, name: "tree-rail-detail.css", kind: "file" },
    {
      size: 6068,
      name: "tree-rail-detail.html",
      kind: "file",
      label: "Tree rail and detail (rejected)",
    },
    { size: 36245, name: "tree-rail-detail.js", kind: "file" },
  ],
  [
    { size: 21577, name: "tree-table.css", kind: "file" },
    {
      size: 7500,
      name: "tree-table.html",
      kind: "file",
      label: "Tree table (chosen)",
    },
    { size: 31615, name: "tree-table.js", kind: "file" },
  ],
]

/** The directory, then the field the rule derives, then the frontmatter.
 * Fixed until the last column, because the first two hold text of a known
 * width and only the label wants the slack. */
const COLS = "lg:grid-cols-[330px_78px_minmax(0,1fr)]"

/** The hairline that separates one source from the next, drawn per row so the
 * rows keep it continuous down the whole table. */
const SPLIT = "lg:border-l lg:border-border/45 lg:pl-5"

/** One source line. The leading indentation is held by a spacer measured in
 * `ch`, so a line too long for the frame wraps back to its own indent instead
 * of to the margin. At 1440 nothing wraps and this is a plain pre line; at 430
 * line 502 takes three visual lines and still says every character it says in
 * the file. Nothing is shortened, so there is no cut to mark. */
function Code({ n, text }: { n: number; text: string }) {
  const indent = text.length - text.trimStart().length
  return (
    <p className="m-0 flex gap-3.5 px-3.5">
      <span className="w-[22px] shrink-0 select-none text-right text-muted-foreground/50 tabular-nums">
        {n}
      </span>
      <span className="flex min-w-0 flex-1">
        <span
          aria-hidden="true"
          className="shrink-0"
          style={{ width: `${indent}ch` }}
        />
        <span className="min-w-0 flex-1 whitespace-pre-wrap break-words text-foreground/85">
          {text.slice(indent)}
        </span>
      </span>
    </p>
  )
}

function Kind({ kind }: { kind: "doc" | "file" }) {
  return (
    <span className="flex items-center gap-2">
      <span className="font-mono text-[10.5px] leading-none text-muted-foreground">
        {kind}
      </span>
      {kind === "doc" ? (
        <BrandMark
          id="markdown"
          className="size-[15px] shrink-0 text-foreground/75"
        />
      ) : null}
    </span>
  )
}

function Line({ entry }: { entry: Entry }) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 border-b border-border/45",
        COLS
      )}
    >
      <div className="flex min-w-0 items-center gap-3 py-[7px] pr-5">
        <span className="w-[46px] shrink-0 text-right font-mono text-[10.5px] leading-none text-muted-foreground tabular-nums">
          {entry.size}
        </span>
        <span className="min-w-0 flex-1 truncate font-mono text-[12px] leading-[1.5] text-foreground">
          {entry.name}
        </span>
        <span className="shrink-0 lg:hidden">
          <Kind kind={entry.kind} />
        </span>
      </div>

      <div className={cn("hidden items-center py-[7px] lg:flex", SPLIT)}>
        <Kind kind={entry.kind} />
      </div>

      <div
        className={cn(
          "min-w-0 items-center pb-[7px] pl-[58px] lg:py-[7px] lg:pl-5",
          SPLIT,
          entry.label ? "flex" : "hidden lg:flex"
        )}
      >
        {entry.label ? (
          <span className="flex min-w-0 items-center gap-2.5">
            <span
              aria-hidden="true"
              className="size-[6px] shrink-0 rounded-full bg-primary"
            />
            <span className="min-w-0 truncate text-[12.5px] leading-[1.5] font-medium text-foreground">
              {entry.label}
            </span>
          </span>
        ) : null}
      </div>
    </div>
  )
}

export function AgentsDerivation() {
  return (
    <div>
      <Head
        title="Nothing is registered."
        muted="Putting the file where it belongs is the registration."
        lead="A card's directory is read at build. Every regular file at its top level becomes an artifact on the card, name-sorted, and opens at a route. Six of these eighteen carry a label somebody wrote by hand. The other twelve are written down nowhere and are on the card anyway."
      />

      <figure
        className="m-0 mt-12 max-w-[62rem] sm:mt-14"
        aria-label="The docstring at line 497 of folio-agents/folio_agents/loader.py and the four lines 501 to 504 under it, then the eighteen files of folio-agents/board/cards/the-board-reads-as-a-tree/ with their byte sizes, from board-data.js at 99245 bytes to tree-table.js at 31615. Beside each filename sits the field those lines derive from it: kind doc for the two Markdown files, brief.md and prototypes-compared.md, and kind file for the other sixteen. The last column is the card's frontmatter and it is empty on twelve of the eighteen rows. The six it fills read: Inline expansion rejected, Document outline rejected, Epic swimlanes rejected, Five layouts compared, Tree rail and detail rejected, and Tree table chosen."
      >
        <Frame
          title="folio-agents/folio_agents/loader.py"
          right="_derived_sibling_artifacts"
          bodyClassName="px-0 py-3.5 text-[11px] leading-[1.9]"
        >
          {RULE.map((line) =>
            line.cut ? (
              /* 498 to 500 removed. The gutter jumping 497 to 501 says how
                 many, and the dashed rule says a cut happened at all. */
              <div
                key="cut"
                aria-hidden="true"
                className="mx-3.5 my-[7px] border-t border-dashed border-border"
              />
            ) : (
              <Code key={line.n} n={line.n!} text={line.text!} />
            )
          )}
        </Frame>

        <div className="mt-9 min-w-0">
          <div className={cn("grid grid-cols-1 gap-1 pb-2.5 pl-3.5 lg:gap-0", COLS)}>
            <p className="m-0 font-mono text-[10.5px] leading-5 text-muted-foreground lg:whitespace-nowrap">
              folio-agents/board/cards/the-board-reads-as-a-tree/
            </p>
            <p className="m-0 hidden font-mono text-[10.5px] leading-5 text-muted-foreground lg:block lg:pl-5">
              kind
            </p>
            <p className="m-0 hidden text-[11px] leading-5 text-muted-foreground lg:block lg:pl-5">
              written by hand
            </p>
          </div>

          <div className="border-t border-border/60">
            {GROUPS.map((group) => (
              <div key={group[0].name} className="flex items-stretch">
                <div className="flex w-3.5 shrink-0 flex-col items-center py-[7px]">
                  {group.length > 1 ? (
                    <span
                      aria-hidden="true"
                      className="w-px flex-1 rounded-full bg-muted-foreground/35"
                    />
                  ) : null}
                </div>
                <div className="min-w-0 flex-1">
                  {group.map((entry) => (
                    <Line key={entry.name} entry={entry} />
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="m-0 mt-3.5 pl-3.5 text-[12px] leading-5 text-muted-foreground">
            Each one publishes at{" "}
            <Path>/_folio/kanban/the-board-reads-as-a-tree/</Path> followed by
            its own filename, unchanged.
          </p>
        </div>

        <figcaption className="mt-7 min-w-0">
          <Meta>
            <Path>git ls-tree -l origin/board</Path>
            <Dot />
            18 files
            <Dot />
            424,421 bytes
            <Dot />
            18 artifacts on the card
            <Dot />
            all 18 routes answered 200
          </Meta>
          <p className="m-0 mt-2.5 max-w-[46rem] text-[13px] leading-6 text-muted-foreground">
            Five competing layouts, the brief that commissioned them and the
            comparison that chose between them, in the directory of the card
            that made the decision. The card is in backlog and the layout it
            chose is not built yet. Deriving the artifacts is Folio for Agents
            0.1.0; publishing them at a route is the optional Docs adapter,{" "}
            <Path>folio_agents.integrations.kanban</Path>, which this site turns
            on in <Path>docs.yaml</Path>.
          </p>
        </figcaption>
      </figure>
    </div>
  )
}
