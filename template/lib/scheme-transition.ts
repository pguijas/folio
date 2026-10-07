// Switching between light and dark. Under Pastel the new scheme is revealed
// as a circle growing from the control that asked for it, or from the middle
// of the viewport for the `d` shortcut, after cojeev's theme transition (MIT,
// see THIRD-PARTY-NOTICES.md). This sets the circle's centre and radius on
// <html>; the reveal itself is the `::view-transition-new(root)` animation in
// shell.css, over --folioh-motion-max. Every other preset, a browser without
// view transitions and a reader who asks for reduced motion switch at once.

import { flushSync } from "react-dom"

let schemeUpdate = 0

export function switchScheme(
  setTheme: (theme: string) => void,
  theme: string,
  from?: Element,
) {
  const update = ++schemeUpdate
  const apply = () => {
    if (update === schemeUpdate) setTheme(theme)
  }
  const root = document.documentElement
  if (
    root.dataset.foliohPreset !== "pastel" ||
    typeof document.startViewTransition !== "function" ||
    document.hidden ||
    matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    apply()
    return
  }
  const box = from?.getBoundingClientRect()
  const x = box ? box.x + box.width / 2 : innerWidth / 2
  const y = box ? box.y + box.height / 2 : innerHeight / 2
  root.style.setProperty("--folioh-reveal-at", `${x}px ${y}px`)
  root.style.setProperty(
    "--folioh-reveal-r",
    `${Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))}px`,
  )
  try {
    const transition = document.startViewTransition(() => flushSync(apply))
    void transition.ready.catch(() => {})
  } catch {
    apply()
  }
}
