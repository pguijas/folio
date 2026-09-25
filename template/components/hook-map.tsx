interface HookMapItem {
  stage: string
  hook: string
  description: string
}

interface HookMapProps {
  title?: string
  hooks: HookMapItem[]
}

export function HookMap({ title = "Extension lifecycle", hooks }: HookMapProps) {
  return (
    <section className="my-6 rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h3 className="m-0 text-base font-semibold text-foreground">{title}</h3>
      </div>
      <ol className="m-0 list-none divide-y divide-border p-0">
        {hooks.map((item, index) => (
          <li
            key={`${item.stage}-${item.hook}`}
            className="grid gap-3 px-4 py-3 text-sm md:grid-cols-[2.5rem_minmax(9rem,0.8fr)_1fr]"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
              {index + 1}
            </span>
            <div>
              <p className="m-0 font-medium text-foreground">{item.stage}</p>
              <code className="mt-1 block font-mono text-xs text-primary">
                {item.hook}
              </code>
            </div>
            <p className="m-0 text-muted-foreground">{item.description}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
