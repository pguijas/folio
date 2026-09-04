"use client"

import { Fragment, useEffect, useRef } from "react"

import { AgentsAnimation } from "./agents-artifact-kinds"
import { DocsAnimation } from "./docs-build-pulse"
import { FOLIO_PRODUCTS } from "./folio-products"
import styles from "./folio-prelanding.module.css"

type AnimationScope = {
  revert: () => void
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

  return (
    <section ref={root} className={styles.cover} aria-label="Folio products">
      <div className={styles.content}>
        <div className={styles.folio} aria-label="Inside the two Folio products">
          <div data-page className={`${styles.page} ${styles.docsPage}`}>
            <DocsAnimation />
          </div>

          <div data-page className={`${styles.page} ${styles.agentsPage}`}>
            <AgentsAnimation />
          </div>
        </div>

        {/* Both states are read from FOLIO_PRODUCTS, which is also what the
            product switcher renders one route below this page. They were two
            hardcoded strings until they disagreed: Folio for Agents shipped
            0.1.0 and the switcher stopped saying "soon" while this cover went
            on saying "Coming soon" about the same product. One source now, so
            they cannot drift again. */}
        <nav data-inside className={styles.choices} aria-label="Choose a product">
          {FOLIO_PRODUCTS.map((product, index) => (
            <Fragment key={product.id}>
              {index > 0 ? (
                <span className={styles.choiceRule} aria-hidden="true" />
              ) : null}
              <a
                href={`.${product.href}`}
                className={`${styles.choice} ${styles.docsChoice}`}
              >
                <span className={styles.choiceName}>{product.name} ↗</span>
                <span className={styles.choiceState}>
                  {product.state === "available" ? "Available" : "Coming soon"}
                </span>
              </a>
            </Fragment>
          ))}
        </nav>
      </div>
    </section>
  )
}
