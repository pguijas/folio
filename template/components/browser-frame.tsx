import type { ReactNode } from "react"

/**
 * Browser window chrome around arbitrary content.
 *
 * Frames live embeds (roadmap miniatures, doc previews, rendered components)
 * as a small browser window: three dots, a mono URL bar, and an optional
 * right-aligned mono label such as "● LIVE". An optional `footer` renders as
 * a status-bar strip inside the window — the place for actions that belong
 * to the framed content. Server-renderable and not-prose-safe so it can sit
 * inside MDX without picking up prose margins.
 */
export function BrowserFrame({
  url,
  label,
  footer,
  children,
}: {
  url: string
  label?: string
  footer?: ReactNode
  children?: ReactNode
}) {
  return (
    // No shadow. The hairline and the card fill are what separate this frame
    // from the section behind it, the way every other surface in this theme is
    // separated. A 50px drop shadow under the roadmap made one exhibit float
    // while the figures either side of it sat flat on the page.
    <figure
      data-slot="browser-frame"
      className="not-prose relative m-0 flex flex-col overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center gap-3 border-b border-border bg-muted/40 px-3.5 py-2.5">
        <span aria-hidden="true" className="flex shrink-0 gap-1.5">
          <span className="size-[9px] rounded-full bg-border" />
          <span className="size-[9px] rounded-full bg-border" />
          <span className="size-[9px] rounded-full bg-border" />
        </span>
        <p className="m-0 min-w-0 max-w-xs flex-1 truncate rounded-md border border-border/70 bg-background px-3 py-1 font-mono text-[11px] leading-4 text-muted-foreground">
          {url}
        </p>
        {label ? (
          <p className="m-0 ml-auto shrink-0 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            {label}
          </p>
        ) : null}
      </div>
      <div className="min-w-0 flex-1 bg-card p-4 sm:p-5">{children}</div>
      {footer ? (
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-1.5 border-t border-border bg-muted/40 px-4 py-2.5 font-mono text-xs">
          {footer}
        </div>
      ) : null}
    </figure>
  )
}
