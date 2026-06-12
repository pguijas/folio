import { roadmapPhases, type RoadmapPhase, type RoadmapStatus } from "@/lib/roadmap-data"
import { cn } from "@/lib/utils"

const statusOrder: RoadmapStatus[] = ["shipped", "active", "next", "later"]

const statusTone: Record<
  RoadmapStatus,
  {
    label: string
    dot: string
    text: string
    border: string
    surface: string
    header: string
  }
> = {
  shipped: {
    label: "shipped",
    dot: "bg-emerald-500",
    text: "text-emerald-700 dark:text-emerald-300",
    border: "border-emerald-500/25",
    surface: "bg-emerald-500/[0.07]",
    header: "bg-emerald-500/[0.06]",
  },
  active: {
    label: "building",
    dot: "bg-amber-400",
    text: "text-amber-700 dark:text-amber-300",
    border: "border-amber-400/40",
    surface: "bg-amber-400/[0.1]",
    header: "bg-amber-400/[0.08]",
  },
  next: {
    label: "next",
    dot: "bg-sky-500",
    text: "text-sky-700 dark:text-sky-300",
    border: "border-sky-500/25",
    surface: "bg-sky-500/[0.07]",
    header: "bg-sky-500/[0.06]",
  },
  later: {
    label: "later",
    dot: "bg-muted-foreground/40",
    text: "text-muted-foreground",
    border: "border-border",
    surface: "bg-muted/35",
    header: "bg-muted/25",
  },
}

function StatusBadge({ status }: { status: RoadmapStatus }) {
  const tone = statusTone[status]

  return (
    <span
      className={cn(
        "inline-flex h-6 items-center rounded-md border px-2 text-[11px] font-semibold uppercase",
        tone.border,
        tone.surface,
        tone.text
      )}
    >
      {tone.label}
    </span>
  )
}

function FeatureList({ features, status }: { features: string[]; status: RoadmapStatus }) {
  const tone = statusTone[status]

  return (
    <div className="flex flex-wrap gap-1.5">
      {features.map((feature) => (
        <span
          key={feature}
          className={cn(
            "rounded-md border px-2 py-1 text-[11px] font-medium text-muted-foreground",
            tone.border,
            status !== "later" && tone.surface
          )}
        >
          {feature}
        </span>
      ))}
    </div>
  )
}

function PhaseCard({ phase, index }: { phase: RoadmapPhase; index: number }) {
  const tone = statusTone[phase.status]

  return (
    <li className={cn("border bg-card p-4", tone.border)}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="font-mono text-xs text-muted-foreground">
          {String(index + 1).padStart(2, "0")}
        </span>
        <span className={cn("font-mono text-xs font-semibold", tone.text)}>
          {phase.version}
        </span>
      </div>

      <div className="mb-3 flex items-center gap-2">
        <span className={cn("size-2.5 shrink-0 rounded-sm", tone.dot)} />
        <span className="text-xs font-semibold uppercase text-muted-foreground">
          {phase.layer}
        </span>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold text-foreground">
          {phase.title}
        </h3>
        <StatusBadge status={phase.status} />
      </div>

      <p className="mb-4 text-sm leading-6 text-muted-foreground">
        {phase.summary}
      </p>

      <FeatureList features={phase.features} status={phase.status} />

      {phase.command ? (
        <div className="mt-5 rounded-md border border-border bg-muted/30 px-2.5 py-2 font-mono text-xs text-muted-foreground">
          <span className="text-foreground">$</span> {phase.command}
        </div>
      ) : null}
    </li>
  )
}

export function Roadmap({ phases = roadmapPhases }: { phases?: RoadmapPhase[] }) {
  const indexed = phases.map((phase, index) => ({ phase, index }))

  if (indexed.length === 0) {
    return (
      <section className="not-prose rounded-lg border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          No roadmap phases configured.
        </p>
      </section>
    )
  }

  return (
    <section className="not-prose" aria-label="Source-defined roadmap visualization">
      <div className="grid gap-3 lg:grid-cols-4">
        {statusOrder.map((status) => {
          const tone = statusTone[status]
          const items = indexed.filter((item) => item.phase.status === status)

          return (
            <section
              key={status}
              className={cn("min-w-0 border border-border bg-background", tone.header)}
              aria-labelledby={`roadmap-${status}`}
            >
              <div className="flex items-center justify-between gap-3 border-b border-border bg-background/70 px-4 py-3">
                <h2
                  id={`roadmap-${status}`}
                  className={cn("flex items-center gap-2 text-sm font-semibold", tone.text)}
                >
                  <span className={cn("size-2.5 rounded-sm", tone.dot)} />
                  {tone.label}
                </h2>
                <span className="font-mono text-xs text-muted-foreground">
                  {items.length}
                </span>
              </div>

              <ol className="grid gap-2 p-2">
                {items.length > 0 ? (
                  items.map(({ phase, index }) => (
                    <PhaseCard key={phase.id} phase={phase} index={index} />
                  ))
                ) : (
                  <li className="border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
                    No phases in this lane.
                  </li>
                )}
              </ol>
            </section>
          )
        })}
      </div>
    </section>
  )
}
