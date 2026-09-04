import { openApiSources, type OpenApiSource } from "@/lib/openapi-data"
import { cn } from "@/lib/utils"

const methodStyles: Record<string, string> = {
  GET: "border-emerald-500/30 bg-emerald-500/[0.08] text-emerald-700 dark:text-emerald-300",
  POST: "border-sky-500/30 bg-sky-500/[0.08] text-sky-700 dark:text-sky-300",
  PUT: "border-amber-500/35 bg-amber-500/[0.1] text-amber-700 dark:text-amber-300",
  PATCH: "border-violet-500/30 bg-violet-500/[0.08] text-violet-700 dark:text-violet-300",
  DELETE: "border-rose-500/30 bg-rose-500/[0.08] text-rose-700 dark:text-rose-300",
}

function MethodBadge({ method }: { method: string }) {
  return (
    <span
      className={cn(
        "inline-flex h-6 min-w-14 items-center justify-center rounded-md border px-2 font-mono text-[11px] font-semibold",
        methodStyles[method] ||
          "border-border bg-muted/40 text-muted-foreground"
      )}
    >
      {method}
    </span>
  )
}

function SourceSummary({ source }: { source: OpenApiSource }) {
  return (
    <div className="grid gap-3 border border-border bg-card p-4 sm:grid-cols-3">
      <div>
        <div className="text-[11px] font-semibold uppercase text-muted-foreground">
          Operations
        </div>
        <div className="mt-1 font-mono text-2xl font-semibold text-foreground">
          {source.operations.length}
        </div>
      </div>
      <div>
        <div className="text-[11px] font-semibold uppercase text-muted-foreground">
          Schemas
        </div>
        <div className="mt-1 font-mono text-2xl font-semibold text-foreground">
          {source.schemas.length}
        </div>
      </div>
      <div>
        <div className="text-[11px] font-semibold uppercase text-muted-foreground">
          Version
        </div>
        <div className="mt-1 font-mono text-2xl font-semibold text-foreground">
          {source.version || "n/a"}
        </div>
      </div>
    </div>
  )
}

function OperationList({ source }: { source: OpenApiSource }) {
  if (source.operations.length === 0) {
    return (
      <div className="border border-dashed border-border bg-card p-4 text-sm text-muted-foreground">
        No operations were found in this OpenAPI source.
      </div>
    )
  }

  return (
    <ol className="grid gap-2">
      {source.operations.map((operation) => (
        <li
          key={`${operation.method}:${operation.path}`}
          className="grid gap-3 border border-border bg-card p-4 lg:grid-cols-[auto_minmax(0,1fr)]"
        >
          <MethodBadge method={operation.method} />
          <div className="min-w-0">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <code className="break-all rounded-md bg-muted px-1.5 py-1 font-mono text-sm text-foreground">
                {operation.path}
              </code>
              {operation.operationId ? (
                <span className="font-mono text-xs text-muted-foreground">
                  {operation.operationId}
                </span>
              ) : null}
            </div>
            <h3 className="mt-3 text-base font-semibold text-foreground">
              {operation.summary || "Untitled operation"}
            </h3>
            {operation.description ? (
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {operation.description}
              </p>
            ) : null}
            {operation.tags.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {operation.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-md border border-border bg-muted/35 px-2 py-1 text-[11px] font-medium text-muted-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  )
}

function SchemaRail({ source }: { source: OpenApiSource }) {
  return (
    <aside className="border border-border bg-muted/20 p-4">
      <h2 className="text-sm font-semibold text-foreground">Schema index</h2>
      {source.schemas.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {source.schemas.map((schema) => (
            <span
              key={schema}
              className="rounded-md border border-border bg-background px-2 py-1 font-mono text-xs text-muted-foreground"
            >
              {schema}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">
          This spec does not define reusable schemas.
        </p>
      )}
      {source.servers.length > 0 ? (
        <div className="mt-5">
          <h3 className="text-xs font-semibold uppercase text-muted-foreground">
            Servers
          </h3>
          <div className="mt-2 grid gap-2">
            {source.servers.map((server) => (
              <code
                key={server}
                className="break-all rounded-md border border-border bg-background px-2 py-1.5 font-mono text-xs text-muted-foreground"
              >
                {server}
              </code>
            ))}
          </div>
        </div>
      ) : null}
    </aside>
  )
}

export function OpenApiReference({
  sourceTitle,
  sources = openApiSources,
}: {
  sourceTitle?: string
  sources?: OpenApiSource[]
}) {
  const source =
    sources.find((candidate) => candidate.title === sourceTitle) || sources[0]

  if (!source) {
    return (
      <section className="not-prose border border-dashed border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          No OpenAPI sources configured.
        </p>
      </section>
    )
  }

  return (
    <section className="not-prose" aria-label={`${source.title} OpenAPI reference`}>
      <div className="mb-5 border border-border bg-background p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="rounded-md border border-border bg-muted/40 px-2 py-1 font-mono text-[11px] font-semibold uppercase text-muted-foreground">
            OpenAPI
          </span>
          <span className="font-mono text-xs text-muted-foreground">
            {source.route}
          </span>
        </div>
        <h2 className="text-2xl font-semibold tracking-normal text-foreground">
          {source.title}
        </h2>
        {source.description ? (
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {source.description}
          </p>
        ) : null}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
        <div className="grid gap-4">
          <SourceSummary source={source} />
          <OperationList source={source} />
        </div>
        <SchemaRail source={source} />
      </div>
    </section>
  )
}
