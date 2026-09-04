import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/* The Folio for Agents landing speaks a quieter dialect than the docs landing.
 *
 * The docs landing separates its sections by filling alternate bands and by
 * putting a border around every card. That works there because almost every
 * card holds a picture. This page holds file listings, command output and one
 * large diagram, and boxing each of them produced a page of boxes inside boxes.
 *
 * So: one continuous background, one hairline at each section seam, a lot of
 * vertical air, and separation carried by whitespace rather than by fill. A
 * drawing sits on an unbordered plate with its route and its counts on a plain
 * line underneath, the way a caption sits under a figure. Lists are rows on
 * hairlines, value left and measurement right. Exactly one band is tinted, the
 * one holding the diagram the whole page argues from, so the tint means
 * something instead of alternating.
 *
 * Everything here reads from the theme tokens, so both modes come out of the
 * same file. No hex, no bare grey. */

export function Band({
  children,
  tint = false,
  seam = true,
  className,
}: {
  children: ReactNode
  /** The one tinted band. Reserve it. */
  tint?: boolean
  /** The hairline at the top of the section. */
  seam?: boolean
  className?: string
}) {
  return (
    <section
      className={cn(
        "landing-section px-6 py-20 sm:py-28",
        seam && "border-t border-border/60",
        tint && "bg-muted/35 dark:bg-muted/20",
        className
      )}
    >
      {children}
    </section>
  )
}

/** The reading frame. `wide` opts into the full site measure, which only the
 * board canvas needs; everything else keeps a narrower column so the page has
 * margins to breathe into. */
export function Measure({
  children,
  wide = false,
  className,
}: {
  children: ReactNode
  wide?: boolean
  className?: string
}) {
  return (
    <div
      className={cn(
        "mx-auto w-full",
        wide ? "max-w-site" : "max-w-[78rem]",
        className
      )}
    >
      {children}
    </div>
  )
}

/** A section heading. No eyebrow: a mono uppercase label that only names the
 * section below it is the design talking about itself. If a string here is not
 * a fact about the product, it does not belong on the page. */
export function Head({
  title,
  muted,
  lead,
  action,
  className,
}: {
  title: string
  /** Second clause, set in the muted tone, on its own line at wide widths. */
  muted?: string
  lead?: string
  action?: { label: string; href: string; external?: boolean }
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between",
        className
      )}
    >
      <div className="min-w-0">
        <h2 className="max-w-2xl text-[26px] leading-[1.14] font-semibold tracking-[-0.022em] text-balance text-foreground sm:text-[34px]">
          {title}
          {muted ? (
            <>
              {" "}
              <span className="text-muted-foreground">{muted}</span>
            </>
          ) : null}
        </h2>
        {lead ? (
          <p className="mt-4 max-w-xl text-[15px] leading-7 text-muted-foreground">
            {lead}
          </p>
        ) : null}
      </div>
      {action ? (
        <a
          href={action.href}
          target={action.external ? "_blank" : undefined}
          rel={action.external ? "noopener noreferrer" : undefined}
          className="group inline-flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          {action.label}
          <span
            aria-hidden="true"
            className="transition-transform group-hover:translate-x-0.5"
          >
            &#8594;
          </span>
        </a>
      ) : null}
    </div>
  )
}

/** The line under a figure: the route, then the counts, separated by middots.
 *
 * Set in the sans, not in mono. JetBrains Mono is a code face and this project
 * had it carrying eyebrows, status words, ordinals and captions until it was
 * doing eleven jobs in one component. Here it does one: literal text you could
 * type or that a program printed. A route is that, so wrap it in `Path`. A
 * count is not, so it stays in the sans with tabular figures. */
export function Meta({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <p
      className={cn(
        "m-0 text-[11.5px] leading-5 tracking-[0.005em] text-muted-foreground tabular-nums",
        className
      )}
    >
      {children}
    </p>
  )
}

/** A literal path, route, field name or command fragment sitting inside prose
 * or inside a Meta line. The one place mono is still correct at label size. */
export function Path({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <span className={cn("font-mono text-[11px] text-foreground/75", className)}>
      {children}
    </span>
  )
}

export function Dot() {
  return <span className="mx-1.5 text-border">&middot;</span>
}

/** An unbordered ground for a drawing. This is the piece that makes the page
 * calm: the figure is separated from the page by a tone step, not by a rule
 * around it. */
export function Plate({
  children,
  className,
  align = "center",
}: {
  children: ReactNode
  className?: string
  align?: "center" | "start"
}) {
  return (
    <div
      className={cn(
        "flex overflow-hidden rounded-xl bg-muted/45 p-5 dark:bg-muted/25",
        align === "center" ? "items-center justify-center" : "items-stretch",
        className
      )}
      aria-hidden="true"
    >
      {children}
    </div>
  )
}

/** A file or a terminal. A plain hairline: no traffic lights, no URL pill. The
 * three dots were rejected on this project and they were never carrying
 * information anyway. */
export function Frame({
  title,
  right,
  children,
  className,
  bodyClassName,
}: {
  title?: ReactNode
  right?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}) {
  return (
    <div
      className={cn(
        "min-w-0 overflow-hidden rounded-lg border border-border/70 bg-background",
        className
      )}
    >
      {title ? (
        <div className="flex items-center justify-between gap-4 border-b border-border/60 bg-muted/30 px-3.5 py-2 font-mono text-[10.5px] leading-none text-muted-foreground dark:bg-muted/20">
          <span className="min-w-0 truncate">{title}</span>
          {right ? <span className="shrink-0">{right}</span> : null}
        </div>
      ) : null}
      <div
        className={cn(
          "overflow-x-auto px-3.5 py-3 font-mono text-[10.5px] leading-[1.85] text-muted-foreground",
          bodyClassName
        )}
      >
        {children}
      </div>
    </div>
  )
}

/** A hairline list. Value on the left, measurement on the right. The densest
 * readable form there is, and the one thing on the page that can hold sixteen
 * items without becoming a wall. */
export function Rows({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <ul className={cn("m-0 list-none divide-y divide-border/60 p-0", className)}>
      {children}
    </ul>
  )
}

export function Row({
  left,
  right,
  href,
  external,
  className,
}: {
  left: ReactNode
  right?: ReactNode
  href?: string
  external?: boolean
  className?: string
}) {
  const body = (
    <>
      <span className="min-w-0 text-[14.5px] leading-6 text-foreground">
        {left}
      </span>
      {right ? (
        <span className="shrink-0 text-right text-[12.5px] leading-6 text-muted-foreground tabular-nums">
          {right}
        </span>
      ) : null}
    </>
  )

  if (href) {
    return (
      <li className={className}>
        <a
          href={href}
          target={external ? "_blank" : undefined}
          rel={external ? "noopener noreferrer" : undefined}
          className="-mx-3 flex items-baseline justify-between gap-6 rounded-md px-3 py-3.5 transition-colors hover:bg-muted/50 dark:hover:bg-muted/25"
        >
          {body}
        </a>
      </li>
    )
  }

  return (
    <li
      className={cn("flex items-baseline justify-between gap-6 py-3.5", className)}
    >
      {body}
    </li>
  )
}

/** A figure with its caption below it, Linear's card shape: the picture, then a
 * plain measurement line, then the claim, then one sentence. No box around the
 * set. */
export function Figure({
  plate,
  meta,
  title,
  detail,
  href,
  external,
  className,
}: {
  plate: ReactNode
  meta?: ReactNode
  title: string
  detail?: string
  href?: string
  external?: boolean
  className?: string
}) {
  const heading = href ? (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer" : undefined}
      className="text-foreground underline-offset-4 hover:underline"
    >
      {title}
    </a>
  ) : (
    title
  )

  return (
    <figure className={cn("m-0 flex min-w-0 flex-col", className)}>
      {plate}
      <figcaption className="mt-4 min-w-0">
        {meta ? <Meta>{meta}</Meta> : null}
        <p className="mt-1.5 m-0 text-[15px] leading-6 font-semibold text-foreground">
          {heading}
        </p>
        {detail ? (
          <p className="mt-1.5 m-0 text-[13.5px] leading-6 text-muted-foreground">
            {detail}
          </p>
        ) : null}
      </figcaption>
    </figure>
  )
}

/** A counted fact, set at a size that says it was measured. */
export function Stat({
  value,
  of,
  label,
  className,
}: {
  value: string
  of?: string
  label: string
  className?: string
}) {
  return (
    <div className={cn("min-w-0", className)}>
      <p className="m-0 flex items-baseline gap-1.5">
        <span className="text-[30px] leading-none font-semibold tracking-[-0.03em] text-foreground tabular-nums">
          {value}
        </span>
        {of ? (
          <span className="text-[14px] leading-none text-muted-foreground tabular-nums">
            {of}
          </span>
        ) : null}
      </p>
      <p className="mt-2 m-0 text-[12.5px] leading-5 text-muted-foreground">
        {label}
      </p>
    </div>
  )
}

/** A proportion drawn as a proportion. */
export function Meter({
  ratio,
  className,
}: {
  ratio: number
  className?: string
}) {
  const pct = Math.max(0, Math.min(1, ratio)) * 100
  return (
    <div
      className={cn("h-1 w-full overflow-hidden rounded-full bg-muted", className)}
      aria-hidden="true"
    >
      <span
        className="block h-full rounded-full bg-primary"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
