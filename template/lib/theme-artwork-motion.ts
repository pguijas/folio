// Theme artwork shares one motion/visibility boundary, including previews.
export function watchThemeArtwork(element: HTMLElement, start: () => () => void, activePreset = "omarchy") {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)")
  const page = element.closest<HTMLElement>(".theme-gallery-page")
  const slide = element.closest<HTMLElement>(".theme-gallery-slide")
  let visible = true
  let pending = 0
  let stop: (() => void) | undefined

  const refresh = () => {
    pending = 0
    stop?.()
    stop = undefined
    const preset = page?.dataset.preset ?? document.documentElement.dataset.folioPreset
    if (preset !== activePreset || reduced.matches || document.hidden || !visible) return
    if (slide && slide.dataset.offset !== "0") return
    const bounds = element.getBoundingClientRect()
    if (!bounds.width || !bounds.height || bounds.bottom <= 0 || bounds.top >= innerHeight) return
    stop = start()
  }
  const schedule = () => {
    cancelAnimationFrame(pending)
    pending = requestAnimationFrame(refresh)
  }
  const theme = new MutationObserver(schedule)
  theme.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-folio-preset", "data-folio-scheme"],
  })
  if (page) theme.observe(page, { attributes: true, attributeFilter: ["style", "data-preset"] })
  if (slide) theme.observe(slide, { attributes: true, attributeFilter: ["data-offset"] })
  const visibility = new IntersectionObserver(([entry]) => {
    if (visible === entry.isIntersecting) return
    visible = entry.isIntersecting
    schedule()
  })
  visibility.observe(element)
  reduced.addEventListener("change", schedule)
  document.addEventListener("visibilitychange", schedule)
  schedule()
  return () => {
    cancelAnimationFrame(pending)
    stop?.()
    theme.disconnect()
    visibility.disconnect()
    reduced.removeEventListener("change", schedule)
    document.removeEventListener("visibilitychange", schedule)
  }
}
