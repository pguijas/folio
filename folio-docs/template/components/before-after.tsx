interface BeforeAfterProps {
  before: string
  after: string
  beforeLabel?: string
  afterLabel?: string
  language?: string
}

function CodePane({ label, code }: { label: string; code: string }) {
  return (
    <div className="min-w-0">
      <div className="border-b border-border bg-muted/35 px-3 py-2 text-xs font-medium text-muted-foreground">
        {label}
      </div>
      <pre className="m-0 min-h-full overflow-x-auto bg-transparent p-3 font-mono text-sm leading-6">
        <code>{code.trim()}</code>
      </pre>
    </div>
  )
}

export function BeforeAfter({
  before,
  after,
  beforeLabel = "Before",
  afterLabel = "After",
}: BeforeAfterProps) {
  return (
    <figure className="my-6 overflow-hidden rounded-lg border border-border bg-card">
      <div className="grid divide-y divide-border md:grid-cols-2 md:divide-x md:divide-y-0">
        <CodePane label={beforeLabel} code={before} />
        <CodePane label={afterLabel} code={after} />
      </div>
    </figure>
  )
}
