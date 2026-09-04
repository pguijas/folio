import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface CommandGridProps {
  children: ReactNode
}

interface CommandCardProps {
  command: string
  title: string
  description: string
  href?: string
  flags?: string[]
}

export function CommandGrid({ children }: CommandGridProps) {
  return (
    <div className="my-6 grid gap-3 md:grid-cols-2">
      {children}
    </div>
  )
}

export function CommandCard({
  command,
  title,
  description,
  href,
  flags = [],
}: CommandCardProps) {
  const content = (
    <div
      className={cn(
        "h-full rounded-lg border border-border bg-card px-4 py-3 transition-colors",
        href && "hover:border-primary/45 hover:bg-muted/25"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="m-0 text-base font-semibold text-foreground">{title}</h3>
          <code className="mt-1 block font-mono text-sm text-primary">{command}</code>
        </div>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      {flags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {flags.map((flag) => (
            <code
              key={flag}
              className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs text-foreground"
            >
              {flag}
            </code>
          ))}
        </div>
      )}
    </div>
  )

  if (href) {
    return (
      <a href={href} className="no-underline">
        {content}
      </a>
    )
  }

  return content
}
