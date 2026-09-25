import { cn } from "@/lib/utils"

interface SwotProps {
  strengths: string[]
  weaknesses: string[]
  opportunities: string[]
  threats: string[]
  title?: string
}

const QUADRANTS = [
  {
    key: "strengths",
    label: "Strengths",
    letter: "S",
    tone: "text-emerald-700 dark:text-emerald-300",
    surface: "bg-emerald-500/[0.06]",
    marker: "bg-emerald-500",
  },
  {
    key: "weaknesses",
    label: "Weaknesses",
    letter: "W",
    tone: "text-amber-700 dark:text-amber-300",
    surface: "bg-amber-400/[0.07]",
    marker: "bg-amber-400",
  },
  {
    key: "opportunities",
    label: "Opportunities",
    letter: "O",
    tone: "text-sky-700 dark:text-sky-300",
    surface: "bg-sky-500/[0.06]",
    marker: "bg-sky-500",
  },
  {
    key: "threats",
    label: "Threats",
    letter: "T",
    tone: "text-rose-700 dark:text-rose-300",
    surface: "bg-rose-500/[0.06]",
    marker: "bg-rose-500",
  },
] as const

function Quadrant({
  label,
  letter,
  tone,
  surface,
  marker,
  items,
}: Omit<(typeof QUADRANTS)[number], "key"> & { items: string[] }) {
  return (
    <div className={cn("min-w-0 p-5", surface)}>
      <div className="mb-3 flex items-center gap-2.5">
        <span
          className={cn(
            "flex size-7 items-center justify-center rounded-md font-mono text-sm font-bold text-background",
            marker
          )}
        >
          {letter}
        </span>
        <p className={cn("m-0 text-sm font-semibold", tone)}>{label}</p>
      </div>
      <div role="list" className="m-0 grid list-none gap-2 p-0">
        {items.map((item) => (
          <p
            key={item}
            role="listitem"
            className="relative m-0 pl-4 text-sm leading-6 text-foreground/85 before:absolute before:left-0 before:top-[10px] before:size-1.5 before:rounded-full before:bg-current before:opacity-40"
          >
            {item}
          </p>
        ))}
      </div>
    </div>
  )
}

export function Swot({
  strengths,
  weaknesses,
  opportunities,
  threats,
  title,
}: SwotProps) {
  const items = { strengths, weaknesses, opportunities, threats }

  return (
    <figure className="not-prose my-6 overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
        <p className="m-0 font-mono text-xs uppercase tracking-[0.14em] text-muted-foreground">
          {title ?? "SWOT"}
        </p>
        <p className="m-0 hidden font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/50 sm:block">
          internal ↑ · external ↓
        </p>
      </div>
      <div className="grid divide-y divide-border sm:grid-cols-2 sm:divide-x">
        {QUADRANTS.map(({ key, ...quadrant }) => (
          <Quadrant key={key} {...quadrant} items={items[key] ?? []} />
        ))}
      </div>
    </figure>
  )
}
