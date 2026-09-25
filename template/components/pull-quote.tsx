import type { ReactNode } from "react"

interface PullQuoteProps {
  children: ReactNode
  kicker?: string
  attribution?: string
}

export function PullQuote({ children, kicker, attribution }: PullQuoteProps) {
  return (
    <figure className="not-prose relative my-8 overflow-hidden rounded-lg border border-primary/25 bg-primary/[0.04] px-6 py-6 sm:px-8">
      <span
        aria-hidden="true"
        className="pointer-events-none absolute -top-5 left-3 font-serif text-[7rem] leading-none text-primary/10 select-none"
      >
        “
      </span>
      {kicker ? (
        <p className="relative m-0 mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
          {kicker}
        </p>
      ) : null}
      <blockquote className="relative m-0 border-0 p-0 text-lg leading-8 font-medium tracking-tight text-foreground sm:text-xl sm:leading-9">
        {children}
      </blockquote>
      {attribution ? (
        <figcaption className="relative mt-3 font-mono text-xs text-muted-foreground">
          — {attribution}
        </figcaption>
      ) : null}
    </figure>
  )
}
