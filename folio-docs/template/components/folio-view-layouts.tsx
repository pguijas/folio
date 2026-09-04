import type { CSSProperties, ReactNode } from "react"

import { LandingNavbar } from "@/components/landing-navbar"
import { ThemeStyleBootstrap } from "@/components/theme-configurator"
import { cn } from "@/lib/utils"

interface PublicLayoutProps {
  title?: string
  eyebrow?: string
  description?: string
  /** Document-shaped views (roadmap) read in a centered column; board-shaped
   * views (kanban) keep the full width. */
  narrow?: boolean
  /** Tool-shaped views (the board) drop the band: a working surface should
   * not spend a screen of chrome on a display title before the first card,
   * and it carries its own name and cross-links in its own toolbar.
   * Reading surfaces keep the band. */
  dense?: boolean
  /** Sibling public views (e.g. roadmap ↔ board), rendered as quiet
   * cross-links on the band's top row opposite the Home link. */
  links?: { label: string; href: string }[]
  /** App-shaped views (the board's workspace mode) take exactly the
   * viewport below the navbar and scroll inside themselves, so at lg+ the
   * frame drops its vertical padding — kept, the page would scroll by
   * exactly that padding. Below lg the view flows and the dense padding
   * stays. */
  workspace?: boolean
  /** Relative path from this view to the site root. Defaults to ".." for
   * views one level down. */
  pathToRoot?: string
  children: ReactNode
}

export function PublicLayout({
  title,
  eyebrow,
  description,
  narrow = false,
  dense = false,
  links,
  workspace = false,
  pathToRoot = "..",
  children,
}: PublicLayoutProps) {
  // `max-w-site` is the whole site's frame (globals.css, --container-site):
  // the navbar, the landing's bands and these views all read from it, so a
  // board and the page above it line up and none of them is squeezed into a
  // reading column on a large screen. Only `narrow` opts out, because a
  // roadmap is a document and a document wants a line length.
  const measure = narrow ? "max-w-4xl" : "max-w-site"
  // `data-folio-surface="board"` puts the page on pure white in light mode
  // (see globals.css). A tool surface reads cleaner without the paper tint
  // the reading surfaces carry, and it is an override of the `--background`
  // token rather than a hard-coded fill, so dark mode and every preset keep
  // their own value.
  return (
    <main
      data-folio-surface={dense ? "board" : undefined}
      className="min-h-screen bg-background pt-16 text-foreground"
      // The docs shell gets this variable from nextra; a public view has to
      // state it itself. The navbar below is `fixed top-0` and 4rem tall —
      // the same fact `pt-16` encodes — and the board's composer rail (and
      // anything else that offsets against the navbar) computes sticky tops
      // and viewport bounds from it. Undeclared, the fallback 0px slid the
      // rail's controls under the navbar and oversized its max-height.
      style={{ "--nextra-navbar-height": "4rem" } as CSSProperties}
    >
      <ThemeStyleBootstrap />
      {/* A public plugin view can sit at any depth, the front page
          included; pathToRoot carries its measure. The bar takes the
          view's own width: a workspace runs to the edges, so a navbar
          stopping at `max-w-site` would be the only centered thing on
          the page. */}
      <LandingNavbar pathToRoot={pathToRoot} workspace={workspace} />
      {/* Tool surfaces (the board) render no band at all: `dense` means
          the view carries its own name and cross-links inside its own
          toolbar, so the page opens on the work rather than on a header.
          Reading surfaces (the roadmap) keep the full band below. */}
      {(title || eyebrow || description) && !dense && (
        <section className="relative isolate overflow-hidden border-b border-border bg-card">
          {/* Band backdrop: graph-paper dots plus a roadmap spine, both in
              the primary token so theme presets restyle them. Static by
              design — nothing to disable for reduced motion. */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle,var(--color-primary)_1px,transparent_1.5px)] [mask-image:radial-gradient(120%_130%_at_100%_0%,black,transparent_62%)] [background-size:24px_24px] opacity-[0.07] dark:opacity-[0.11]" />
            <svg
              viewBox="0 0 520 210"
              fill="none"
              className="absolute top-1/2 -right-8 hidden w-[520px] -translate-y-1/2 [mask-image:linear-gradient(to_left,black_60%,transparent)] text-primary opacity-[0.16] lg:block dark:opacity-[0.22]"
            >
              <path
                d="M0 178 L520 38"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeDasharray="2 7"
                strokeLinecap="round"
              />
              <g transform="translate(88 154)">
                <circle r="15" fill="currentColor" />
                <path
                  d="M-6 0.5 L-1.5 5 L7 -4.5"
                  stroke="var(--color-card)"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                />
              </g>
              <g transform="translate(250 111)">
                <circle
                  r="15"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  fill="var(--color-card)"
                />
                <circle r="4.5" fill="currentColor" />
              </g>
              <g transform="translate(400 70)">
                <circle
                  r="15"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeDasharray="3 5"
                  fill="var(--color-card)"
                />
              </g>
              <g transform="translate(492 45)">
                <circle
                  r="10"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeDasharray="3 5"
                  fill="var(--color-card)"
                />
              </g>
            </svg>
          </div>
          <div
            className={cn("relative mx-auto px-6", measure, "py-12 sm:py-16")}
          >
            <div className="mb-5 flex items-center justify-between gap-4">
              <a
                href={`${pathToRoot}/`}
                className="inline-flex items-center gap-1.5 font-mono text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                <span aria-hidden="true">&larr;</span> Home
              </a>
              {links && links.length > 0 ? (
                <nav className="flex items-center gap-5">
                  {links.map((link) => (
                    <a
                      key={link.href}
                      href={link.href}
                      className="group inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-background px-3 font-sans text-xs font-medium text-muted-foreground transition-colors hover:border-foreground/40 hover:text-foreground"
                    >
                      {link.label}{" "}
                      <span
                        aria-hidden="true"
                        className="transition-transform group-hover:translate-x-0.5"
                      >
                        &rarr;
                      </span>
                    </a>
                  ))}
                </nav>
              ) : null}
            </div>
            {eyebrow && (
              <p className="font-mono text-xs text-muted-foreground uppercase">
                {eyebrow}
              </p>
            )}
            {title && (
              <h1 className="mt-4 max-w-3xl text-4xl font-bold tracking-normal text-foreground sm:text-5xl">
                {title}
              </h1>
            )}
            {description && (
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </section>
      )}
      {/* `pt-0` on a dense surface was right only while the board carried a
          masthead: the masthead's own top padding was the gap under the
          navbar. With the masthead gone the toolbar sat flush against the
          navbar's bottom edge — 1px of daylight — so the surface has to
          hold that space itself now.

          A workspace goes full-bleed at lg+, not just unpadded vertically:
          its rail is drawn flush-left (squared corners, no left border),
          and inside a centered, side-padded measure that edge floated 24px
          into whitespace. The workspace holds its own inner air instead —
          the rail touches the viewport, the board column pads itself.
          Below lg the page flows normally and the drawer takes over. */}
      <section
        className={cn(
          "mx-auto px-6",
          measure,
          dense ? "pt-7 pb-8" : "py-10",
          workspace && "lg:max-w-none lg:px-0 lg:pt-0 lg:pb-0"
        )}
      >
        {children}
      </section>
    </main>
  )
}
