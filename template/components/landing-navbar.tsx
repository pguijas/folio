"use client"

import { useEffect, useState } from "react"
import { Moon02Icon, Sun03Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useTheme } from "next-themes"

import {
  GitHubMark,
  isGitHubHref,
  normalizeLandingHref,
} from "@/components/landing/actions"
import { cn } from "@/lib/utils"

const projectName = __PROJECT_NAME_JSON__
const projectMonogram = __PROJECT_MONOGRAM_JSON__
const secondaryCtaText = __LANDING_CTA_SECONDARY_TEXT_JSON__
const secondaryCtaLink: string | null = __LANDING_CTA_SECONDARY_LINK_JSON__
/* The navbar always points at the docs — the hero owns the configured CTA. */
const normalizedSecondaryCtaLink = secondaryCtaLink
  ? normalizeLandingHref(secondaryCtaLink)
  : null
const secondaryCtaIsExternal =
  normalizedSecondaryCtaLink?.startsWith("http") ?? false

interface LandingNavbarProps {
  /** Relative path from the current page back to the site root — "." on the
   * landing itself, ".." on single-segment public views. Keeps every href
   * relative so exports stay portable (file://, GitHub Pages subpaths). */
  pathToRoot?: string
  /** Set on app-shaped views (the board's workspace mode), which run to the
   * viewport edges instead of stopping at `max-w-site`. Kept centered, the
   * navbar broke off 120px before the board did on a wide screen and the
   * monogram floated in whitespace the work below had already claimed. The
   * bar keeps its `px-6`, which is the padding the workspace's board column
   * carries too, so the monogram lands on the first column's edge and the
   * theme toggle on the last one's. */
  workspace?: boolean
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    const frame = requestAnimationFrame(() => setMounted(true))
    return () => cancelAnimationFrame(frame)
  }, [])
  const isDark = resolvedTheme === "dark"
  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label="Toggle theme"
      title="Toggle theme"
      className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {mounted ? (
        <HugeiconsIcon
          icon={isDark ? Sun03Icon : Moon02Icon}
          size={16}
          strokeWidth={1.8}
          aria-hidden="true"
        />
      ) : (
        <span className="block size-4" aria-hidden="true" />
      )}
    </button>
  )
}

export function LandingNavbar({
  pathToRoot = ".",
  workspace = false,
}: LandingNavbarProps) {
  return (
    <header className="landing-navbar fixed top-0 z-50 w-full border-b border-border/50 bg-background/75 backdrop-blur-xl">
      <div
        className={cn(
          "mx-auto flex h-16 max-w-site items-center justify-between px-6",
          // The same breakpoint the workspace goes full-bleed at, so the two
          // never disagree at any width.
          workspace && "lg:max-w-none"
        )}
      >
        <a href={`${pathToRoot}/`} className="flex items-center gap-2.5">
          <span className="flex size-7 items-center justify-center rounded-md bg-primary font-mono text-[11px] font-bold text-primary-foreground shadow-[0_12px_28px_-16px_var(--primary)]">
            {projectMonogram}
          </span>
          <span className="text-sm font-semibold text-foreground">
            {projectName}
          </span>
        </a>
        <nav className="flex items-center gap-1">
          <a
            href={`${pathToRoot}/docs/`}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            Documentation
          </a>
          {normalizedSecondaryCtaLink ? (
            isGitHubHref(normalizedSecondaryCtaLink) ? (
              <a
                href={normalizedSecondaryCtaLink}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={secondaryCtaText}
                title={secondaryCtaText}
                className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <GitHubMark />
              </a>
            ) : (
              <a
                href={normalizedSecondaryCtaLink}
                target={secondaryCtaIsExternal ? "_blank" : undefined}
                rel={secondaryCtaIsExternal ? "noopener noreferrer" : undefined}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {secondaryCtaText}
              </a>
            )
          ) : null}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
