"use client"

import { useCallback, useEffect, useState } from "react"

import type { RoadmapGroup } from "@/lib/roadmap-utils"
import { RoadmapProjectCard } from "@/components/roadmap-project-card"

/* The stack of product cards, and which of them are open.
 *
 * Both are open by default, which is what the server renders and therefore
 * what a reader with no JavaScript gets: the whole roadmap, both products.
 * `?product=<key>` narrows that to one — the link the product landings use, so
 * arriving from Folio for Agents opens on Folio for Agents instead of on
 * whichever product happens to be declared first.
 *
 * Collapsing is a `<details>`, so the releases stay in the DOM either way. A
 * closed card hides its content; it does not drop it, and a crawler or an
 * agent reading the HTML still finds every release.
 *
 * The open set lives here rather than in each card because the fragment
 * describes the page: one card open is `?product=docs`, more than one is no
 * parameter at all. A card cannot decide that alone.
 */

/** The query key the landings link with. Exported because the page emits a
 *  pre-paint script that reads the same key, and two spellings of it would be
 *  a bug nobody notices until the collapse flashes. */
export const ROADMAP_PRODUCT_PARAM = "product"

export function RoadmapCards({
  groups,
  named,
}: {
  groups: RoadmapGroup[]
  /** Keys the site actually named in docs.yaml. A card for a project with no
   *  configured label draws no heading, so it has nothing to collapse into
   *  and stays open. */
  named: string[]
}) {
  /* `null` is "every card open" — the server's answer, and the one the first
   * paint has to match. Reading the query synchronously here instead would
   * render one thing on the server and another in the browser. */
  const [open, setOpen] = useState<string[] | null>(null)

  useEffect(() => {
    const wanted = new URLSearchParams(window.location.search).get(ROADMAP_PRODUCT_PARAM)
    if (!wanted) return
    /* A key the roadmap does not have names no card, and collapsing every
       card over a typo would leave the page blank. */
    if (!groups.some((group) => group.key === wanted)) return
    /* Synchronous by design: this is the one-time handover from the URL (an
       external system the server cannot read) to client state, and it must
       land before the pre-paint stylesheet is dropped below. */
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOpen([wanted])
  }, [groups])

  /* Hand over from the pre-paint stylesheet, one commit late.
   *
   * The page ships a rule that hides the other cards before React runs, keyed
   * off an attribute on <html>. Dropping that attribute in the effect above
   * would run it synchronously, before the state it just scheduled has
   * committed — the CSS would stop hiding the card while React still had it
   * open, and both would flash. Waiting for `open` to stop being null is
   * waiting for exactly that commit. */
  useEffect(() => {
    if (open === null) return
    document.documentElement.removeAttribute("data-roadmap-product")
  }, [open])

  const isOpen = useCallback(
    (key: string) => open === null || open.includes(key),
    [open]
  )

  const toggle = useCallback(
    (key: string) => {
      const current = open ?? groups.map((group) => group.key)
      const next = current.includes(key)
        ? current.filter((k) => k !== key)
        : [...current, key]
      setOpen(next)

      /* The parameter only says something when it says "this one": exactly
         one card open is a link worth having, and any other state is the
         page's default. `replaceState` because collapsing a card is not a
         place a reader should have to press Back out of. */
      const url = new URL(window.location.href)
      if (next.length === 1) url.searchParams.set(ROADMAP_PRODUCT_PARAM, next[0])
      else url.searchParams.delete(ROADMAP_PRODUCT_PARAM)
      window.history.replaceState(null, "", url.pathname + url.search + url.hash)
    },
    [groups, open]
  )

  return (
    <div className="flex flex-col gap-4">
      {groups.map((group) => (
        <RoadmapProjectCard
          key={group.key}
          group={group}
          named={named.includes(group.key)}
          open={isOpen(group.key)}
          onToggle={() => toggle(group.key)}
        />
      ))}
    </div>
  )
}
