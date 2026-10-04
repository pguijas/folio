"use client"

import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

export function Steps({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null)

  // A step that mounts below the fold is marked offscreen until it scrolls
  // in, so a theme can draw its connector then. Reduced motion marks none.
  useEffect(() => {
    const root = ref.current
    if (!root || typeof IntersectionObserver === "undefined") return
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return

    const waiting = Array.from(
      root.querySelectorAll<HTMLElement>(':scope > [data-slot="step"]')
    ).filter((step) => step.getBoundingClientRect().top > window.innerHeight)
    if (waiting.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          delete (entry.target as HTMLElement).dataset.state
          observer.unobserve(entry.target)
        }
      },
      { rootMargin: "0px 0px -15% 0px" }
    )
    for (const step of waiting) {
      step.dataset.state = "offscreen"
      observer.observe(step)
    }
    return () => {
      observer.disconnect()
      for (const step of waiting) delete step.dataset.state
    }
  }, [])

  return (
    <div
      ref={ref}
      data-slot="steps"
      className={cn(
        "relative ml-4 pl-8 my-8",
        "[counter-reset:step]",
        "[&>div]:relative [&>div]:mb-10 [&>div:last-child]:mb-0"
      )}
    >
      <div data-slot="steps-rail" className="absolute left-0 top-4 bottom-4 w-px bg-border" />
      {children}
    </div>
  )
}

export function Step({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div data-slot="step" className="[counter-increment:step]">
      <div
        data-slot="step-marker"
        className={cn(
          "absolute -left-[41px] flex h-7 w-7 items-center justify-center rounded-full",
          "bg-primary text-primary-foreground text-xs font-semibold",
          "ring-4 ring-background",
          "before:content-[counter(step)]"
        )}
      />
      <h3 data-slot="step-title" className="font-semibold text-base mb-1.5 text-foreground leading-7">
        {title}
      </h3>
      <div data-slot="step-body" className="text-sm text-muted-foreground [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
        {children}
      </div>
    </div>
  )
}

Step.displayName = "Step"
