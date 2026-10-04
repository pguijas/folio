"use client"

import { useEffect, useRef } from "react"
import { watchThemeArtwork } from "@/lib/theme-artwork-motion"

export { FOLIO_BANNER, ThemeWordmark } from "./theme-wordmark"

// An original, fixed grid: three paths keep every copy small in the DOM.
const pixelPaths = ["", "", ""]
for (let row = 0; row < 27; row++) {
  for (let column = 0; column < 40; column++) {
    const level = (column * 3 + row * 5 + column * row) % 11
    if (level < 3) pixelPaths[level] += `M${column * 3} ${row * 3}h1v1h-1Z`
  }
}

export function ThemePixelField() {
  const host = useRef<HTMLSpanElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const element = host.current
    const surface = canvas.current
    if (!element || !surface) return
    return watchThemeArtwork(element, () => {
      const context = surface.getContext("2d")
      if (!context) return () => {}
      const preview = Boolean(element.closest(".theme-gallery-page"))
      const colors = getComputedStyle(element)
      const ink = colors.color
      const bright = colors.getPropertyValue("--foreground").trim()
      let width = 0
      let height = 0
      let frame = 0
      let last = 0
      let lastPointer = 0
      type Point = { x: number; y: number; born: number }
      let trail: Point[] = []
      let waves: (Point & { strength: number })[] = []
      let press: (Point & { id: number; clientX: number; clientY: number }) | undefined
      const measure = () => {
        width = element.clientWidth
        height = element.clientHeight
        const ratio = Math.min(devicePixelRatio || 1, 2)
        surface.width = Math.round(width * ratio)
        surface.height = Math.round(height * ratio)
        context.setTransform(ratio, 0, 0, ratio, 0, 0)
      }
      const locate = (event: PointerEvent) => {
        if (!preview && (event.target as Element)?.closest?.('[role="dialog"]')) return
        const bounds = element.getBoundingClientRect()
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) return
        return { x: (event.clientX - bounds.left) * width / bounds.width, y: (event.clientY - bounds.top) * height / bounds.height, born: performance.now() }
      }
      const move = (event: PointerEvent) => {
        if (press && Math.hypot(event.clientX - press.clientX, event.clientY - press.clientY) > 12) press = undefined
        const point = locate(event)
        if (!point || event.pointerType !== "mouse" || point.born - lastPointer < 45) return
        lastPointer = point.born
        trail = [...trail.slice(-7), point]
      }
      const down = (event: PointerEvent) => {
        if (event.button !== 0 || !event.isPrimary) return
        if ((event.target as Element)?.closest?.('a, button, input, select, textarea, [role="button"], [contenteditable="true"]')) return
        const point = locate(event)
        if (point) press = { ...point, id: event.pointerId, clientX: event.clientX, clientY: event.clientY }
      }
      const up = (event: PointerEvent) => {
        if (!press || event.pointerId !== press.id) return
        const now = performance.now()
        waves = [...waves.slice(-3), { ...press, born: now, strength: 0.35 + Math.min((now - press.born) / 1200, 1) * 0.65 }]
        press = undefined
      }
      const cancel = () => { press = undefined }
      const draw = (now: number) => {
        frame = requestAnimationFrame(draw)
        if (now - last < 1000 / 30) return
        last = now
        trail = trail.filter(point => now - point.born < 800)
        waves = waves.filter(point => now - point.born < 1600)
        context.clearRect(0, 0, width, height)
        const step = Math.max(preview ? 5 : 10, width / 96)
        const reach = preview ? 40 : 110
        for (let y = 0, row = 0; y < height; y += step, row++) {
          for (let x = 0, column = 0; x < width; x += step, column++) {
            const seed = ((column * 47 + row * 89 + column * row * 3) % 101) / 101
            const drift = (Math.sin(column * 0.19 + now / 3700) + Math.cos(row * 0.23 - now / 4300) + Math.sin((column + row) * 0.11 + now / 5100)) / 3
            let light = Math.max(0, drift - 0.05) * 0.5
            for (const point of trail) {
              const distance = ((x - point.x) ** 2 + (y - point.y) ** 2) / reach ** 2
              light = Math.max(light, Math.exp(-distance * 2) * (1 - (now - point.born) / 800) * 0.8)
            }
            for (const wave of waves) {
              const age = (now - wave.born) / 1600
              const radius = age * reach * (2 + wave.strength)
              const ring = Math.max(0, 1 - Math.abs(Math.hypot(x - wave.x, y - wave.y) - radius) / (step * 2))
              light += ring * (1 - age) * wave.strength
            }
            if (press) {
              const charge = Math.min((now - press.born) / 1200, 1)
              const distance = Math.hypot(x - press.x, y - press.y) / (reach * (0.3 + charge))
              light += Math.max(0, 1 - distance) * (0.3 + charge * 0.5)
            }
            if (seed > light || light < 0.03) continue
            context.fillStyle = light > 0.65 ? bright : ink
            context.globalAlpha = Math.min(0.85, light + 0.12)
            const size = Math.max(2, Math.round(step * (light > 0.6 ? 0.55 : 0.35)))
            context.fillRect(Math.round(x), Math.round(y), size, size)
          }
        }
        if (!element.dataset.live) element.dataset.live = "true"
      }
      const resize = new ResizeObserver(measure)
      resize.observe(element)
      measure()
      frame = requestAnimationFrame(draw)
      window.addEventListener("pointermove", move, { passive: true })
      window.addEventListener("pointerdown", down, { passive: true })
      window.addEventListener("pointerup", up, { passive: true })
      window.addEventListener("pointercancel", cancel, { passive: true })
      window.addEventListener("contextmenu", cancel)
      window.addEventListener("blur", cancel)
      return () => {
        cancelAnimationFrame(frame)
        resize.disconnect()
        window.removeEventListener("pointermove", move)
        window.removeEventListener("pointerdown", down)
        window.removeEventListener("pointerup", up)
        window.removeEventListener("pointercancel", cancel)
        window.removeEventListener("contextmenu", cancel)
        window.removeEventListener("blur", cancel)
        delete element.dataset.live
      }
    })
  }, [])

  return (
    <span ref={host} aria-hidden="true" className="theme-pixel-field">
      <svg aria-hidden="true" focusable="false" viewBox="0 0 120 80" preserveAspectRatio="xMidYMid slice" fill="currentColor">
        {pixelPaths.map((d, index) => <path key={index} d={d} opacity={[0.18, 0.32, 0.5][index]} />)}
      </svg>
      <canvas ref={canvas} />
    </span>
  )
}
