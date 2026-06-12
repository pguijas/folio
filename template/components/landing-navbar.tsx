"use client"

import { normalizeLandingHref } from "@/components/landing/actions"

const projectName = __PROJECT_NAME_JSON__
const projectMonogram = __PROJECT_MONOGRAM_JSON__
const primaryCtaText = __LANDING_CTA_PRIMARY_TEXT_JSON__
const primaryCtaLink = __LANDING_CTA_PRIMARY_LINK_JSON__
const secondaryCtaText = __LANDING_CTA_SECONDARY_TEXT_JSON__
const secondaryCtaLink: string | null = __LANDING_CTA_SECONDARY_LINK_JSON__
const normalizedPrimaryCtaLink = normalizeLandingHref(primaryCtaLink)
const normalizedSecondaryCtaLink = secondaryCtaLink
  ? normalizeLandingHref(secondaryCtaLink)
  : null
const secondaryCtaIsExternal = normalizedSecondaryCtaLink?.startsWith("http") ?? false

export function LandingNavbar() {
  return (
    <header className="landing-navbar fixed top-0 z-50 w-full border-b border-border/50 bg-background/75 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <a href="./" className="flex items-center gap-2.5">
          <span className="flex size-7 items-center justify-center rounded-md bg-primary font-mono text-[11px] font-bold text-primary-foreground shadow-[0_12px_28px_-16px_var(--primary)]">
            {projectMonogram}
          </span>
          <span className="text-sm font-semibold text-foreground">
            {projectName}
          </span>
        </a>
        <nav className="flex items-center gap-1">
          <a
            href={normalizedPrimaryCtaLink}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {primaryCtaText}
          </a>
          {normalizedSecondaryCtaLink ? (
            <a
              href={normalizedSecondaryCtaLink}
              target={secondaryCtaIsExternal ? "_blank" : undefined}
              rel={secondaryCtaIsExternal ? "noopener noreferrer" : undefined}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {secondaryCtaText}
            </a>
          ) : null}
        </nav>
      </div>
    </header>
  )
}
