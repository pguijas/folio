"use client"

import {
  type MouseEvent,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useSyncExternalStore,
} from "react"
import { createPortal } from "react-dom"
import { HugeiconsIcon } from "@hugeicons/react"
import { Cancel01Icon } from "@hugeicons/core-free-icons"
import { folioProject } from "@/lib/folio-template"
import {
  findHamburger,
  findMobileNav,
  HEADLESS_PORTAL_ROOT_ID,
  NEXTRA_DESKTOP_QUERY,
  searchShowsNothing,
  setMenu,
  useMenu,
} from "@/lib/nextra-dom"

// Nextra's mobile menu, made a modal drawer.
//
// Nextra renders the menu as a full-screen <aside> it slides down from the
// top, with no dialog role, no Esc and no focus handling. This component keeps
// Nextra's aside, its open state (`useMenu`) and its own closing on a link
// click or a route change, and adds what a modal needs: a title and a close
// button, a scrim, Esc, focus kept inside while open and given back on close,
// and the rest of the page inert. The geometry and the motion are CSS in
// globals.css, keyed off `html[data-folio-drawer]`; without this component
// mounted, the menu stays exactly as Nextra draws it.
//
// The drawer's look is taken from cojeev's docs drawer (MIT), itself derived
// from ui-layouts (MIT); see THIRD-PARTY-NOTICES.md.

const PANEL_ID = "folio-mobile-nav"
const SCRIM_CLASS = "folio-drawer-scrim"

// Body children the open drawer leaves live. Next's route announcer and any
// live region must still speak, headless-ui's portal root holds the results
// of the search box inside the drawer, and scripts and styles are not UI.
const STAYS_LIVE = `script, style, template, next-route-announcer, #${HEADLESS_PORTAL_ROOT_ID}, [aria-live]`

const TABBABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "summary",
  "[tabindex]:not([tabindex='-1'])",
].join(", ")

type ReturnFocus = "hamburger" | "destination"

// `checkVisibility` arrived in Safari 17.4; before it, a box and a visible
// computed style tell the same for the tab order.
function isShown(element: HTMLElement) {
  if (typeof element.checkVisibility === "function") {
    return element.checkVisibility({ checkVisibilityCSS: true, visibilityProperty: true })
  }
  return element.getClientRects().length > 0 && getComputedStyle(element).visibility === "visible"
}

function tabbables(panel: HTMLElement) {
  return Array.from(panel.querySelectorAll<HTMLElement>(TABBABLE)).filter(
    (element) => element.tabIndex >= 0 && !element.closest("[inert]") && isShown(element)
  )
}

function hashTarget() {
  try {
    return document.getElementById(decodeURIComponent(location.hash.slice(1)))
  } catch {
    return null
  }
}

// Where focus goes when a route change closes the drawer: the section a hash
// link points at, so the next Tab carries on from there, or else the page the
// reader just chose. Either is a place to land, not a control: it takes
// focus without a ring and drops the tabindex once focus moves on.
// `preventScroll`, so the page stays where the navigation put it.
function focusDestination() {
  const target = hashTarget() ?? document.getElementById("main-content")
  if (!target) return
  if (!target.hasAttribute("tabindex")) {
    target.tabIndex = -1
    target.dataset.folioFocusTarget = ""
    target.addEventListener(
      "blur",
      () => {
        target.removeAttribute("tabindex")
        delete target.dataset.folioFocusTarget
      },
      { once: true }
    )
  }
  target.focus({ preventScroll: true })
}

// Nextra's layout renders the menu before this component hydrates and keeps
// it for the life of the layout, so the lookup has nothing to subscribe to.
// The server has no menu, which keeps the first render empty for hydration.
function subscribeToNothing() {
  return () => {}
}

function noMenuOnTheServer() {
  return null
}

export function MobileNavDrawer() {
  const open = useMenu()
  const titleId = useId()
  const panel = useSyncExternalStore(
    subscribeToNothing,
    findMobileNav,
    noMenuOnTheServer
  )
  // The slot the title and the close button portal into, first in the panel
  // so they come first in the tab order too.
  const header = useMemo(() => {
    if (!panel) return null
    const slot = document.createElement("div")
    slot.className = "folio-drawer-header"
    return slot
  }, [panel])
  // Esc, the scrim and the close button give focus back to the hamburger;
  // anything else that closes the drawer is a navigation, which focuses where
  // it led.
  const returnFocus = useRef<ReturnFocus>("destination")
  const wasOpen = useRef(false)
  // What the open drawer made inert, kept across the closing so the page is
  // given back after the closing's first frame, not before it.
  const inerted = useRef<HTMLElement[]>([])

  function close(returnTo: ReturnFocus) {
    returnFocus.current = returnTo
    setMenu(false)
  }

  // A press on the close button or the scrim would move focus there, or to
  // the body, before the closing's first frame; the focus goes back to the
  // hamburger after it instead, so the press leaves it where it is.
  function keepFocus(event: MouseEvent) {
    event.preventDefault()
  }

  useLayoutEffect(() => {
    if (!panel || !header) return

    panel.prepend(header)
    if (!panel.id) panel.setAttribute("id", PANEL_ID)
    panel.setAttribute("role", "dialog")
    panel.setAttribute("aria-modal", "true")
    panel.setAttribute("aria-labelledby", titleId)
    panel.setAttribute("tabindex", "-1")

    return () => {
      header.remove()
      // Unmounted open, or mid-closing: nothing else will give the page back.
      for (const element of inerted.current) element.inert = false
      inerted.current = []
      panel.removeAttribute("inert")
      delete document.documentElement.dataset.folioDrawer
      delete document.documentElement.dataset.folioDrawerMotion
    }
  }, [panel, header, titleId])

  useLayoutEffect(() => {
    if (!panel) return
    const root = document.documentElement
    const hamburger = findHamburger()

    // Transitions start with the first open. Set any earlier, the swap from
    // Nextra's slide-down position to the drawer's would itself animate
    // across the screen on page load.
    if (open) root.dataset.folioDrawerMotion = ""
    root.dataset.folioDrawer = open ? "open" : "closed"
    // The panel is live from the opening's first frame, whose visibility flip
    // restyles it anyway. The closing leaves it inert once focus is out.
    if (open) panel.removeAttribute("inert")
    hamburger?.setAttribute("aria-expanded", String(open))
    hamburger?.setAttribute("aria-controls", panel.id)
    if (!open && !wasOpen.current) return
    wasOpen.current = open

    // Focus moves, and the page goes inert or live again, once the first
    // frame of the opening or the closing has painted. Each restyles the whole
    // page (a focus change does through Nextra's `html:not(:has(*:focus))`),
    // and done before that frame they held the drawer back. The scrim takes
    // any tap in between, and the keydown below already keeps Tab inside.
    // Focus given back here, and not in a cleanup, also outlasts React, which
    // restores the focus it saw before a commit once the cleanups have run.
    let afterPaint = 0
    const frame = requestAnimationFrame(() => {
      afterPaint = window.setTimeout(() => {
        if (!open) {
          for (const element of inerted.current) element.inert = false
          inerted.current = []
          if (returnFocus.current === "hamburger") {
            hamburger?.focus({ preventScroll: true })
          } else {
            focusDestination()
          }
          // Still on screen while it slides out, the panel would otherwise
          // take the next Tab, and screen readers would find it beside the
          // page.
          panel.setAttribute("inert", "")
          return
        }
        // A page still inert from a closing cut short keeps its list; an
        // element made inert by someone else is left to them.
        for (const element of document.body.children) {
          if (
            element instanceof HTMLElement &&
            element !== panel &&
            !element.classList.contains(SCRIM_CLASS) &&
            !element.matches(STAYS_LIVE) &&
            !element.inert
          ) {
            element.inert = true
            inerted.current.push(element)
          }
        }
        panel.focus({ preventScroll: true })
      })
    })
    const cancelAfterPaint = () => {
      cancelAnimationFrame(frame)
      clearTimeout(afterPaint)
    }
    if (!open) return cancelAfterPaint
    returnFocus.current = "destination"

    // Esc is left to a layer inside the drawer that claims it, except the
    // search when an emptied query has left it open with nothing to show:
    // the drawer then closes with it, rather than on a second Esc.
    let searchWasEmpty = false
    const beforeEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") searchWasEmpty = searchShowsNothing()
    }
    const keepFocusInside = (event: KeyboardEvent) => {
      if (event.key === "Escape" && (!event.defaultPrevented || searchWasEmpty)) {
        event.preventDefault()
        returnFocus.current = "hamburger"
        setMenu(false)
        return
      }
      if (event.key !== "Tab" || event.defaultPrevented) return

      const items = tabbables(panel)
      const active = document.activeElement
      const first = items[0]
      const last = items[items.length - 1]
      if (!first || !last) {
        event.preventDefault()
        panel.focus()
      } else if (!(active instanceof Node) || !panel.contains(active)) {
        event.preventDefault()
        ;(event.shiftKey ? last : first).focus()
      } else if (event.shiftKey && (active === first || active === panel)) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && active === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener("keydown", beforeEscape, true)
    document.addEventListener("keydown", keepFocusInside)

    return () => {
      cancelAfterPaint()
      document.removeEventListener("keydown", beforeEscape, true)
      document.removeEventListener("keydown", keepFocusInside)
    }
  }, [open, panel])

  // The drawer is a phone layout. Widening the window past Nextra's `md`
  // breakpoint hides the aside, so it closes rather than reopening later.
  useEffect(() => {
    const desktop = window.matchMedia(NEXTRA_DESKTOP_QUERY)
    function closeOnDesktop() {
      if (desktop.matches) setMenu(false)
    }
    desktop.addEventListener("change", closeOnDesktop)
    return () => desktop.removeEventListener("change", closeOnDesktop)
  }, [])

  if (!panel || !header) return null

  return (
    <>
      {createPortal(
        <>
          <h2 id={titleId} className="folio-drawer-title">
            {folioProject.name}
          </h2>
          <button
            type="button"
            className="folio-drawer-close"
            aria-label="Close menu"
            onMouseDown={keepFocus}
            onClick={() => close("hamburger")}
          >
            <HugeiconsIcon
              icon={Cancel01Icon}
              size={20}
              strokeWidth={1.8}
              aria-hidden="true"
            />
          </button>
        </>,
        header
      )}
      {createPortal(
        <div
          className={SCRIM_CLASS}
          aria-hidden="true"
          onMouseDown={keepFocus}
          onClick={() => close("hamburger")}
        />,
        document.body
      )}
    </>
  )
}
