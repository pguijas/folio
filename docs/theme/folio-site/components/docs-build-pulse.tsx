"use client"

import { useEffect, useRef } from "react"

import styles from "./docs-build-pulse.module.css"

type AnimationScope = {
  revert: () => void
}

export function DocsAnimation() {
  const root = useRef<HTMLElement>(null)

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return
    }

    let cancelled = false
    let scope: AnimationScope | undefined

    void import("animejs").then(
      ({ createScope, createTimeline, stagger, steps, utils }) => {
        if (cancelled || !root.current) {
          return
        }

        scope = createScope({ root }).add(() => {
          utils.set("[data-bar]", { scaleX: 0 })
          utils.set("[data-glow]", { scaleX: 0, opacity: 0 })
          utils.set("[data-panel]", { opacity: 0 })

          createTimeline()
            .add(
              "[data-bar='nav']",
              {
                scaleX: [0, 1],
                duration: 420,
                delay: stagger(150),
                ease: "out(3)",
              },
              0,
            )
            .add(
              "[data-bar='eyebrow']",
              { scaleX: [0, 1], duration: 340, ease: "out(3)" },
              760,
            )
            .add(
              "[data-glow='eyebrow']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              760,
            )
            .add(
              "[data-glow='eyebrow']",
              { scaleX: [0, 1], duration: 340, ease: "out(3)" },
              760,
            )
            .add(
              "[data-glow='eyebrow']",
              { opacity: [1, 0], duration: 420, ease: "inOutSine" },
              1180,
            )
            .add(
              "[data-bar='title']",
              { scaleX: [0, 1], duration: 460, ease: "out(3)" },
              1150,
            )
            .add(
              "[data-glow='title']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              1150,
            )
            .add(
              "[data-glow='title']",
              { scaleX: [0, 1], duration: 460, ease: "out(3)" },
              1150,
            )
            .add(
              "[data-glow='title']",
              { opacity: [1, 0], duration: 460, ease: "inOutSine" },
              1690,
            )
            .add(
              "[data-bar='copy1']",
              { scaleX: [0, 1], duration: 520, ease: steps(12) },
              1800,
            )
            .add(
              "[data-glow='copy1']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              1800,
            )
            .add(
              "[data-glow='copy1']",
              { scaleX: [0, 1], duration: 520, ease: steps(12) },
              1800,
            )
            .add(
              "[data-glow='copy1']",
              { opacity: [1, 0], duration: 380, ease: "inOutSine" },
              2400,
            )
            .add(
              "[data-bar='copy2']",
              { scaleX: [0, 1], duration: 520, ease: steps(12) },
              2440,
            )
            .add(
              "[data-glow='copy2']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              2440,
            )
            .add(
              "[data-glow='copy2']",
              { scaleX: [0, 1], duration: 520, ease: steps(12) },
              2440,
            )
            .add(
              "[data-glow='copy2']",
              { opacity: [1, 0], duration: 380, ease: "inOutSine" },
              3040,
            )
            .add(
              "[data-bar='copy3']",
              { scaleX: [0, 1], duration: 520, ease: steps(12) },
              3080,
            )
            .add(
              "[data-glow='copy3']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              3080,
            )
            .add(
              "[data-glow='copy3']",
              { scaleX: [0, 1], duration: 520, ease: steps(12) },
              3080,
            )
            .add(
              "[data-glow='copy3']",
              { opacity: [1, 0], duration: 380, ease: "inOutSine" },
              3680,
            )
            .add(
              "[data-panel]",
              { opacity: [0, 1], duration: 380, ease: "inOutSine" },
              3560,
            )
            .add(
              "[data-bar='row1']",
              { scaleX: [0, 1], duration: 360, ease: "out(3)" },
              3980,
            )
            .add(
              "[data-glow='row1']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              3980,
            )
            .add(
              "[data-glow='row1']",
              { scaleX: [0, 1], duration: 360, ease: "out(3)" },
              3980,
            )
            .add(
              "[data-glow='row1']",
              { opacity: [1, 0], duration: 360, ease: "inOutSine" },
              4420,
            )
            .add(
              "[data-bar='row2']",
              { scaleX: [0, 1], duration: 360, ease: "out(3)" },
              4200,
            )
            .add(
              "[data-glow='row2']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              4200,
            )
            .add(
              "[data-glow='row2']",
              { scaleX: [0, 1], duration: 360, ease: "out(3)" },
              4200,
            )
            .add(
              "[data-glow='row2']",
              { opacity: [1, 0], duration: 360, ease: "inOutSine" },
              4640,
            )
            .add(
              "[data-bar='row3']",
              { scaleX: [0, 1], duration: 360, ease: "out(3)" },
              4420,
            )
            .add(
              "[data-glow='row3']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              4420,
            )
            .add(
              "[data-glow='row3']",
              { scaleX: [0, 1], duration: 360, ease: "out(3)" },
              4420,
            )
            .add(
              "[data-glow='row3']",
              { opacity: [1, 0], duration: 360, ease: "inOutSine" },
              4860,
            )

          /* The settled page stays up; each cycle only an accent overlay
           * redraws over one copy line, then one panel row. */
          createTimeline({ loop: true, loopDelay: 3600, delay: 6200 })
            .add(
              "[data-glow='copy2']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              0,
            )
            .add(
              "[data-glow='copy2']",
              { scaleX: [0, 1], duration: 560, ease: steps(12) },
              0,
            )
            .add(
              "[data-glow='copy2']",
              { opacity: [1, 0], duration: 520, ease: "inOutSine" },
              700,
            )
            .add(
              "[data-glow='row2']",
              { opacity: [0, 1], duration: 60, ease: "linear" },
              1900,
            )
            .add(
              "[data-glow='row2']",
              { scaleX: [0, 1], duration: 440, ease: "out(3)" },
              1900,
            )
            .add(
              "[data-glow='row2']",
              { opacity: [1, 0], duration: 480, ease: "inOutSine" },
              2420,
            )
        })
      },
    )

    return () => {
      cancelled = true
      scope?.revert()
    }
  }, [])

  return (
    <figure
      ref={root}
      data-inside
      className={styles.root}
      aria-label="A documentation page composes itself from source: navigation bars appear in sequence, a heading and copy lines draw in, a panel of rows fills, and the settled page stays live, refreshing a single line at a time"
    >
      <div className={styles.nav} aria-hidden="true">
        <span data-bar="nav" className={styles.navLine} />
        <span data-bar="nav" className={styles.navLine} />
        <span data-bar="nav" className={styles.navLine} />
        <span data-bar="nav" className={styles.navLine} />
      </div>

      <div className={styles.body} aria-hidden="true">
        <span className={styles.eyebrowStack}>
          <span data-bar="eyebrow" className={styles.eyebrow} />
          <span data-glow="eyebrow" className={styles.glow} />
        </span>

        <span className={styles.titleStack}>
          <span data-bar="title" className={styles.title} />
          <span
            data-glow="title"
            className={`${styles.glow} ${styles.titleGlow}`}
          />
        </span>

        <span className={styles.copyLines}>
          <span className={`${styles.copyStack} ${styles.copyA}`}>
            <span data-bar="copy1" className={styles.copyLine} />
            <span data-glow="copy1" className={styles.glow} />
          </span>
          <span className={`${styles.copyStack} ${styles.copyB}`}>
            <span data-bar="copy2" className={styles.copyLine} />
            <span data-glow="copy2" className={styles.glow} />
          </span>
          <span className={`${styles.copyStack} ${styles.copyC}`}>
            <span data-bar="copy3" className={styles.copyLine} />
            <span data-glow="copy3" className={styles.glow} />
          </span>
        </span>

        <div data-panel className={styles.panel}>
          <span className={`${styles.rowStack} ${styles.rowA}`}>
            <span data-bar="row1" className={styles.rowBar} />
            <span data-glow="row1" className={styles.glow} />
          </span>
          <span className={`${styles.rowStack} ${styles.rowB}`}>
            <span data-bar="row2" className={styles.rowBar} />
            <span data-glow="row2" className={styles.glow} />
          </span>
          <span className={`${styles.rowStack} ${styles.rowC}`}>
            <span data-bar="row3" className={styles.rowBar} />
            <span data-glow="row3" className={styles.glow} />
          </span>
        </div>
      </div>
    </figure>
  )
}
