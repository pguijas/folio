"use client"

import { type ReactNode, useEffect, useRef } from "react"

import styles from "./agents-artifact-kinds.module.css"

type AnimationScope = {
  revert: () => void
}

type Anime = typeof import("animejs")
type Props = import("animejs").AnimationParams
type AgentId = "1" | "2" | "3"

const OUT = "out(2)"
const SINE = "inOutSine"
const BACK = "outBack(3)"
const POP = "outBack(2.4)"

/** Four columns by three rows: the whole of the data artifact's pattern. */
const CELLS = Array.from({ length: 12 }, (_, index) => index)

/** Each agent owns one 1650ms beat, so only one is ever in the accent. */
const B1 = 300
const B2 = 1950
const B3 = 3600
const BEATS: Record<AgentId, number> = { "1": B1, "2": B2, "3": B3 }

/** The story, built at module scope so the beats read as a short script.
 * Nothing is drawn between any two elements at all: three agents fill a
 * shared tray and the work below resolves once they have. There is no
 * layer above them handing anything out. */
function buildStory({ createTimeline, stagger, steps, utils }: Anime) {
  utils.set("[data-bot]", { y: "0rem" })
  utils.set("[data-work]", { y: "0rem" })
  utils.set("[data-antenna]", { rotate: 0 })
  utils.set("[data-eyes]", { scaleY: 1 })
  utils.set("[data-eye-lit]", { opacity: 0 })
  utils.set("[data-slot-lit]", { opacity: 0 })
  utils.set("[data-work-lit]", { opacity: 0 })
  utils.set("[data-tick-lit]", { opacity: 0 })
  utils.set("[data-tick]", { opacity: 0, scale: 0 })
  utils.set("[data-line]", { scaleX: 0 })
  utils.set("[data-band]", { scaleX: 0 })
  utils.set("[data-block]", { opacity: 0, scale: 0.72 })
  utils.set("[data-cell]", { opacity: 0, scale: 0.4 })
  utils.set("[data-read]", { opacity: 0, y: "0rem" })

  const tl = createTimeline({ loop: true, loopDelay: 2200 })
  const at = (target: string, props: Props, ms: number) =>
    tl.add(target, props, ms)

  const lightUp = (target: string, d: number, ms: number) =>
    at(target, { opacity: [0, 1], duration: d, ease: OUT }, ms)

  const lightOff = (target: string, d: number, ms: number) =>
    at(target, { opacity: [1, 0], duration: d, ease: SINE }, ms)

  /** Lean into the work, then settle back with a little overshoot. */
  const bob = (target: string, drop: string, ms: number) => {
    at(target, { y: ["0rem", drop], duration: 170, ease: OUT }, ms)
    at(target, { y: [drop, "0rem"], duration: 500, ease: BACK }, ms + 170)
  }

  const twitch = (target: string, deg: number, ms: number) => {
    at(target, { rotate: [0, deg], duration: 140, ease: "out(3)" }, ms)
    at(target, { rotate: [deg, 0], duration: 400, ease: BACK }, ms + 140)
  }

  /** One agent's turn: it wakes, its own slot lights, it leans in, it dims
   * again before the next one wakes. The fill is scheduled per kind below. */
  const beat = (id: AgentId) => {
    const b = BEATS[id]
    lightUp(`[data-eye-lit='${id}']`, 260, b)
    twitch(`[data-antenna='${id}']`, -16, b + 130)
    lightUp(`[data-slot-lit='${id}']`, 220, b + 250)
    bob(`[data-bot='${id}']`, "0.14rem", b + 400)
    lightOff(`[data-slot-lit='${id}']`, 540, b + 1250)
    lightOff(`[data-eye-lit='${id}']`, 380, b + 1260)
  }

  // 1. Prose: three uneven lines type themselves into the first frame.
  //    Nothing sent the agent here; it is simply the first to work.
  beat("1")
  at(
    "[data-line]",
    { scaleX: [0, 1], duration: 360, delay: stagger(150), ease: steps(8) },
    B1 + 380,
  )

  // 2. A page: a band across the top, then two unequal blocks under it.
  beat("2")
  at("[data-band]", { scaleX: [0, 1], duration: 320, ease: steps(8) }, B2 + 380)
  at(
    "[data-block]",
    {
      opacity: [0, 1],
      scale: [0.72, 1],
      duration: 300,
      delay: stagger(140),
      ease: POP,
    },
    B2 + 580,
  )

  // 3. Data: a grid of squares, filling out from the first corner.
  beat("3")
  at(
    "[data-cell]",
    {
      opacity: [0, 1],
      scale: [0.4, 1],
      duration: 260,
      delay: stagger(72, { grid: [4, 3], from: "first" }),
      ease: "outBack(2.6)",
    },
    B3 + 380,
  )

  // 4. The shared read: one line crosses all three frames while every agent
  //    watches, so what one of them published is plainly there for the rest.
  //    No agent is handed anything; they are all reading the same tray.
  at("[data-read]", { opacity: [0, 1], duration: 140, ease: "linear" }, 5350)
  at(
    "[data-read]",
    { y: ["0rem", "4.6rem"], duration: 900, ease: "linear" },
    5350,
  )
  at("[data-read]", { opacity: [1, 0], duration: 220, ease: "linear" }, 6080)
  at(
    "[data-eye-lit]",
    { opacity: [0, 0.6], duration: 240, ease: OUT },
    5420,
  )
  at(
    "[data-eye-lit]",
    { opacity: [0.6, 0], duration: 420, ease: SINE },
    6120,
  )

  // 5. Only once all three have been read does the card below take its tick:
  //    the work is resolved by what was published, not the other way round.
  lightUp("[data-work-lit]", 220, 6420)
  lightUp("[data-tick-lit]", 180, 6480)
  at(
    "[data-tick]",
    { opacity: [0, 1], scale: [0, 1], duration: 360, ease: "outBack(3.2)" },
    6480,
  )
  bob("[data-work]", "0.1rem", 6480)
  twitch("[data-antenna]", 12, 6700)
  at("[data-eyes]", { scaleY: [1, 0.42], duration: 200, ease: SINE }, 6700)
  at("[data-eyes]", { scaleY: [0.42, 1], duration: 260, ease: OUT }, 6940)
  lightOff("[data-tick-lit]", 620, 7040)
  lightOff("[data-work-lit]", 640, 7080)
}

function Robot({ id }: { id: AgentId }) {
  return (
    <div className={styles.seat}>
      <span data-bot={id} className={styles.bot}>
        <span data-antenna={id} className={styles.antenna} />
        <span className={styles.head}>
          <span data-eyes className={styles.eyes}>
            <span className={styles.eye}>
              <span data-eye-lit={id} className={styles.eyeLit} />
            </span>
            <span className={styles.eye}>
              <span data-eye-lit={id} className={styles.eyeLit} />
            </span>
          </span>
        </span>
      </span>
    </div>
  )
}

/** One tray slot. Same hairline frame at the same size every time, so the
 * interior is the only thing separating one kind of output from another. */
function Slot({ id, children }: { id: AgentId; children: ReactNode }) {
  return (
    <div className={styles.slot}>
      {children}
      <span data-slot-lit={id} className={styles.lit} />
    </div>
  )
}

export function AgentsAnimation() {
  const root = useRef<HTMLElement>(null)

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return
    }

    let cancelled = false
    let scope: AnimationScope | undefined

    void import("animejs").then((anime) => {
      if (cancelled || !root.current) {
        return
      }

      scope = anime.createScope({ root }).add(() => {
        buildStory(anime)
      })
    })

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
      aria-label="Three small robot figures stand in a row between a shared tray of three identical hairline frames above them and one task card below: each robot in turn lights up in the accent colour and fills only the frame above itself, the first with three uneven lines of prose, the second with a page layout of a band and two unequal blocks, the third with a grid of small squares, so the three kinds of output appear one after another at the same size in the same frame; then a single line crosses all three frames at once while every robot's eyes light, because what any one of them published is there for the others to read, and only after that does the card at the foot of the scene take its tick and everything settle back to grey"
    >
      <div className={styles.stage} aria-hidden="true">
        <div className={styles.scene}>
          <div className={styles.tray}>
            <span data-read className={styles.read} />
            <Slot id="1">
              <span className={styles.prose}>
                <span data-line className={`${styles.line} ${styles.lineA}`} />
                <span data-line className={`${styles.line} ${styles.lineB}`} />
                <span data-line className={`${styles.line} ${styles.lineC}`} />
              </span>
            </Slot>

            <Slot id="2">
              <span className={styles.page}>
                <span data-band className={styles.band} />
                <span className={styles.blocks}>
                  <span
                    data-block
                    className={`${styles.block} ${styles.blockA}`}
                  />
                  <span
                    data-block
                    className={`${styles.block} ${styles.blockB}`}
                  />
                </span>
              </span>
            </Slot>

            <Slot id="3">
              <span className={styles.grid}>
                {CELLS.map((cell) => (
                  <span key={cell} data-cell className={styles.cell} />
                ))}
              </span>
            </Slot>
          </div>

          <div className={styles.crew}>
            <Robot id="1" />
            <Robot id="2" />
            <Robot id="3" />
          </div>

          <div data-work className={styles.work}>
            <span className={styles.box}>
              <span data-tick className={styles.tick} />
              <span data-tick-lit className={styles.tickLit} />
            </span>
            <span className={styles.workBar} />
            <span data-work-lit className={styles.lit} />
          </div>
        </div>
      </div>
    </figure>
  )
}
