import { cn } from "@/lib/utils"

type ChecklistState = "done" | "warn" | "todo"

interface ChecklistItem {
  label: string
  description?: string
  state?: ChecklistState
}

interface ChecklistProps {
  title?: string
  items: ChecklistItem[]
}

const stateStyles: Record<ChecklistState, string> = {
  done: "border-primary/25 bg-primary/10 text-primary",
  warn: "border-destructive/25 bg-destructive/10 text-destructive",
  todo: "border-border bg-muted text-muted-foreground",
}

const stateLabels: Record<ChecklistState, string> = {
  done: "OK",
  warn: "WARN",
  todo: "TODO",
}

export function Checklist({ title, items }: ChecklistProps) {
  return (
    <section className="my-6 rounded-lg border border-border bg-card">
      {title && (
        <div className="border-b border-border px-4 py-3">
          <h3 className="m-0 text-base font-semibold text-foreground">{title}</h3>
        </div>
      )}
      <ul className="m-0 list-none divide-y divide-border p-0">
        {items.map((item) => {
          const state = item.state ?? "todo"
          return (
            <li key={item.label} className="flex gap-3 px-4 py-3">
              <span
                className={cn(
                  "mt-0.5 h-fit rounded border px-1.5 py-0.5 text-[0.68rem] font-semibold",
                  stateStyles[state]
                )}
              >
                {stateLabels[state]}
              </span>
              <div className="min-w-0">
                <p className="m-0 text-sm font-medium text-foreground">{item.label}</p>
                {item.description && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.description}
                  </p>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
