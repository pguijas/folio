"use client"

import type { ToggleEvent as ReactToggleEvent } from "react"

import type { RoadmapGroup } from "@/lib/roadmap-utils"
import { ProjectIcon } from "@/components/roadmap-header"
import { RoadmapReleases } from "@/components/roadmap-releases"
import { cn } from "@/lib/utils"

/* One product, one card: its mark, its name, what it is, and its roadmap.
 *
 * Everything the roadmap has to say about a product is inside its card. The
 * page draws one card per project and shows them all at once; it used to draw
 * a switcher instead, which meant the product you were not reading was not on
 * the page at all. Two cards say the same thing without asking.
 *
 * Inside, the plan is compact — a node, a numeral, a title — and the release
 * you pick opens beside it. Printed at full detail one after another, seven
 * releases were a scroll rather than a plan; the split is what makes the card
 * a card instead of a container for a long document. The split failed on its
 * own, across the full width of the page, because one release is a sentence
 * and six checkboxes and a 1400px pane made that look like an error. Bounded
 * by a card that also carries a product name and a description, the same two
 * columns have something to be next to.
 *
 * A `<details>`, not a div with a boolean: the disclosure semantics, the
 * keyboard and the "still in the DOM while closed" are all native, and the
 * server can render it open without a script to unfold it.
 */

const FOCUS_RING =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"

export function RoadmapProjectCard({
  group,
  /** Whether the site actually named this project in docs.yaml. `RoadmapGroup`
   *  falls back to the raw key, and an unconfigured key is the literal string
   *  "shared" — printing that as a product name was a bug, so a roadmap whose
   *  projects were never named gets a card with no heading. With no heading
   *  there is nothing to collapse into, so it has no disclosure either. */
  named = true,
  open = true,
  onToggle,
}: {
  group: RoadmapGroup
  named?: boolean
  open?: boolean
  onToggle?: () => void
}) {
  const body = (
    <>
      {named && group.description ? (
        <p className="mt-2.5 mb-0 max-w-3xl text-sm leading-6 text-pretty text-muted-foreground">
          {group.description}
        </p>
      ) : null}

      <div className={cn(named && "mt-7 border-t border-border pt-7")}>
        {/* The project key scopes each card's fragment, so `#docs-0.3` and
            `#agents-0.3` are different links and neither card answers to the
            other's. The label names the list: two cards both announcing
            "Releases" are two regions a screen reader cannot tell apart. */}
        <RoadmapReleases
          phases={group.phases}
          projectKey={group.key}
          label={named ? `${group.label} releases` : "Releases"}
        />
      </div>
    </>
  )

  /* Zero elevation, as a constant: a card here is a border and nothing else.
     `--card` and `--background` are within 0.001 lightness in the shipped
     preset, so the fill draws nothing in light mode and the hairline is
     genuinely the only separation — that is accepted, not a gap to patch with
     a shadow. */
  const shell =
    "rounded-2xl border border-border bg-card px-5 py-5 sm:px-8 sm:py-7"

  if (!named) {
    return (
      <section aria-label="Releases" className={shell}>
        {body}
      </section>
    )
  }

  /* Let the element toggle itself, then follow it. Cancelling the click and
     driving `open` from React instead looked equivalent and was not: it takes
     the disclosure away from everything that opens one without a click —
     find-in-page, a fragment landing inside the card, an assistive
     technology's own expand — and leaves them flipping an attribute React
     immediately puts back. `toggle` fires after the element has moved, so the
     guard is what stops the state update from echoing. */
  const onDetailsToggle = (event: ReactToggleEvent<HTMLDetailsElement>) => {
    if (event.currentTarget.open !== open) onToggle?.()
  }

  return (
    /* `data-roadmap-card` is what the page's pre-paint rule selects on, so a
       reader arriving at ?product=<other> never sees this card open and then
       close. It carries the key rather than a boolean because the rule has to
       name the one card that stays. */
    <details
      open={open}
      onToggle={onDetailsToggle}
      data-roadmap-card={group.key}
      className={shell}
    >
      <summary
        className={cn(
          "flex cursor-pointer list-none items-center gap-2.5 rounded-md",
          "[&::-webkit-details-marker]:hidden",
          FOCUS_RING
        )}
      >
        <ProjectIcon
          projectKey={group.key}
          className="size-[18px] text-muted-foreground"
        />
        <h2
          id={`roadmap-card-${group.key}`}
          className="m-0 text-xl font-semibold tracking-tight text-foreground"
        >
          {group.label}
        </h2>

        {/* The one control on the card, so it sits at the far edge where the
            row ends rather than tucked against the name. */}
        <svg
          viewBox="0 0 16 16"
          fill="none"
          aria-hidden="true"
          data-roadmap-chevron=""
          className={cn(
            "ml-auto size-4 shrink-0 text-muted-foreground transition-transform duration-150 motion-reduce:transition-none",
            open && "rotate-180"
          )}
        >
          <path
            d="M4 6.5 8 10.5l4-4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </summary>

      {body}
    </details>
  )
}
