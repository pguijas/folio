import { Head, Meter, Rows } from "@/components/agents-kit"
import { cn } from "@/lib/utils"

/* What 0.1 is, and what is only named.
 *
 * The earlier studies drew this as four columns of sixteen sentence-long
 * bullets, and two independent readings called it the most boring block on the
 * page. It was: the sections above this one already show everything 0.1
 * contains, so restating them as a list of promises adds words and no facts.
 *
 * What is left is the smallest thing that still answers the question a reader
 * has here — is this finished, and what comes after it. Four rows on hairlines:
 * the version, the title, the one-line summary the roadmap already declares,
 * and the status word. The only measurement on the block sits on 0.1, because
 * 0.1 is the only phase with anything to measure.
 *
 * Every string below is verbatim from the four `project: agents` phases in the
 * `roadmap:` block of docs.yaml at HEAD: version, title, status word, summary.
 * The working tree currently carries an uncommitted edit that deletes the
 * `projects:` block and those four phases, so checking this file against
 * docs.yaml on disk will not match until that edit lands or is dropped; check
 * it against `git show HEAD:docs.yaml` instead. Status words included: 0.1 is
 * `active`, not shipped, and a study that printed `shipped` here was wrong. */

type Phase = {
  version: string
  title: string
  /** The literal docs.yaml status. Not a rewritten one. */
  status: "active" | "next" | "later"
  summary: string
}

const PHASES: Phase[] = [
  {
    version: "0.1",
    title: "Repository Board",
    status: "active",
    summary:
      "Agents and humans operate one reviewable board made of Markdown files in git.",
  },
  {
    version: "0.2",
    title: "Session Memory",
    status: "next",
    summary:
      "A useful agent session leaves a concise conclusion that the next session can find and reuse.",
  },
  {
    version: "0.3",
    title: "Project Coordination",
    status: "next",
    summary:
      "The board becomes a dependable projection of releases, dependencies, and active ownership.",
  },
  {
    version: "0.4",
    title: "Harness Network",
    status: "later",
    summary:
      "Teams share useful agent workflows and context contracts without centralizing their repository state.",
  },
]

/* Three marks, three states, no legend. The active phase is a ring with a core,
 * which is how the roadmap page itself draws `active`; the named phases are
 * dashed and empty. A filled mark is reserved for a shipped phase, and this
 * product has none, so it never appears here. */
function Mark({ active }: { active: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "mt-[3px] grid size-4 shrink-0 place-items-center rounded-full",
        active
          ? "border border-primary bg-background"
          : "border border-dashed border-border"
      )}
    >
      {active ? <span className="size-[5px] rounded-full bg-primary" /> : null}
    </span>
  )
}

export function AgentsRoadmap() {
  return (
    <>
      <Head
        title="0.1 is the board."
        muted="The rest is named, not built."
        lead="Folio's own agents board runs on 0.1 today. The three releases under it are named and scoped, and not built."
        /* `?product=agents` opens /roadmap/ on this product's card with the
           other collapsed, so the four phases below are the first thing the
           page shows rather than something to scroll past Folio Docs for. */
        action={{ label: "Full roadmap", href: "../roadmap/?product=agents" }}
      />

      <Rows className="mt-12 border-t border-border/60 sm:mt-14">
        {PHASES.map((phase) => {
          const active = phase.status === "active"
          return (
            <li
              key={phase.version}
              className="grid grid-cols-[auto_minmax(0,1fr)] items-start gap-x-5 py-6 sm:grid-cols-[auto_minmax(0,1fr)_minmax(0,20rem)] sm:gap-x-10 sm:py-7"
            >
              <Mark active={active} />

              <div className="min-w-0">
                <p className="m-0 flex flex-wrap items-baseline gap-x-3.5 gap-y-1">
                  <span
                    className={cn(
                      "font-mono text-[13px] leading-6 tabular-nums",
                      active ? "text-primary" : "text-muted-foreground"
                    )}
                  >
                    {phase.version}
                  </span>
                  <span
                    className={cn(
                      "text-[15.5px] leading-6 font-semibold tracking-[-0.01em]",
                      active ? "text-foreground" : "text-muted-foreground"
                    )}
                  >
                    {phase.title}
                  </span>
                </p>
                <p className="mt-1.5 m-0 max-w-[46rem] text-[13.5px] leading-6 text-muted-foreground">
                  {phase.summary}
                </p>
              </div>

              {/* Shrink-to-fit, so the bar under the measure is exactly as
                  wide as the measure it belongs to. */}
              <div className="col-start-2 mt-3 min-w-0 sm:col-start-3 sm:mt-0 sm:text-right">
                <div className="inline-block max-w-full min-w-0 align-top">
                  {/* Sans, not mono. A status word is a label, not literal
                      text you could type, and mono at label size was the one
                      face doing every job on this page. Weight and tone carry
                      the live phase instead. */}
                  <p
                    className={cn(
                      "m-0 text-[12.5px] leading-6 tracking-[0.005em] sm:text-right",
                      active
                        ? "font-medium text-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {phase.status}
                  </p>
                  {active ? (
                    <>
                      <p className="mt-1.5 m-0 text-[11.5px] leading-5 tracking-[0.005em] tabular-nums text-muted-foreground">
                        <span className="font-medium text-foreground">
                          18 / 20
                        </span>{" "}
                        cards on{"\u00a0milestone\u00a00.1 released"}
                      </p>
                      <Meter ratio={18 / 20} className="mt-2.5" />
                    </>
                  ) : null}
                </div>
              </div>
            </li>
          )
        })}
      </Rows>
    </>
  )
}
