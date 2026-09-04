"use client"

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react"

import type { RoadmapPhase, RoadmapStatus } from "@/lib/roadmap-data"
import { sortByVersion, statusLabels } from "@/lib/roadmap-utils"
import { cn } from "@/lib/utils"

/* One project's releases: the whole plan on the left, one release on the right.
 *
 * Printing every release at full detail, one after another, made reading how
 * far a product had got a matter of scrolling past seven summaries and forty
 * features. Split in two, the left column is the plan — a node, a numeral, a
 * title, nothing else — short enough to take in at a glance, and the detail
 * that used to be inline is shown for whichever release is selected.
 *
 * Every release's detail is in the markup, always; the ones not selected carry
 * `hidden`. Rendering only the selected one would put a single release in the
 * served HTML and leave the rest reachable by click alone — which is how this
 * page lost ten of its eleven releases to crawlers, to Markdown mirrors and to
 * anyone reading with JavaScript off. Hiding is a style; not rendering is a
 * deletion. `.folio-roadmap-panel` in globals.css stacks them all in one grid
 * cell so the column is as tall as the tallest release and stops resizing.
 *
 * Selection is one mark that travels. It used to be drawn per row — the picked
 * row gained a fill, the previous one lost it, and the two cross-faded in
 * different places up to six rows apart, so nothing told the eye where the
 * selection had gone. One marker riding the rungs is the conclusion of the
 * fixed 44px row this list was already built on.
 *
 * Sans throughout. Mono is for the version numeral and a phase's command —
 * the two strings here that are read as literals.
 */

const FOCUS_RING =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"

/* The two-column split starts above 1024, not at it: 1024 belongs to the
 * stacked case and Tailwind's `lg` would claim it, so the wide variant is
 * `min-[1025px]:` — written out at every use, because the class scanner reads
 * this file as text and would not see a prefix held in a constant. */

/** Row pitch. The marker's travel is this times the selected index, so the two
 *  cannot drift: change the row height and change this together. */
const ROW_PITCH = "2.75rem" // h-11

/** The numeral as it is printed and as it is written to the hash. */
function versionOf(phase: RoadmapPhase): string {
  return phase.version.replace(/^v/i, "")
}

/**
 * The fragment that names one release.
 *
 * Scoped by project because the page draws one of these per product and both
 * products number from 0.1 — an unscoped `#0.1` would name a release in each
 * card and the two would fight over it.
 */
function hashFor(projectKey: string, phase: RoadmapPhase): string {
  const version = versionOf(phase)
  return projectKey ? `${projectKey}-${version}` : version
}

/**
 * The release a reader lands on: the one in progress, else the first still to
 * come, else — everything shipped — the last one.
 *
 * "The first still to come" is the first unshipped release in version order,
 * not the first one labelled `next`. This roadmap has 0.6 marked `later` ahead
 * of 0.7 marked `next`, so keying on the label would open 0.7 and skip 0.6.
 */
function defaultPhase(ordered: RoadmapPhase[]): RoadmapPhase | undefined {
  return (
    ordered.find((phase) => phase.status === "active") ??
    ordered.find((phase) => phase.status !== "shipped") ??
    ordered[ordered.length - 1]
  )
}

/* ---- the compact line --------------------------------------------------- */

/**
 * One node, four states, no legend: a filled dot has shipped, an accent ring
 * with an accent core is in progress, a plain ring is up next, and a fainter
 * ring is later. Weight decreases as the release gets further out, which is
 * the whole reading.
 *
 * None of them is drawn in `border-border`. In the shipped palette that token
 * is 1.5:1 against the card — enough for a divider, not enough for the only
 * mark saying what state a release is in.
 *
 * The `forced-colors:` variants exist because that reasoning has a second
 * failure mode: in a forced-colours mode every author background becomes
 * Canvas and every author border becomes CanvasText, so the filled disc turns
 * into a hole and the three rings — which differ only by `--primary` and by an
 * alpha fraction — flatten into one another. Four states with no legend have
 * no fallback reading when they collapse, so each is re-authored in a system
 * colour the UA honours.
 */
function ListNode({ status }: { status: RoadmapStatus }) {
  return (
    /* The disc masks the spine so the line reads as continuous behind a solid
       node and stays out of the middle of a hollow one. It is the card's own
       background because the row's selected fill stops short of this column. */
    <span
      aria-hidden="true"
      className="relative z-10 flex size-3.5 items-center justify-center rounded-full bg-card"
    >
      {status === "shipped" ? (
        <span className="size-2.5 rounded-full bg-muted-foreground/70 forced-colors:bg-[color:CanvasText]" />
      ) : null}
      {status === "active" ? (
        <span className="flex size-3.5 items-center justify-center rounded-full border border-primary forced-colors:border-[color:Highlight]">
          <span className="size-1.5 rounded-full bg-primary forced-colors:bg-[color:Highlight]" />
        </span>
      ) : null}
      {status === "next" ? (
        <span className="size-2.5 rounded-full border border-muted-foreground forced-colors:border-[color:CanvasText]" />
      ) : null}
      {status === "later" ? (
        <span className="size-2.5 rounded-full border border-muted-foreground/70 forced-colors:border-[color:GrayText]" />
      ) : null}
    </span>
  )
}

function ReleaseRow({
  phase,
  selected,
  first,
  last,
  /* The line is solid accent from the top down to the release in progress and
     a hairline after it: progress reads without counting nodes. Both halves of
     a row are drawn separately so the change of weight lands on the node
     itself, not a row above or below it. */
  aboveDone,
  belowDone,
  id,
  panelId,
  onSelect,
  buttonRef,
}: {
  phase: RoadmapPhase
  selected: boolean
  first: boolean
  last: boolean
  aboveDone: boolean
  belowDone: boolean
  id: string
  panelId: string
  onSelect: () => void
  buttonRef: (node: HTMLButtonElement | null) => void
}) {
  const active = phase.status === "active"
  const future = phase.status === "next" || phase.status === "later"

  return (
    <button
      ref={buttonRef}
      type="button"
      role="tab"
      id={id}
      aria-controls={panelId}
      aria-selected={selected}
      tabIndex={selected ? 0 : -1}
      onClick={onSelect}
      /* `relative` is load-bearing, not cosmetic: the selection marker is
         absolutely positioned in the tablist and would otherwise paint over
         every numeral and title. Positioned siblings paint in DOM order, and
         the marker is first, so the rows land on top of it.

         A fixed row height is what keeps the card still: the left column
         defines the rhythm, and nothing on the right can change it. */
      className={cn(
        "group relative flex h-11 w-full cursor-pointer items-center rounded-md text-left",
        "focus-visible:outline-none"
      )}
    >
      <span className="relative flex h-full w-4 shrink-0 items-center justify-center">
        {!first ? (
          <span
            aria-hidden="true"
            className={cn(
              "absolute top-0 left-1/2 h-1/2 w-px -translate-x-1/2",
              aboveDone
                ? "bg-primary forced-colors:bg-[color:Highlight]"
                : "bg-muted-foreground/30 forced-colors:bg-[color:GrayText]"
            )}
          />
        ) : null}
        {!last ? (
          <span
            aria-hidden="true"
            className={cn(
              "absolute bottom-0 left-1/2 h-1/2 w-px -translate-x-1/2",
              belowDone
                ? "bg-primary forced-colors:bg-[color:Highlight]"
                : "bg-muted-foreground/30 forced-colors:bg-[color:GrayText]"
            )}
          />
        ) : null}
        <ListNode status={phase.status} />
      </span>

      {/* The hover fill starts after the rail, so the line and the nodes never
          sit on a tinted band. Focus lands on this rectangle rather than on the
          button, so the focus ring and the selection marker agree about where
          a row is — on the button they were two rounded rectangles 24px apart,
          and `outline-offset-2` bled into the flush neighbours on every arrow
          step. */}
      <span
        className={cn(
          "ml-2 flex min-w-0 flex-1 items-center gap-2.5 rounded-md px-2.5 py-1.5 transition-colors",
          !selected && "group-hover:bg-muted/60",
          selected && "forced-colors:outline-1 forced-colors:outline-[color:Highlight]",
          "group-focus-visible:outline-2 group-focus-visible:outline-offset-0 group-focus-visible:outline-ring"
        )}
      >
        <span
          className={cn(
            "shrink-0 font-mono text-xs tabular-nums",
            active ? "text-primary" : "text-muted-foreground"
          )}
        >
          v{versionOf(phase)}
        </span>
        {/* Hover lifts a future release's title out of muted. The fill behind
            it is 1.06:1, which on a trackpad reads as no response at all, and
            a second channel costs nothing. It carries its own transition: the
            parent's `transition-colors` does not reach a child that sets its
            own colour. */}
        <span
          className={cn(
            "truncate text-sm tracking-tight transition-colors",
            selected
              ? "font-semibold text-foreground"
              : future
                ? "font-medium text-muted-foreground group-hover:text-foreground"
                : "font-medium text-foreground"
          )}
        >
          {phase.title}
        </span>
        {/* Points at the pane the row opened, and only while there is one to
            point at: stacked, the detail is underneath. Drawn on every row and
            hidden by opacity, so the title truncates at the same width whether
            or not the row is the selected one — and faded rather than flipped,
            or it pops off one row and on at another in the same frame. */}
        <svg
          viewBox="0 0 16 16"
          fill="none"
          aria-hidden="true"
          className={cn(
            "ml-auto hidden size-3.5 shrink-0 text-muted-foreground transition-opacity duration-150 ease-[cubic-bezier(0.16,1,0.3,1)] motion-reduce:transition-none min-[1025px]:block",
            !selected && "opacity-0"
          )}
        >
          <path
            d="M6 3.5 10.5 8 6 12.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    </button>
  )
}

/* ---- the selected release ----------------------------------------------- */

/** One feature, one line, in the checklist form the project's own board cards
 *  use: shipped work is checked off, everything pending is an open box. */
function FeatureItem({
  feature,
  status,
}: {
  feature: string
  status: RoadmapStatus
}) {
  const done = status === "shipped"
  return (
    <li className="flex items-start gap-3 text-sm leading-6 text-foreground/85">
      <span
        aria-hidden="true"
        className={cn(
          "mt-[5px] flex size-3.5 shrink-0 items-center justify-center rounded-[4px] border",
          done
            ? "border-muted-foreground/70 bg-muted-foreground/70 text-card"
            : status === "later"
              ? "border-dashed border-muted-foreground/60"
              : "border-muted-foreground/60"
        )}
      >
        {done ? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={3.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="size-2.5"
          >
            <path d="M20 6 9 17l-5-5" />
          </svg>
        ) : null}
      </span>
      <span className="min-w-0">{feature}</span>
    </li>
  )
}

function ReleaseDetail({ phase }: { phase: RoadmapPhase }) {
  const active = phase.status === "active"
  return (
    <>
      {/* Version and state above the title, the layer as a subtitle under it.
          Packed onto one slash-separated line the three read as a breadcrumb —
          a path you could click — when only one of them is a category at all. */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span
          className={cn(
            "font-mono text-sm tabular-nums",
            active ? "text-primary" : "text-muted-foreground"
          )}
        >
          v{versionOf(phase)}
        </span>
        <span
          className={cn(
            "text-sm font-medium",
            active ? "text-primary" : "text-muted-foreground"
          )}
        >
          {statusLabels[phase.status]}
        </span>
      </div>

      {/* The release being built is what the reader came for, and it used to
          be set at the same size as the product name 200px above it. */}
      <h3 className="mt-3 mb-0 text-2xl font-semibold tracking-tight text-balance text-foreground">
        {phase.title}
      </h3>

      {/* The layer sits under the title at the summary's size, not above it:
          it is a one- or two-word gloss, and at 16px it outranked the sentence
          that actually explains the release. */}
      <p className="mt-1.5 mb-0 text-sm text-muted-foreground">{phase.layer}</p>

      <p className="mt-4 mb-0 max-w-2xl text-sm leading-6 text-pretty text-muted-foreground">
        {phase.summary}
      </p>

      {/* Three columns where there is room for three. Two left a third of the
          pane empty at desktop width, which is what made the split read as a
          wide box holding one paragraph. `xl` rather than an arbitrary
          `min-[…]`: Tailwind orders arbitrary variants ahead of the named
          breakpoints, so `sm:grid-cols-2` won and the third column never
          arrived. */}
      {phase.features.length ? (
        <ul className="mt-5 mb-0 grid list-none grid-cols-1 gap-x-8 gap-y-1.5 border-t border-border p-0 pt-5 sm:grid-cols-2 xl:grid-cols-3">
          {phase.features.map((feature) => (
            <FeatureItem
              key={feature}
              feature={feature}
              status={phase.status}
            />
          ))}
        </ul>
      ) : null}

      {phase.command ? (
        <code className="mt-5 block overflow-x-auto border-0 bg-transparent p-0 font-mono text-xs text-muted-foreground">
          <span className="text-muted-foreground/50 select-none">$ </span>
          {phase.command}
        </code>
      ) : null}
    </>
  )
}

/* ---- the body ------------------------------------------------------------ */

interface RoadmapReleasesProps {
  /** One project's releases, or every release when none are named. */
  phases: RoadmapPhase[]
  /** Which project these belong to. It scopes the fragment, so two cards on
   *  one page can each hold a selection without naming each other's. */
  projectKey?: string
  /** What to call this list. Two cards on one page both labelled "Releases"
   *  are two regions a screen reader cannot tell apart. */
  label?: string
}

export function RoadmapReleases({
  phases,
  projectKey = "",
  label = "Releases",
}: RoadmapReleasesProps) {
  const uid = useId()
  const panelId = useCallback((id: string) => `${uid}-panel-${id}`, [uid])
  const tabId = useCallback((id: string) => `${uid}-tab-${id}`, [uid])

  const ordered = useMemo(() => sortByVersion(phases), [phases])
  const refs = useRef<Record<string, HTMLButtonElement | null>>({})
  const panelRefs = useRef<Record<string, HTMLDivElement | null>>({})

  /* `null` means "whatever this project opens on". Holding the fallback as an
   * absence rather than copying it into state is what makes a back button and
   * an empty hash land on the same release — and it is what the server
   * renders, so the markup and the first paint agree. */
  const [chosen, setChosen] = useState<string | null>(null)

  /* The marker only travels once a reader has moved it. Before that — first
   * paint, and a `#docs-0.5` deep link resolved in the effect below — it is
   * placed. Sliding in from the default release on arrival would animate
   * something nobody did. */
  const [armed, setArmed] = useState(false)

  /* Set only on the pointer path. Below 1025px the detail is under a list up
   * to 308px tall, so a tap changes content off-screen with no visible
   * response; a keyboard user in the same layout already has the focus ring
   * moving row to row, and scrolling on every arrow press would carry the
   * focused row out of view to fix a cue that is not missing. */
  const reveal = useRef(false)

  const selected =
    ordered.find((phase) => phase.id === chosen) ?? defaultPhase(ordered)

  /* Selection in the hash, so a release can be linked to. A click pushes —
   * back and forward walk the releases a reader opened — while arrow keys
   * replace, because holding Down through the list should not bury the page
   * the reader arrived from under a dozen entries. */
  const select = useCallback(
    (phase: RoadmapPhase, push: boolean) => {
      setArmed(true)
      if (push) reveal.current = true
      setChosen(phase.id)
      const hash = `#${hashFor(projectKey, phase)}`
      if (window.location.hash === hash) return
      if (push) window.history.pushState(null, "", hash)
      else window.history.replaceState(null, "", hash)
    },
    [projectKey]
  )

  useEffect(() => {
    const apply = () => {
      const raw = window.location.hash.slice(1)
      let want = raw
      try {
        want = decodeURIComponent(raw)
      } catch {
        // A malformed escape names no release.
      }
      /* A fragment belongs to one card. Strip this project's prefix and give
         up if it is not there, so selecting in one card never moves the
         other. */
      if (projectKey) {
        const prefix = `${projectKey}-`
        if (!want.startsWith(prefix)) {
          if (want) return
        } else {
          want = want.slice(prefix.length)
        }
      }
      want = want.replace(/^v/i, "")
      /* The numeral is the link a reader writes. The phase id is what the old
         page put on each heading, so `#extension` still opens 0.3 rather than
         quietly falling back to the default. */
      const match =
        ordered.find((phase) => versionOf(phase) === want) ??
        ordered.find((phase) => phase.id === want)
      /* No hash, or one this project does not have, is the default — which is
         also what makes Back out of a selection land where the page opened. */
      setChosen(match ? match.id : null)
    }
    apply()
    /* pushState never fires hashchange, and traversing entries it wrote fires
       popstate; a plain `#docs-0.3` link fires hashchange. Both, or one of the
       two ways in is deaf. Travel is armed here and not on the first `apply()`
       above: a deep link places the marker, a later navigation moves it. */
    const onNavigate = () => {
      setArmed(true)
      apply()
    }
    window.addEventListener("hashchange", onNavigate)
    window.addEventListener("popstate", onNavigate)
    return () => {
      window.removeEventListener("hashchange", onNavigate)
      window.removeEventListener("popstate", onNavigate)
    }
  }, [ordered, projectKey])

  /* After the commit, not inside the click: a panel still carrying `hidden`
   * measures as nothing, so scrolling to it from the handler scrolls nowhere.
   * `block: "nearest"` makes this a no-op whenever the panel is already in
   * view, which is the whole two-column case. */
  useEffect(() => {
    if (!reveal.current) return
    reveal.current = false
    const node = selected ? panelRefs.current[selected.id] : null
    if (!node) return
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    node.scrollIntoView({ block: "nearest", behavior: still ? "auto" : "smooth" })
  }, [selected])

  const onKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (!selected) return
    const index = ordered.findIndex((phase) => phase.id === selected.id)
    let next: RoadmapPhase | undefined
    if (event.key === "ArrowDown") {
      next = ordered[Math.min(index + 1, ordered.length - 1)]
    } else if (event.key === "ArrowUp") {
      next = ordered[Math.max(index - 1, 0)]
    } else if (event.key === "Home") {
      next = ordered[0]
    } else if (event.key === "End") {
      next = ordered[ordered.length - 1]
    }
    if (!next) return
    event.preventDefault()
    select(next, false)
    refs.current[next.id]?.focus()
  }

  if (!selected) {
    return (
      <p className="m-0 text-sm text-muted-foreground">
        No roadmap phases configured.
      </p>
    )
  }

  /* Accent up to the release in progress. With none in progress the line runs
   * accent through the last shipped release, so a plan that is half done and
   * paused still reads as half done. */
  const activeIndex = ordered.findIndex((phase) => phase.status === "active")
  const progressIndex =
    activeIndex >= 0
      ? activeIndex
      : ordered.reduce(
          (last, phase, index) => (phase.status === "shipped" ? index : last),
          -1
        )
  const selectedIndex = ordered.findIndex((phase) => phase.id === selected.id)

  return (
    <div className="grid gap-y-7 min-[1025px]:grid-cols-[19rem_minmax(0,1fr)] min-[1025px]:items-start min-[1025px]:gap-x-10 min-[1025px]:gap-y-0">
      <div
        role="tablist"
        aria-label={label}
        aria-orientation="vertical"
        onKeyDown={onKeyDown}
        className="relative min-w-0"
      >
        {/* One marker for the whole list, riding the rungs. Geometry is the
            row's: the rail is `w-4` plus the fill's `ml-2`, so the marker
            starts at 24px; the fill is a 20px line box inside `py-1.5`, so it
            is 32px tall and sits 6px down in a 44px row. It is first in DOM so
            the rows, which are `relative`, paint over it. */}
        <span
          aria-hidden="true"
          style={{ transform: `translateY(calc(${selectedIndex} * ${ROW_PITCH}))` }}
          className={cn(
            "pointer-events-none absolute top-1.5 right-0 left-6 h-8 rounded-md bg-muted",
            armed &&
              "transition-transform duration-[180ms] ease-[cubic-bezier(0.32,0.72,0,1)] motion-reduce:transition-none"
          )}
        />

        {ordered.map((phase, index) => (
          <ReleaseRow
            key={phase.id}
            phase={phase}
            selected={phase.id === selected.id}
            first={index === 0}
            last={index === ordered.length - 1}
            aboveDone={index <= progressIndex}
            belowDone={index < progressIndex}
            id={tabId(phase.id)}
            panelId={panelId(phase.id)}
            onSelect={() => select(phase, true)}
            buttonRef={(node) => {
              refs.current[phase.id] = node
            }}
          />
        ))}
      </div>

      {/* Every release, always in the markup; all but one carry `hidden`. The
          grid puts them in one cell, so the column is as tall as the tallest
          release in this card and never resizes under the reader. */}
      <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] border-t border-border pt-6 min-[1025px]:border-t-0 min-[1025px]:border-l min-[1025px]:pt-0 min-[1025px]:pl-10">
        {ordered.map((phase) => (
          <div
            key={phase.id}
            id={panelId(phase.id)}
            ref={(node) => {
              panelRefs.current[phase.id] = node
            }}
            role="tabpanel"
            aria-labelledby={tabId(phase.id)}
            hidden={phase.id !== selected.id}
            /* The pane holds no focusable element of its own, so it takes a
               stop itself or its contents are unreachable by keyboard. */
            tabIndex={phase.id === selected.id ? 0 : -1}
            className={cn("folio-roadmap-panel min-w-0", FOCUS_RING)}
          >
            <ReleaseDetail phase={phase} />
          </div>
        ))}
      </div>
    </div>
  )
}
