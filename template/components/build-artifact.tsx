interface BuildArtifactItem {
  path: string
  kind: string
  description: string
}

interface BuildArtifactProps {
  title?: string
  description?: string
  items: BuildArtifactItem[]
}

export function BuildArtifact({
  title = "Build artifacts",
  description,
  items,
}: BuildArtifactProps) {
  return (
    <section className="my-6 rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h3 className="m-0 text-base font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      <div className="divide-y divide-border">
        {items.map((item) => (
          <div
            key={`${item.kind}-${item.path}`}
            className="grid gap-2 px-4 py-3 text-sm md:grid-cols-[minmax(10rem,0.75fr)_auto_1.5fr]"
          >
            <code className="font-mono text-foreground">{item.path}</code>
            <span className="w-fit rounded border border-border bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {item.kind}
            </span>
            <p className="m-0 text-muted-foreground">{item.description}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
