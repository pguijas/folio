/** The two products the cover splits into. Hrefs are written root-relative
 * ("/folio-docs/"); the switcher runs each one through normalizeLandingHref
 * with the depth of the page it is rendering on, so the same string resolves
 * from the root cover and from a product landing one route below it. */
export type FolioProductId = "docs" | "agents"

export interface FolioProduct {
  id: FolioProductId
  /** Short form, for a switcher that already sits beside the wordmark. */
  label: string
  /** Full form, for anywhere the word "Folio" is not already on screen. */
  name: string
  /** One line on what the product is, for switchers that have room for it.
   * Kept short enough to sit on a single line in the switcher panel; a blurb
   * that wraps turns a scannable list into a paragraph. */
  blurb: string
  /** Null while the product has no landing to cross to. Independent of
   * `state`: a product can have a page that says it is not finished. */
  href: string | null
  /** Whether the product itself is shipped, which is a different question
   * from whether it has a page. */
  state: "available" | "soon"
}

export const FOLIO_PRODUCTS: FolioProduct[] = [
  {
    id: "docs",
    label: "Docs",
    name: "Folio Docs",
    blurb: "A site built from your source and guides.",
    href: "/folio-docs/",
    state: "available",
  },
  {
    id: "agents",
    label: "Agents",
    name: "Folio for Agents",
    blurb: "A place in the repository for everything a session makes.",
    href: "/folio-agents/",
    /* 0.1.0 ships independently as `folio-agents` and `folio board` runs in a
       checkout today, so this is no longer "soon". The landing it points at
       opens on 0.1 and counts what is stored; a Soon chip over that was the
       switcher contradicting the page under it.

       The blurb names the store rather than the board on purpose: the board is
       one thing kept under the convention and one way of reading it back, and
       "a board of Markdown files in git" was the smallest true thing we could
       have said about the product. */
    state: "available",
  },
]
