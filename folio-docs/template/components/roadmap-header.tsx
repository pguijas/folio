import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/* The roadmap page's masthead.
 *
 * One background: the header sits on the page, not on a card. The band this
 * replaces filled its own `bg-card` section behind a border, which split the
 * top of the page into a second colour and made the first thing a reader saw
 * a slab rather than a title. There is no backdrop and no decorative spine
 * either — the page below is already a diagram of nodes and lines, and
 * drawing an ornamental one above it says nothing twice.
 *
 * Sans throughout. Mono is for a version numeral, which lives on the cards
 * below, not here.
 *
 * It holds no selection. It used to own a project switcher, so it also owned
 * the state and took its body as a render prop; the page now draws one card
 * per project and shows both at once, so there is nothing to select and this
 * is a plain server component again.
 */

interface RoadmapHeaderProps {
  /** The page's name. Drawn once, as the h1, and nowhere else. */
  title?: string
  description?: string
  /** Sibling public views (the board), as quiet text links. */
  links?: { label: string; href: string }[]
  /** The page body: the project cards. */
  children?: ReactNode
}

export const FOCUS_RING =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"

/**
 * A mark per project, drawn inline because the template ships no icon set and
 * this needs two glyphs, not a dependency.
 *
 * Keyed by the project key from docs.yaml, with a neutral dot for anything
 * unrecognised — a site whose projects are not Folio's still gets a card that
 * lines up, just without a bespoke mark. A framework component should not know
 * these two names; when this lands in the real roadmap the glyph belongs in
 * `roadmap.projects.<key>.icon` alongside the label.
 */
export function ProjectIcon({
  projectKey,
  className,
}: {
  projectKey: string
  className?: string
}) {
  const common = {
    viewBox: "0 0 16 16",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    className: cn("size-4 shrink-0", className),
  }

  // Docs: a page. Agents: a robot.
  if (projectKey === "docs") {
    return (
      <svg {...common}>
        <path d="M4 2h5l3 3v9H4z" />
        <path d="M9 2v3h3" />
      </svg>
    )
  }
  if (projectKey === "agents") {
    return (
      <svg {...common}>
        <path d="M8 1.5v2" />
        <rect x="2.75" y="3.75" width="10.5" height="8" rx="2.25" />
        <path d="M5.5 11.75v1.75M10.5 11.75v1.75" />
        <circle cx="5.9" cy="7.5" r="0.9" fill="currentColor" stroke="none" />
        <circle cx="10.1" cy="7.5" r="0.9" fill="currentColor" stroke="none" />
      </svg>
    )
  }
  return (
    <svg {...common}>
      <circle cx="8" cy="8" r="3.25" />
    </svg>
  )
}

export function RoadmapHeader({
  title,
  description,
  links,
  children,
}: RoadmapHeaderProps) {
  return (
    <div className="not-prose">
      <header className="pt-4 pb-2">
        <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-5">
          {title ? (
            <h1 className="m-0 max-w-3xl text-4xl leading-[1.05] font-bold tracking-[-0.03em] text-balance text-foreground sm:text-5xl">
              {title}
            </h1>
          ) : null}
          {/* Same border, radius and hover as the project cards below, so the
              header reads as one family rather than a title with a stray link
              beside it. It leaves the page, so it keeps an arrow. */}
          {links?.length ? (
            <nav className="flex flex-wrap items-center gap-2 lg:mt-2">
              {links.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "group inline-flex items-center gap-2 rounded-lg border border-border px-3.5 py-2 text-sm font-medium text-muted-foreground transition-colors",
                    "hover:border-foreground/30 hover:bg-card hover:text-foreground",
                    FOCUS_RING
                  )}
                >
                  {link.label}
                  <svg
                    viewBox="0 0 16 16"
                    fill="none"
                    aria-hidden="true"
                    className="size-3.5 transition-transform duration-150 group-hover:translate-x-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-x-0"
                  >
                    <path
                      d="M3 8h9M8.5 4.5 12 8l-3.5 3.5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </a>
              ))}
            </nav>
          ) : null}
        </div>

        {description ? (
          <p className="mt-5 max-w-2xl text-lg leading-8 text-pretty text-muted-foreground">
            {description}
          </p>
        ) : null}
      </header>

      <div className="mt-7">{children}</div>
    </div>
  )
}
