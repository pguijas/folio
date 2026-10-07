"use client"

import { useEffect, useRef } from "react"
import { watchThemeArtwork } from "@/lib/theme-artwork-motion"

/* folioh's real CLI banner (FOLIOH_ASCII_ART in folioh-cli/src/ui/banner.rs). The CLI also
   stamps its own release on the last line (`banner()` in the same file passes the crate
   version). Nothing injects that release into the template,
   and the site's `projectVersion` is a different number, so the mock renders
   the art alone: a literal here would go stale on the next folioh release and
   would misstate folioh's version on every other project's landing page. */
export const FOLIOH_BANNER = [
  " ████████╗ ██████╗ ██╗     ██╗ ██████╗  ██╗  ██╗",
  " ██╔═════╝██╔═══██╗██║     ██║██╔═══██╗ ██║  ██║",
  " █████╗   ██║   ██║██║     ██║██║   ██║ ███████║",
  " ██╔══╝   ██║   ██║██║     ██║██║   ██║ ██╔══██║",
  " ██║      ╚██████╔╝███████╗██║╚██████╔╝ ██║  ██║",
  " ╚═╝       ╚═════╝ ╚══════╝╚═╝ ╚═════╝  ╚═╝  ╚═╝",
].join("\n")

// Original text effects: sweep, falling columns, scattered decode, then radial.
// Whitespace stays fixed so the banner never changes its grid while rebuilding.
export function wordmarkFrame(text: string, effect: number, progress: number): string {
  if (progress >= 1) return text
  const lines = text.split("\n").map((line) => Array.from(line))
  const width = Math.max(1, ...lines.map((line) => line.length))
  const height = lines.length
  const glyphs = "+*:░▒▓"
  return lines.map((line, y) => line.map((character, x) => {
    if (/\s/.test(character)) return character
    let threshold: number
    switch (effect % 4) {
      case 0: threshold = x / width; break
      case 1: threshold = y / height * 0.65 + (x * 7 % 11) / 11 * 0.35; break
      case 2: threshold = (x * 17 + y * 23) % 41 / 41; break
      default: threshold = Math.hypot((x - (width - 1) / 2) / width, (y - (height - 1) / 2) / height) / Math.SQRT1_2
    }
    if (progress > threshold) return character
    if (effect % 4 !== 2 && threshold - progress > 0.16) return " "
    return glyphs[(x + y * 3 + Math.floor(progress * 30)) % glyphs.length]
  }).join("")).join("\n")
}

export function ThemeWordmark({ name, interactive = true }: { name: string; interactive?: boolean }) {
  const elementRef = useRef<HTMLElement | null>(null)
  const nextEffect = useRef(0)
  const ascii = name.toLowerCase() === "folioh"
  const text = ascii ? FOLIOH_BANNER : name

  useEffect(() => {
    const element = elementRef.current
    if (!element) return
    element.textContent = text
    let frame = 0
    const width = element.style.width
    const stop = () => {
      cancelAnimationFrame(frame)
      element.textContent = text
      element.style.width = width
    }
    const replay = () => {
      stop()
      element.style.width = getComputedStyle(element).width
      const effect = nextEffect.current++ % 4
      const started = performance.now()
      let painted = -Infinity
      const paint = (now: number) => {
        const progress = Math.max(0, Math.min(1, (now - started) / 1200))
        if (progress >= 1) {
          stop()
          return
        }
        if (now - painted >= 1000 / 30) {
          element.textContent = wordmarkFrame(text, effect, progress)
          painted = now
        }
        frame = requestAnimationFrame(paint)
      }
      frame = requestAnimationFrame(paint)
    }
    return watchThemeArtwork(element, () => {
      if (interactive) {
        element.removeAttribute("disabled")
        element.addEventListener("click", replay)
      }
      replay()
      return () => {
        if (interactive) {
          element.removeEventListener("click", replay)
          element.setAttribute("disabled", "")
        }
        stop()
      }
    })
  }, [text, interactive])

  const attributes = {
    ref: (element: HTMLElement | null) => { elementRef.current = element },
    "data-pagefind-ignore": "all",
    "data-ascii": ascii || undefined,
    className: "theme-wordmark",
  }
  return interactive
    ? <button {...attributes} type="button" disabled aria-label={`Replay ${name} animation`}>{text}</button>
    : <span aria-hidden="true" {...attributes}>{text}</span>
}
