import {
  roadmapPhases,
  type RoadmapPhase,
  type RoadmapStatus,
} from "@/lib/roadmap-data"
import {
  groupPhasesByProject,
  projectKeyOf,
  statusLabels,
  projectLabel,
  sortByVersion,
} from "@/lib/roadmap-utils"
import { cn } from "@/lib/utils"
import { ViewHeaderRule } from "@/components/view-header"

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
}: {
  phase: RoadmapPhase
  isLast: boolean
  compact?: boolean
}) {
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
                {statusLabels[phase.status]}
                {active ? (
                  <span className="ml-1 inline-block size-1 rounded-full bg-primary align-middle" />
                ) : null}
              </span>
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

function EmptyRoadmap() {
  return (
    <section className="not-prose rounded-lg border border-border bg-card p-5">
      <p className="text-sm text-muted-foreground">
        No roadmap phases configured.
      </p>
    </section>
  )
}

interface TimelineProps {
  phases: RoadmapPhase[]
  /** Render one project's releases. Without it, multiple project values
   * become separate release lines automatically. */
  project?: string
  compact?: boolean
  maxPhases?: number
  /** false renders the truncation row as a plain count — for hosts (e.g. a
   * framed miniature) whose own chrome already links to the full roadmap. */
  moreLink?: boolean
}

/**
 * The vertical release line: one node per phase, spine between them.
 *
 * The one presentation the roadmap has, at both sizes: the full page and the
 * embedded miniature (the landing, a browser-frame excerpt, a
 * `<Roadmap compact />` in a guide) differ only by `compact`.
 */
function RoadmapTimeline({
  phases,
  project,
  compact = false,
  maxPhases,
  moreLink = true,
}: TimelineProps) {
  const groups = groupPhasesByProject(phases)

  /* Phases that name several projects draw one line each, stacked. A
   * single-project roadmap — every phase under the default key — never
   * reaches this branch. */
  if (!project && groups.length > 1) {
    return (
      <section
        className="not-prose grid gap-12"
        aria-label="Releases by project"
      >
        {groups.map(({ key, phases: projectPhases }) => (
          <RoadmapTimeline
            key={key}
            phases={projectPhases}
            project={key}
            compact={compact}
            maxPhases={maxPhases}
            moreLink={moreLink}
          />
        ))}
      </section>
    )
  }

  const scopedPhases = project
    ? phases.filter((phase) => projectKeyOf(phase) === project)
    : phases

  if (scopedPhases.length === 0) {
    return <EmptyRoadmap />
  }

  const ordered = sortByVersion(scopedPhases)
  const shipped = scopedPhases.filter(
    (phase) => phase.status === "shipped"
  ).length
  const visible =
    maxPhases !== undefined && maxPhases < ordered.length
      ? ordered.slice(0, Math.max(maxPhases, 0))
      : ordered
  const hidden = ordered.length - visible.length

  return (
    <section
      className="not-prose"
      aria-label={
        project
          ? `${projectLabel(project)} releases`
          : "Source-defined roadmap visualization"
      }
    >
      {/* Only the embedded miniature draws a rule. On the full page the header
          above already names the roadmap, so a second "Releases" label under it
          said the same thing twice, and the count beside it restated what the
          filled nodes on the spine already show. */}
      {compact ? (
        <ViewHeaderRule
          label={project ? `${projectLabel(project)} releases` : "Releases"}
          compact
          right={
            <p className="m-0 font-mono text-[11px] tabular-nums text-muted-foreground">
              <span className="text-foreground">{shipped}</span>
              <span className="text-muted-foreground/50">
                {" "}/ {scopedPhases.length}
              </span>
            </p>
          }
        />
      ) : null}

      <div role="list" className="relative m-0 list-none p-0">
        {visible.map((phase, index) => (
          <PhaseRow
            key={phase.id}
            phase={phase}
            isLast={index === visible.length - 1 && hidden === 0}
            compact={compact}
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

interface RoadmapProps {
  phases?: RoadmapPhase[]
  project?: string
  compact?: boolean
  maxPhases?: number
  moreLink?: boolean
  /** An optional header rule above the timeline, for a host that has no
   * chrome of its own. The `/roadmap` page passes neither: its name, its
   * description and its board link are drawn by the layout's title band. */
  title?: string
  links?: { label: string; href: string }[]
}

/**
 * The roadmap: one vertical release line, at full size or `compact`.
 *
 * This file stays a server component — no directive, no hooks, no browser
 * storage — so the landing page can render the miniature without pulling the
 * roadmap into the hydration bundle.
 */
export function Roadmap({
  phases = roadmapPhases,
  project,
  compact = false,
  maxPhases,
  moreLink = true,
  title,
  links,
}: RoadmapProps) {
  const timeline = (
    <RoadmapTimeline
      phases={phases}
      project={project}
      compact={compact}
      maxPhases={maxPhases}
      moreLink={moreLink}
    />
  )

  if (!title) return timeline

  return (
    <div className="not-prose">
      <ViewHeaderRule
        label={title}
        compact={compact}
        right={<HeaderLinks links={links} />}
      />
      {timeline}
    </div>
  )
}

function HeaderLinks({ links }: { links?: { label: string; href: string }[] }) {
  if (!links?.length) return null
  return (
    <>
      {links.map((link) => (
        <a
          key={link.href}
          href={link.href}
          className="font-mono text-[11px] tracking-[0.14em] text-muted-foreground uppercase underline decoration-border underline-offset-4 transition-colors hover:text-foreground hover:decoration-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          {link.label}
        </a>
      ))}
    </>
  )
}
