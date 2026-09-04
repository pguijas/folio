"use client"

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react"
import { ArrowDown01Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"

import {
  FOLIO_PRODUCTS,
  type FolioProduct,
  type FolioProductId,
} from "@/components/folio-products"
import { normalizeLandingHref } from "@/components/landing/actions"
import { cn } from "@/lib/utils"

/** The only marker a row carries on its right: the quiet mono chip for a
 * product with no landing yet. The product you are already on is marked by
 * the accent rule down the row's left edge instead, so "where you are" and
 * "where you cannot go" never share a signal. The chip's reason is in text,
 * so `aria-disabled` is never the only thing a screen reader gets. */
function RowMarker({ product }: { product: FolioProduct }) {
  if (product.state !== "soon") {
    return null
  }

  return (
    <>
      {/* The chip is the visual signal and the sentence beside it is the
          spoken one. They are separate elements because an `sr-only` span
          nested inside an `aria-hidden` chip would be hidden along with it,
          which is how a state ends up conveyed by colour alone. */}
      <span
        aria-hidden="true"
        className="shrink-0 font-mono text-[11px] tracking-wide text-muted-foreground uppercase"
      >
        Soon
      </span>
      <span className="sr-only">, coming soon</span>
    </>
  )
}

function RowBody({ product }: { product: FolioProduct }) {
  return (
    <>
      <span className="flex items-baseline gap-2">
        <span className="min-w-0 flex-1 truncate text-sm font-medium">
          {product.name}
        </span>
        <RowMarker product={product} />
      </span>
      {/* The blurb is the whole point of this treatment — the panel is the
          one place with room to say what each product is. The panel is sized
          so these sit on one line; a wrapping blurb turns a list you scan
          into a paragraph you read. */}
      <span className="mt-1 block text-xs leading-snug text-muted-foreground">
        {product.blurb}
      </span>
    </>
  )
}

export function FolioProductSwitcher({
  current,
  pathToRoot,
}: {
  current: FolioProductId
  /** Relative path from the page carrying the switcher back to the site root
   * — "." on the cover, ".." on a product landing. The product hrefs are
   * root-relative, so without it a landing links one level too deep. */
  pathToRoot?: string
}) {
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const itemRefs = useRef<(HTMLElement | null)[]>([])
  const menuId = useId()

  const lastIndex = FOLIO_PRODUCTS.length - 1
  const currentIndex = Math.max(
    FOLIO_PRODUCTS.findIndex((product) => product.id === current),
    0
  )
  const currentProduct = FOLIO_PRODUCTS[currentIndex]

  /* One place moves focus: whichever row `activeIndex` points at owns it for
     as long as the menu is open. Arrow keys only move the index. */
  useEffect(() => {
    if (!open) {
      return
    }
    itemRefs.current[activeIndex]?.focus({ preventScroll: true })
  }, [open, activeIndex])

  useEffect(() => {
    if (!open) {
      return
    }
    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("pointerdown", handlePointerDown)
    return () => document.removeEventListener("pointerdown", handlePointerDown)
  }, [open])

  const openAt = useCallback((index: number) => {
    setActiveIndex(index)
    setOpen(true)
  }, [])

  const closeToTrigger = useCallback(() => {
    setOpen(false)
    triggerRef.current?.focus()
  }, [])

  const handleKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Escape") {
        if (!open) {
          return
        }
        event.preventDefault()
        closeToTrigger()
        return
      }

      /* Tab out of an open menu closes it. Focus lands on the trigger
         first, synchronously, so the browser's own Tab then continues from
         the switcher's place in the bar rather than from the document top. */
      if (event.key === "Tab") {
        if (open) {
          closeToTrigger()
        }
        return
      }

      if (event.key === "ArrowDown") {
        event.preventDefault()
        if (open) {
          setActiveIndex((index) => (index >= lastIndex ? 0 : index + 1))
        } else {
          openAt(currentIndex)
        }
        return
      }

      if (event.key === "ArrowUp") {
        event.preventDefault()
        if (open) {
          setActiveIndex((index) => (index <= 0 ? lastIndex : index - 1))
        } else {
          openAt(lastIndex)
        }
        return
      }

      if (!open) {
        return
      }

      /* Enter and Space activate the focused row. The browser already does
         Enter on a link; Space it does not, and left alone Space scrolls the
         page behind an open menu. An inert row has nothing to activate, so
         the key dismisses rather than dying under the finger. */
      if (event.key === "Enter" || event.key === " ") {
        const row = event.target
        if (row instanceof HTMLAnchorElement) {
          if (event.key === " ") {
            event.preventDefault()
            row.click()
          }
          return
        }
        event.preventDefault()
        closeToTrigger()
        return
      }

      if (event.key === "Home") {
        event.preventDefault()
        setActiveIndex(0)
      } else if (event.key === "End") {
        event.preventDefault()
        setActiveIndex(lastIndex)
      }
    },
    [closeToTrigger, currentIndex, lastIndex, open, openAt]
  )

  return (
    /* `h-16` matches the bar's own fixed height, so this cannot make the
       header taller — it only gives the panel a `top-full` that lands exactly
       on the header's bottom border, letting the two hairlines merge. */
    <div
      ref={rootRef}
      onKeyDown={handleKeyDown}
      /* Pulled back against the group's `gap-3` so the divider sits close to
         the wordmark: the header should read as one path into the product,
         "Folio / Docs", not as a wordmark with a control parked beside it. */
      className="relative -ml-1.5 flex h-16 shrink-0 items-center gap-1.5"
    >
      {/* Hidden along with the label below `sm`, where the trigger is the
          chevron alone and a divider would point at nothing. */}
      <span
        aria-hidden="true"
        className="hidden text-sm text-border select-none sm:inline"
      >
        /
      </span>
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        aria-label={`Switch product, currently ${currentProduct.name}`}
        onClick={() => (open ? setOpen(false) : openAt(currentIndex))}
        className={cn(
          /* `h-8` rather than the navbar's `py-1.5`: with the label hidden
             below `sm` the padding alone would leave a 24px control in a bar
             where everything else is 32px. At `sm` and up the two agree. */
          "flex h-8 shrink-0 items-center gap-1.5 rounded-md px-1.5 text-sm font-medium text-foreground transition-colors sm:px-2",
          "hover:bg-muted",
          /* An outline, not a `ring`. Tailwind draws rings as box-shadows and
             forced-colors mode drops box-shadows, so `ring-2` paired with
             `outline-none` (which is `outline-style: none` in v4) would leave
             the trigger with no focus indicator at all in high contrast. Same
             `ring` token, and the idiom the theme's other controls use. */
          "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
          /* Measured at 375px against the full bar — monogram, wordmark,
             Documentation, GitHub, theme toggle — the label does not fit, so
             below `sm` the trigger drops to the chevron alone. It then reads
             as a disclosure on the wordmark rather than a control of its own,
             which is the treatment's whole idea, and the accessible name
             still carries the product. */
          open && "bg-muted"
        )}
      >
        <span className="hidden sm:inline">{currentProduct.label}</span>
        <HugeiconsIcon
          icon={ArrowDown01Icon}
          size={12}
          strokeWidth={2}
          /* Turns to face the open panel, so the trigger says whether the
             menu is down without relying on the panel being in view. */
          className={cn(
            "size-3 shrink-0 text-muted-foreground transition-transform duration-150 motion-reduce:transition-none",
            open && "rotate-180"
          )}
          aria-hidden="true"
        />
      </button>

      {open ? (
        <div
          id={menuId}
          role="menu"
          aria-label="Switch product"
          aria-orientation="vertical"
          className={cn(
            "animate-in duration-150 fade-in-0 slide-in-from-top-1 motion-reduce:animate-none",
            /* Phones: a full-bleed sheet flush under the bar. A card anchored
               to the trigger would start ~106px in and run past a 375px
               viewport, so it spans instead and the rows take the header's
               own `px-6` gutter. */
            "fixed inset-x-0 top-16 border-y border-border bg-background",
            /* sm and up: the card hangs off the wordmark, wide enough that
               every blurb sits on one line. Only the bottom corners round —
               the top edge is meant to merge into the header's own hairline,
               and rounding it would peel the panel off the bar. */
            "sm:absolute sm:inset-x-auto sm:top-full sm:left-0 sm:w-80 sm:rounded-b-md sm:border-x"
          )}
        >
          {FOLIO_PRODUCTS.map((product, index) => {
            const isCurrent = product.id === currentProduct.id
            /* Crossable is a question about the page, not about the product.
               An unfinished product with a landing is a link that still
               carries its Soon mark; the mark describes what you will find
               when you get there. */
            const href = product.href
              ? normalizeLandingHref(product.href, pathToRoot)
              : null
            const rowClassName = cn(
              /* The accent rule down the left edge is what marks the product
                 you are on. Every row reserves the 2px so no row shifts when
                 the marked one changes, and the padding compensates for it. */
              "block border-l-2 py-3 pr-6 pl-[calc(1.5rem-2px)] sm:pr-3 sm:pl-[calc(0.875rem-2px)]",
              isCurrent ? "border-primary" : "border-transparent",
              /* Offset inwards: a row runs the full width of the panel, so a
                 positive offset would draw the indicator outside the panel's
                 own border. Arrowing through the rows is marked by this
                 outline alone — filling the active row would put the hover
                 token on the row you are on at the same time as on the row
                 under the pointer, and two filled rows say two things. */
              "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
            )
            const setItemRef = (node: HTMLElement | null) => {
              itemRefs.current[index] = node
            }
            /* Keeps the highlight and the focus ring on the same row when
               focus arrives from somewhere other than an arrow key — a mouse
               click on a row lands on a `tabIndex` element and focuses it,
               and without this the fill would stay behind on the old one. */
            const syncActive = () => setActiveIndex(index)

            if (href && !isCurrent) {
              return (
                <a
                  key={product.id}
                  ref={setItemRef}
                  href={href}
                  role="menuitem"
                  tabIndex={index === activeIndex ? 0 : -1}
                  onFocus={syncActive}
                  onClick={() => setOpen(false)}
                  className={cn(
                    rowClassName,
                    "text-foreground transition-colors hover:bg-muted"
                  )}
                >
                  <RowBody product={product} />
                </a>
              )
            }

            /* Both inert cases: the product you are on, and one with no
               landing to cross to. Neither is a link and neither takes a
               hover fill, so nothing here looks clickable. */
            return (
              <div
                key={product.id}
                ref={setItemRef}
                role="menuitem"
                /* Only the unreachable product is disabled. The current one is
                   inert for a different reason and `aria-current` already says
                   which; marking it disabled as well would let a reader set to
                   skip disabled items lose the one row that says where it is,
                   and would announce the page you are on as withheld. */
                aria-disabled={isCurrent ? undefined : true}
                aria-current={isCurrent ? "page" : undefined}
                tabIndex={index === activeIndex ? 0 : -1}
                onFocus={syncActive}
                className={cn(
                  rowClassName,
                  isCurrent ? "text-foreground" : "text-muted-foreground"
                )}
              >
                <RowBody product={product} />
              </div>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
