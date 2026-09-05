"use client"

import { useEffect, useRef, type ComponentType } from "react"

import { AgentsAnimation } from "./agents-artifact-kinds"
import { DocsAnimation } from "./docs-build-pulse"
import { FOLIO_PRODUCTS, type FolioProductId } from "./folio-products"
import styles from "./folio-prelanding.module.css"

type AnimationScope = {
  revert: () => void
}

/** Which drawing goes inside which product's frame. Keyed by product id so a
 *  product added to FOLIO_PRODUCTS without a drawing fails the type check
 *  here instead of rendering an empty frame. */
const PRODUCT_PAGES: Record<
  FolioProductId,
  { Animation: ComponentType; pageClassName: string }
> = {
  docs: { Animation: DocsAnimation, pageClassName: styles.docsPage },
  agents: { Animation: AgentsAnimation, pageClassName: styles.agentsPage },
}

export function FolioPrelanding() {
  const root = useRef<HTMLElement>(null)

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return
    }

    let cancelled = false
    let scope: AnimationScope | undefined

    void import("animejs").then(({ animate, createScope, stagger }) => {
      if (cancelled || !root.current) {
        return
      }

      scope = createScope({ root }).add(() => {
        animate("[data-page]", {
          scaleX: { from: 0 },
          opacity: { from: 0 },
          duration: 860,
          delay: stagger(90),
          ease: "out(4)",
        })
        animate("[data-inside]", {
          opacity: { from: 0 },
          y: { from: 8 },
          duration: 520,
          delay: stagger(55, { start: 520 }),
          ease: "out(3)",
        })
      })
    })

    return () => {
      cancelled = true
      scope?.revert()
    }
  }, [])

  /* Each product is one cell: its drawing with its name directly under it.
   * They used to live in two separate rows — all drawings, then all names —
   * which reads fine side by side but falls apart when a phone stacks the
   * rows: two screens of unlabeled wireframe, with both names orphaned at
   * the bottom.
   *
   * Names and states are read from FOLIO_PRODUCTS, which is also what the
   * product switcher renders one route below this page. They were two
   * hardcoded strings until they disagreed: Folio for Agents shipped
   * 0.1.0 and the switcher stopped saying "soon" while this cover went
   * on saying "Coming soon" about the same product. One source now, so
   * they cannot drift again. */
  return (
    <section ref={root} className={styles.cover} aria-label="Folio products">
      {/* A plain div, not a <nav>: the animation figures carry their own
          long descriptions, and parking those inside a navigation landmark
          makes a screen reader wade through both drawings to reach two
          links. The section label plus two self-naming links carry it. */}
      <div className={styles.content}>
        {FOLIO_PRODUCTS.map((product) => {
          const { Animation, pageClassName } = PRODUCT_PAGES[product.id]
          return (
            <div key={product.id} className={styles.product}>
              <div data-page className={`${styles.page} ${pageClassName}`}>
                <Animation />
              </div>
              <a
                data-inside
                href={`.${product.href}`}
                className={styles.choice}
              >
                <span className={styles.choiceName}>
                  {product.name}
                  <span aria-hidden="true"> ↗</span>
                </span>
                <span className={styles.choiceState}>
                  {product.state === "available" ? "Available" : "Coming soon"}
                </span>
              </a>
            </div>
          )
        })}
      </div>
    </section>
  )
}
