interface Stat {
  value: string
  label: string
  detail?: string
}

interface StatStripProps {
  stats: Stat[]
}

export function StatStrip({ stats }: StatStripProps) {
  return (
    <figure className="not-prose my-6 overflow-hidden rounded-lg border border-border bg-card">
      <div className="grid divide-y divide-border sm:auto-cols-fr sm:grid-flow-col sm:divide-x sm:divide-y-0">
        {stats.map((stat) => (
          <div key={stat.label} className="min-w-0 px-5 py-4">
            <p className="m-0 font-mono text-2xl font-bold tracking-tight text-foreground tabular-nums sm:text-3xl">
              {stat.value}
            </p>
            <p className="m-0 mt-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              {stat.label}
            </p>
            {stat.detail ? (
              <p className="m-0 mt-1 text-xs leading-5 text-muted-foreground/80">
                {stat.detail}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </figure>
  )
}
