"use client"

import { useEffect, useState } from "react"
import {
  ArrowRight01Icon,
  GithubIcon,
  Moon02Icon,
  Sun03Icon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { useTheme } from "next-themes"

interface ProjectHeaderActionsProps {
  repoHref?: string
  themeToggle?: boolean
  actionHref?: string
  actionLabel?: string
}

function externalProps(href: string) {
  if (/^https?:\/\//.test(href)) {
    return { target: "_blank", rel: "noreferrer" }
  }
  return {}
}

export function ProjectHeaderActions({
  repoHref,
  themeToggle = false,
  actionHref,
  actionLabel,
}: ProjectHeaderActionsProps) {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    const frame = requestAnimationFrame(() => setMounted(true))
    return () => cancelAnimationFrame(frame)
  }, [])

  const isDark = resolvedTheme === "dark"

  return (
    <div className="flex items-center gap-3">
      {repoHref ? (
        <a
          href={repoHref}
          {...externalProps(repoHref)}
          aria-label="GitHub repository"
          title="GitHub repository"
          className="rounded-md p-2 text-muted-foreground transition-colors hover:text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <HugeiconsIcon
            icon={GithubIcon}
            size={16}
            strokeWidth={1.8}
            aria-hidden="true"
          />
        </a>
      ) : null}
      {themeToggle ? (
        <button
          type="button"
          onClick={() => setTheme(isDark ? "light" : "dark")}
          aria-label="Toggle theme"
          title="Toggle theme"
          className="rounded-md p-2 text-muted-foreground transition-colors hover:text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
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
      ) : null}
      {actionHref && actionLabel ? (
        <a
          href={actionHref}
          {...externalProps(actionHref)}
          className="flex items-center gap-1.5 rounded-md bg-foreground px-3.5 py-1.5 text-xs font-medium text-background transition-colors hover:bg-foreground/80 focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <span>{actionLabel}</span>
          <HugeiconsIcon
            icon={ArrowRight01Icon}
            size={12}
            strokeWidth={1.8}
            aria-hidden="true"
          />
        </a>
      ) : null}
    </div>
  )
}
