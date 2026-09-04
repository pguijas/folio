"use client"

import { cn } from "@/lib/utils"

export function Timeline({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative my-8 ml-4 pl-8 space-y-8">
      <div className="absolute left-0 top-2 bottom-2 w-px bg-border" />
      {children}
    </div>
  )
}

export function TimelineItem({
  date,
  title,
  badge,
  children,
}: {
  date: string
  title: string
  badge?: string
  children: React.ReactNode
}) {
  return (
    <div className="relative">
      <div className="absolute -left-[35px] top-1 h-3 w-3 rounded-full bg-primary ring-4 ring-background" />
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-medium text-muted-foreground">{date}</span>
        {badge && (
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
              badge === "breaking"
                ? "bg-destructive/10 text-destructive"
                : badge === "new"
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  : "bg-muted text-muted-foreground"
            )}
          >
            {badge}
          </span>
        )}
      </div>
      <h4 className="text-sm font-semibold text-foreground mb-1">{title}</h4>
      <div className="text-sm text-muted-foreground [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
        {children}
      </div>
    </div>
  )
}

TimelineItem.displayName = "TimelineItem"
