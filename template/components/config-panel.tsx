import type { ReactNode } from "react"

interface ConfigField {
  name: string
  type?: string
  default?: string
  description: string
}

interface ConfigPanelProps {
  title: string
  description?: string
  fields?: ConfigField[]
  children?: ReactNode
}

export function ConfigPanel({
  title,
  description,
  fields = [],
  children,
}: ConfigPanelProps) {
  return (
    <section data-slot="config-panel" className="my-6 overflow-hidden rounded-lg border border-border bg-card">
      <div data-slot="config-panel-header" className="border-b border-border bg-muted/35 px-4 py-3">
        <h3 data-slot="config-panel-title" className="m-0 text-base font-semibold text-foreground">{title}</h3>
        {description && (
          <p data-slot="config-panel-description" className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {children && (
        <div data-slot="config-panel-code" className="border-b border-border [&_pre]:!m-0 [&_pre]:!rounded-none [&_pre]:!border-0">
          {children}
        </div>
      )}
      {fields.length > 0 && (
        <dl data-slot="config-panel-fields" className="divide-y divide-border">
          {fields.map((field) => (
            <div
              key={field.name}
              data-slot="config-panel-field"
              className="grid gap-2 px-4 py-3 text-sm md:grid-cols-[minmax(9rem,0.75fr)_1.5fr]"
            >
              <dt className="font-mono text-foreground">{field.name}</dt>
              <dd className="m-0 text-muted-foreground">
                <div>{field.description}</div>
                {(field.type || field.default) && (
                  <div className="mt-1 flex flex-wrap gap-2">
                    {field.type && (
                      <code data-slot="config-panel-type" className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs text-foreground">
                        {field.type}
                      </code>
                    )}
                    {field.default && (
                      <code data-slot="config-panel-default" className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs text-foreground">
                        default: {field.default}
                      </code>
                    )}
                  </div>
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  )
}
