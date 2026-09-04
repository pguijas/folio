import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/**
 * The standard header rule for dedicated plugin views (and their embeds):
 * a mono micro-label on the left, metadata or controls on the right, one
 * hairline underneath. Roadmap and kanban both open with this rule, so
 * every plugin page shares one grammar.
 */
export function ViewHeaderRule({
  label,
  right,
  compact = false,
  className,
}: {
  label: string
  right?: ReactNode
  compact?: boolean
  className?: string
}) {
  return (
    <header
      className={cn(
        "flex items-center justify-between gap-4 border-b border-border",
        compact ? "mb-4 pb-2.5" : "mb-8 pb-4",
        className
      )}
    >
      <p
        className={cn(
          "m-0 font-mono uppercase tracking-[0.14em] text-muted-foreground",
          compact ? "text-[10px]" : "text-xs"
        )}
      >
        {label}
      </p>
      {right ? <div className="flex items-center gap-3">{right}</div> : null}
    </header>
  )
}
