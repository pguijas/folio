// Nextra's DOM, as the template's components find it.
//
// nextra-theme-docs exposes no API for the parts of its layout the template
// enhances: the mobile menu the drawer takes over, the hamburger that opens
// it, the search results shown over it, the code blocks previews detect.
// Components reach them by the class names Nextra renders, and those names
// are private to Nextra and can change in any release. So every lookup
// lives here, in one module, and `e2e_export` asserts each class below, the
// portal root's id and the breakpoint still ship in a built site: a Nextra
// upgrade that renames one fails that test rather than silently dropping a
// feature. CSS that styles these classes (globals.css, the theme
// configurator's shell CSS) mostly degrades to Nextra's look instead of
// breaking, which is why it is not routed through here. The exceptions are
// `.nextra-search-results`, which globals.css raises over the open drawer:
// renamed, the search in the drawer would show its results under the panel,
// which is why it is listed below as well; and the few Nextra utility
// classes the styles select on, which `e2e_export` checks on its own.

export { setMenu, useMenu } from "nextra-theme-docs"

export const NEXTRA_CLASS = {
  code: "nextra-code",
  hamburger: "nextra-hamburger",
  mobileNav: "nextra-mobile-nav",
  searchResults: "nextra-search-results",
} as const

/**
 * The node headless-ui, which runs Nextra's search box, portals the search
 * results into, a child of `<body>` while they show.
 */
export const HEADLESS_PORTAL_ROOT_ID = "headlessui-portal-root"

/**
 * Nextra's `md` breakpoint, past which the mobile menu gives way to the
 * sidebar. The query is Nextra's own, in rem, so a larger default font moves
 * both.
 */
export const NEXTRA_DESKTOP_QUERY = "(width >= 48rem)"

function findByClass(name: string): HTMLElement | null {
  const element = document.querySelector(`.${name}`)
  return element instanceof HTMLElement ? element : null
}

/** The `<aside>` Nextra shows as the menu below the `md` breakpoint. */
export function findMobileNav() {
  return findByClass(NEXTRA_CLASS.mobileNav)
}

/** The navbar button that toggles the mobile menu. */
export function findHamburger() {
  return findByClass(NEXTRA_CLASS.hamburger)
}

/**
 * Whether the search is open with nothing to show. An emptied query leaves
 * the combobox open, and its results list in the page, empty and invisible.
 */
export function searchShowsNothing() {
  return document.querySelector(`.${NEXTRA_CLASS.searchResults}:empty`) !== null
}

/** Whether a `className` prop marks a code block Nextra rendered. */
export function isNextraCodeClassName(className: unknown) {
  return (
    typeof className === "string" &&
    new RegExp(`(?:^|\\s)${NEXTRA_CLASS.code}(?:\\s|$)`).test(className)
  )
}
