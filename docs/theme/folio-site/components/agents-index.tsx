import { Head } from "@/components/agents-kit"
import { BrandMark, type BrandId } from "@/components/brand-marks"
import { cn } from "@/lib/utils"

/* The closing half of the claim: the store leaves the repository as text a
 * program can fetch. Five addresses, five sizes, nothing else in the row.
 *
 * This is deliberately NOT the store map's shape. The map is an indented tree
 * with a description under every path and a count on the right; two sections
 * drawing the same object the same way is one section too many. So here the
 * path and the byte figure ARE the row, and everything a description would
 * have said is one paragraph above the list. An index, not a map.
 *
 * Every number was measured against the running dev server, not read off a
 * doc. `curl -s -o /dev/null -w "%{http_code} %{size_download}" <url>`:
 *
 *   /llms.txt                                              200 27283
 *   /llms-full.txt                                         200 677123
 *   /_folio/contract.json                                  200 11669
 *   /_folio/markdown/architecture.md                       200 2336
 *   /_folio/kanban/the-board-reads-as-a-tree/tree-table.html  200 7500
 *
 * 131 pages: `grep -c '^- \[' llms.txt` is 131, and `grep -c '^URL: '` on
 * llms-full.txt is 131 as well. There are 132 files under
 * .build/public/_folio/markdown; the one llms.txt does not list is
 * api-reference/index.md, the section page for the API reference, whose source
 * is one byte long because the page has no body of its own. That difference is
 * real but it is not worth a clause, so no mirror count is printed at all and
 * the corpus is counted once, as 131 pages.
 *
 * Scope of the last row, which is the easy thing to get wrong. docs.yaml
 * declares two kanban sources, `docs: folio-docs/board` and
 * `agents: folio-agents/board`, and both publish flat under /_folio/kanban/.
 * So the served build holds 8 directories and 67 files
 * (`find .build/public/_folio/kanban -type f | wc -l`), of which
 * landing-for-the-two-product-family (26 files) belongs to the Docs board.
 * Folio for Agents' own store is 7 directories and 41 files, which is what the
 * map two sections above prints. Both counts are true of different objects, so
 * the paragraph names which object it is counting.
 *
 * "byte for byte" is not a figure of speech. sha256 of three files taken from
 * `git show origin/board:folio-agents/board/cards/the-board-reads-as-a-tree/<f>`
 * and from the published copy agreed on all three (tree-table.html
 * 4e30b5a1e10f…, brief.md e8bb1c38b9e9…, board-data.js aa31def0f945…).
 *
 * The one accent marks the segment of an address that varies: the page name,
 * the card id, the filename. The three rows with no accent are single files.
 *
 * The quotation is verbatim from folio-agents/docs/agents/board/agents.md, two
 * sentences from the same section with the cut between them marked. It is here
 * because a list of things a tool can open owes the reader the sentence saying
 * that nothing hands it the address. */

const noLigatures = {
  fontFeatureSettings: '"liga" 0, "calt" 0',
  fontVariantLigatures: "none",
} as const

/** An address, with the segments that vary set in the accent. */
function Route({
  parts,
  className,
}: {
  parts: Array<string | { v: string }>
  className?: string
}) {
  return (
    <span
      style={noLigatures}
      className={cn("font-mono break-words text-foreground", className)}
    >
      {parts.map((part, i) =>
        typeof part === "string" ? (
          <span key={i}>{part}</span>
        ) : (
          <span key={i} className="text-primary">
            {part.v}
          </span>
        )
      )}
    </span>
  )
}

type Published = {
  route: Array<string | { v: string }>
  bytes: string
}

const PUBLISHED: Published[] = [
  { route: ["/llms.txt"], bytes: "27,283" },
  { route: ["/llms-full.txt"], bytes: "677,123" },
  { route: ["/_folio/contract.json"], bytes: "11,669" },
  {
    route: ["/_folio/markdown/", { v: "architecture" }, ".md"],
    bytes: "2,336",
  },
  {
    route: [
      "/_folio/kanban/",
      { v: "the-board-reads-as-a-tree" },
      "/",
      { v: "tree-table.html" },
    ],
    bytes: "7,500",
  },
]

/* Generic, and the sentence they sit inside says so. These are programs that
 * can open a text file over HTTP, which is every program that can do that.
 * Three of them have written to this board and the trail section names those
 * three; nothing here claims the other three ever did. */
const OPENERS: BrandId[] = [
  "claude",
  "codex",
  "cursor",
  "copilot",
  "gemini",
  "editor",
]

export function AgentsIndex() {
  return (
    <>
      <Head
        title="The build hands the store back as routes."
        muted="Every one is plain text, and the size is what the server sent back."
      />

      <p className="m-0 mt-5 max-w-[46rem] text-[15px] leading-7 text-muted-foreground">
        Folio Docs 0.3.0 writes the first four for any site it builds: this
        site&rsquo;s 131 pages as one index, the same 131 with their bodies
        attached, what the build accepts as data, and the Markdown each page was
        written from. The fifth is the optional adapter this site&rsquo;s{" "}
        <span className="font-mono text-[13px] text-foreground/80">
          docs.yaml
        </span>{" "}
        names,{" "}
        <span className="font-mono text-[13px] text-foreground/80">
          folio_agents.integrations.kanban
        </span>
        , which republishes card directories byte for byte. This build carries
        eight of those directories and 67 files in them, because it publishes
        both of Folio&rsquo;s boards.
      </p>

      <figure
        className="not-prose m-0 mt-10 min-w-0 sm:mt-12"
        aria-label="Five published addresses and the size each one returned. /llms.txt, 27,283 bytes. /llms-full.txt, 677,123 bytes. /_folio/contract.json, 11,669 bytes. /_folio/markdown/architecture.md, 2,336 bytes, where the page name varies. /_folio/kanban/the-board-reads-as-a-tree/tree-table.html, 7,500 bytes, where the card id and the filename vary; those are the same bytes as the file in git."
      >
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,19rem)] lg:gap-16">
          <ul className="m-0 min-w-0 list-none divide-y divide-border/60 self-start border-y border-border/60 p-0">
            {PUBLISHED.map((item, i) => (
              <li
                key={i}
                className="flex items-baseline justify-between gap-6 py-4"
              >
                <Route parts={item.route} className="min-w-0 text-[13.5px] leading-6" />
                <p className="m-0 shrink-0 whitespace-nowrap">
                  <span className="text-[15px] leading-6 font-semibold tabular-nums text-foreground">
                    {item.bytes}
                  </span>{" "}
                  <span className="text-[11.5px] text-muted-foreground">
                    bytes
                  </span>
                </p>
              </li>
            ))}
          </ul>

          {/* The margin column: the sentence the list owes the reader, and the
              claim about who can read it. Neither is an address, so neither is
              a row. */}
          <div className="flex min-w-0 flex-col gap-10 lg:border-l lg:border-border/60 lg:pl-10">
            <blockquote className="m-0">
              <p className="m-0 text-[14px] leading-7 text-foreground">
                Nothing installs this protocol. An agent arrives at it by one of
                three paths, each of them an ordinary file.
              </p>
              <p
                aria-hidden="true"
                className="m-0 py-1 text-[13px] leading-6 text-muted-foreground/70"
              >
                [&hellip;]
              </p>
              <p className="m-0 text-[14px] leading-7 text-foreground">
                Folio registers the file with nothing: it calls no runtime and
                knows of none.
              </p>
              <footer className="mt-4 font-mono text-[10px] leading-5 text-muted-foreground">
                folio-agents/docs/agents/board/agents.md
              </footer>
            </blockquote>

            <p className="m-0 text-[14px] leading-8 text-muted-foreground">
              None of it needs an integration. These are text files at a URL,
              so anything that can fetch one reads them:{" "}
              <span className="font-mono text-[12.5px] text-foreground/80">
                curl
              </span>
              ,{" "}
              <span className="inline-flex items-center gap-2.5 align-[-0.22em] text-foreground/75">
                {OPENERS.map((id) => (
                  <BrandMark key={id} id={id} className="size-[16px]" labelled />
                ))}
              </span>
              , the editor you already have open.
            </p>
          </div>
        </div>
      </figure>
    </>
  )
}
