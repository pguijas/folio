import { kanbanColumns } from "@/lib/kanban-data"
import {
  roadmapPhases,
  type RoadmapPhase,
  type RoadmapStatus,
} from "@/lib/roadmap-data"
import { cn } from "@/lib/utils"
import { ViewHeaderRule } from "@/components/view-header"

const statusMeta: Record<
  RoadmapStatus,
  { label: string; rank: number }
> = {
  shipped: { label: "Shipped", rank: 0 },
  active: { label: "In progress", rank: 1 },
  next: { label: "Up next", rank: 2 },
  later: { label: "Later", rank: 3 },
}

function Node({
  status,
  compact = false,
}: {
  status: RoadmapStatus
  compact?: boolean
}) {
  const size = compact ? "size-[18px]" : "size-[26px]"
  if (status === "shipped") {
    return (
      <span
        className={cn(
          "relative z-10 flex items-center justify-center rounded-full border border-primary bg-primary text-primary-foreground",
          size
        )}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          className={compact ? "size-2" : "size-3"}
          aria-hidden="true"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </span>
    )
  }
  if (status === "active") {
    return (
      <span
        className={cn(
          "relative z-10 flex items-center justify-center rounded-full border border-primary bg-background",
          size
        )}
      >
        <span className="absolute inset-0 motion-safe:animate-ping rounded-full border border-primary opacity-30" />
        <span className={cn("rounded-full bg-primary", compact ? "size-1.5" : "size-2")} />
      </span>
    )
  }
  return (
    <span
      className={cn(
        "relative z-10 flex items-center justify-center rounded-full border border-border bg-background",
        size
      )}
    >
      <span className="size-1.5 rounded-full bg-muted-foreground/40" />
    </span>
  )
}

/* One feature, one line — a markdown-style task-list item. Shipped
   features get a checked box; everything pending gets an empty one
   (dashed once the phase is far out), mirroring the acceptance-criteria
   checklists on the project's own board cards. */
function FeatureItem({
  feature,
  status,
}: {
  feature: string
  status: RoadmapStatus
}) {
  const done = status === "shipped"
  return (
    <li
      className={cn(
        "flex items-start gap-2.5 text-sm leading-6",
        done && "text-foreground/85",
        status === "active" && "text-foreground/80",
        status === "next" && "text-muted-foreground",
        status === "later" && "text-muted-foreground/70"
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "mt-[5px] flex size-3.5 shrink-0 items-center justify-center rounded-[4px] border",
          done && "border-primary bg-primary text-primary-foreground",
          status === "active" && "border-primary/50",
          status === "next" && "border-border",
          status === "later" && "border-dashed border-border"
        )}
      >
        {done ? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={3.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="size-2.5"
          >
            <path d="M20 6 9 17l-5-5" />
          </svg>
        ) : null}
      </span>
      <span className="min-w-0">{feature}</span>
    </li>
  )
}

function PhaseRow({
  phase,
  isLast,
  compact = false,
  boardHref,
  hasCards = false,
}: {
  phase: RoadmapPhase
  isLast: boolean
  compact?: boolean
  boardHref?: string
  /** Whether any card carries this phase's milestone. A phase with none links
   * to an empty board, so it gets no link at all. */
  hasCards?: boolean
}) {
  const meta = statusMeta[phase.status]
  const done = phase.status === "shipped"
  const active = phase.status === "active"
  const future = !done && !active

  // Every phase reads the same — summary then checklist — except the far
  // "later" rows, which stay a spine of dashed boxes.
  const showSummary = !compact && phase.status !== "later"
  const showFeatures = !compact
  const showCommand = !compact && active && Boolean(phase.command)

  return (
    <div
      role="listitem"
      className={cn(
        "relative m-0 grid",
        compact
          ? "grid-cols-[18px_1fr] gap-x-3"
          : "grid-cols-[26px_1fr] gap-x-5 sm:gap-x-7"
      )}
    >
      {/* spine segment below the node */}
      {!isLast ? (
        <span
          aria-hidden="true"
          className={cn(
            "absolute w-px",
            compact
              ? "left-[8.5px] top-[18px] bottom-0"
              : "left-[12.5px] top-[26px] bottom-0",
            done ? "bg-primary/60" : "border-l border-dashed border-border"
          )}
        />
      ) : null}

      <Node status={phase.status} compact={compact} />

      <div
        className={cn(
          "min-w-0",
          compact ? "pb-4" : showSummary ? "pb-10" : showFeatures ? "pb-8" : "pb-6",
          isLast && (compact ? "pb-0.5" : "pb-2")
        )}
      >
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span
            className={cn(
              "font-mono tabular-nums",
              compact ? "text-[11px]" : "text-xs",
              done || active ? "text-primary" : "text-muted-foreground"
            )}
          >
            v{phase.version.replace(/^v/i, "")}
          </span>
          {/* title + status share a wrapper so a wrapped status lands under
              the title's left edge, not under the version column */}
          <span className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-3 gap-y-1">
            {compact ? (
              <p
                className={cn(
                  "m-0 text-[13px] font-semibold tracking-tight",
                  future ? "text-muted-foreground" : "text-foreground"
                )}
              >
                {phase.title}
              </p>
            ) : (
              <h2
                id={phase.id}
                className={cn(
                  "m-0 scroll-mt-24 text-[15px] font-semibold tracking-tight",
                  future ? "text-muted-foreground" : "text-foreground"
                )}
              >
                {phase.title}
              </h2>
            )}
            {/* the filled check node already says "shipped" — no label */}
            {!done ? (
              <span
                className={cn(
                  "font-mono uppercase tracking-[0.14em]",
                  compact ? "text-[9px]" : "text-[10px]",
                  active ? "text-primary" : "text-muted-foreground"
                )}
              >
                {meta.label}
                {active ? (
                  <span className="ml-1 inline-block size-1 rounded-full bg-primary align-middle" />
                ) : null}
              </span>
            ) : null}
            {boardHref && !compact && hasCards ? (
              <a
                href={`${boardHref}?milestone=${encodeURIComponent(phase.version.replace(/^v/i, ""))}`}
                className="ml-auto font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/70 transition-colors hover:text-foreground"
              >
                board &rarr;
              </a>
            ) : null}
          </span>
        </div>

        {showSummary ? (
          <p
            className={cn(
              "mt-1.5 mb-0 max-w-xl text-sm leading-6 break-words",
              future ? "text-muted-foreground/70" : "text-muted-foreground"
            )}
          >
            {phase.summary}
          </p>
        ) : null}

        {showFeatures ? (
          <div className={cn(showSummary ? "mt-3" : "mt-2.5")}>
            <span className="mb-2 block font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/60">
              {phase.layer}
            </span>
            <ul className="m-0 grid list-none grid-cols-1 gap-x-10 gap-y-1 p-0 sm:grid-cols-2">
              {phase.features.map((feature) => (
                <FeatureItem
                  key={feature}
                  feature={feature}
                  status={phase.status}
                />
              ))}
            </ul>
          </div>
        ) : null}

        {showCommand ? (
          <code className="mt-3 inline-block border-0 bg-transparent p-0 font-mono text-xs text-muted-foreground">
            <span className="select-none text-muted-foreground/50">$ </span>
            {phase.command}
          </code>
        ) : null}
      </div>
    </div>
  )
}

export function Roadmap({
  phases = roadmapPhases,
  compact = false,
  maxPhases,
  moreLink = true,
  boardHref,
}: {
  phases?: RoadmapPhase[]
  compact?: boolean
  maxPhases?: number
  /** false renders the truncation row as a plain count — for hosts (e.g. a
   * framed miniature) whose own chrome already links to the full roadmap. */
  moreLink?: boolean
  /** Public kanban route; when set, each phase deep-links into the board
   * pre-filtered by its milestone (?milestone=<version>). */
  boardHref?: string
}) {
  if (phases.length === 0) {
    return (
      <section className="not-prose rounded-lg border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          No roadmap phases configured.
        </p>
      </section>
    )
  }

  // A phase whose milestone matches no card would deep-link into an empty
  // board, so it gets no link. Empty when the kanban plugin is off, which
  // drops every link — correct, since there is no board to reach.
  const milestonesWithCards = new Set(
    kanbanColumns.flatMap((column) =>
      column.cards.map((card) => card.milestone).filter(Boolean)
    )
  )

  const ordered = [...phases].sort(
    (a, b) => statusMeta[a.status].rank - statusMeta[b.status].rank
  )
  const shipped = phases.filter((phase) => phase.status === "shipped").length
  const visible =
    maxPhases !== undefined && maxPhases < ordered.length
      ? ordered.slice(0, Math.max(maxPhases, 0))
      : ordered
  const hidden = ordered.length - visible.length

  return (
    <section
      className="not-prose"
      aria-label="Source-defined roadmap visualization"
    >
      <ViewHeaderRule
        label="Release track"
        compact={compact}
        right={
          <>
            {!compact ? (
              <div className="flex items-center gap-1" aria-hidden="true">
                {ordered.map((phase) => (
                  <span
                    key={phase.id}
                    className={cn(
                      "h-1.5 w-4 rounded-full",
                      phase.status === "shipped" && "bg-primary",
                      phase.status === "active" && "bg-primary/45",
                      phase.status === "next" && "bg-border",
                      phase.status === "later" && "bg-border/60"
                    )}
                  />
                ))}
              </div>
            ) : null}
            <p
              className={cn(
                "m-0 font-mono tabular-nums text-muted-foreground",
                compact ? "text-[11px]" : "text-xs"
              )}
            >
              <span className="text-foreground">{shipped}</span>
              <span className="text-muted-foreground/50"> / {phases.length} shipped</span>
            </p>
          </>
        }
      />

      <div role="list" className="relative m-0 list-none p-0">
        {visible.map((phase, index) => (
          <PhaseRow
            key={phase.id}
            phase={phase}
            isLast={index === visible.length - 1 && hidden === 0}
            compact={compact}
            boardHref={boardHref}
            hasCards={milestonesWithCards.has(
              phase.version.replace(/^v/i, "")
            )}
          />
        ))}
        {hidden > 0 ? (
          <div
            role="listitem"
            className={cn(
              "relative m-0 grid",
              compact
                ? "grid-cols-[18px_1fr] gap-x-3"
                : "grid-cols-[26px_1fr] gap-x-5 sm:gap-x-7"
            )}
          >
            <span
              aria-hidden="true"
              className={cn(
                "relative z-10 flex items-center justify-center rounded-full border border-dashed border-border bg-background",
                compact ? "size-[18px]" : "size-[26px]"
              )}
            >
              <span className="size-1 rounded-full bg-muted-foreground/40" />
            </span>
            <p
              className={cn(
                "m-0 self-center font-mono text-muted-foreground",
                compact ? "text-[11px]" : "text-xs"
              )}
            >
              + {hidden} more
              {moreLink ? (
                <>
                  {" · "}
                  <a
                    href="/roadmap"
                    className="text-muted-foreground underline decoration-border underline-offset-4 hover:text-foreground hover:decoration-foreground"
                  >
                    full roadmap &rarr;
                  </a>
                </>
              ) : null}
            </p>
          </div>
        ) : null}
      </div>
    </section>
  )
}
