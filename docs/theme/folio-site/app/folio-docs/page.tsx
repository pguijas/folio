"use client"

import { normalizeLandingHref } from "@/components/landing/actions"
import {
  BuildPipelineLandingHero,
  DocsMapLandingHero,
  HeartbeatLandingHero,
  SourcePipelineLandingHero,
} from "@/components/landing/hero"
import { FolioProductSwitcher } from "@/components/folio-product-switcher"
import { LandingNavbar } from "@/components/landing-navbar"
import { LandingSectionRenderer } from "@/components/landing/sections"
import { ThemeStyleBootstrap } from "@/components/theme-configurator"
import type {
  LandingHeroVariant,
  LandingLink,
  LandingPipelineStep,
  LandingSection,
} from "@/components/landing/types"

const installCommands: string[] = __LANDING_INSTALL_COMMANDS__
const landingSections = __LANDING_SECTIONS__ as LandingSection[]

const projectName = __PROJECT_NAME_JSON__
const projectMonogram = __PROJECT_MONOGRAM_JSON__
const projectVersion = __PROJECT_VERSION_JSON__
const landingTagline = __LANDING_TAGLINE_JSON__
const landingNoticeText = __LANDING_NOTICE_TEXT_JSON__
const landingNoticeLink = __LANDING_NOTICE_LINK_JSON__
const landingHeadline = __LANDING_HEADLINE_JSON__
const landingDescription = __LANDING_DESCRIPTION_JSON__
const primaryCtaText = __LANDING_CTA_PRIMARY_TEXT_JSON__
const primaryCtaLink = __LANDING_CTA_PRIMARY_LINK_JSON__
const secondaryCtaText = __LANDING_CTA_SECONDARY_TEXT_JSON__
const secondaryCtaLink: string | null = __LANDING_CTA_SECONDARY_LINK_JSON__
const landingHeroVariant = __LANDING_HERO_VARIANT_JSON__ as LandingHeroVariant

/* This landing is served from /folio-docs/, one route below the site root, so
   every href it builds from a configured "/path" has to climb back out first.
   The root cover leaves this at its "." default. */
const pathToRoot = ".."

const normalizedPrimaryCtaLink = normalizeLandingHref(primaryCtaLink, pathToRoot)
const normalizedSecondaryCtaLink = secondaryCtaLink
  ? normalizeLandingHref(secondaryCtaLink, pathToRoot)
  : null
const secondaryCtaIsExternal =
  normalizedSecondaryCtaLink?.startsWith("http") ?? false

const actionLinks: LandingLink[] = [
  {
    href: normalizedPrimaryCtaLink,
    title: primaryCtaText,
    detail: "Start with the guide",
    primary: true,
  },
  ...(normalizedSecondaryCtaLink
    ? [
        {
          href: normalizedSecondaryCtaLink,
          title: secondaryCtaText,
          detail: "Open the source",
          external: secondaryCtaIsExternal,
        },
      ]
    : []),
]

const footerLinks: LandingLink[] = actionLinks.map(
  ({ href, title, external }) => ({
    href,
    title,
    detail: "",
    external,
  })
)

const actionGridClassName = [
  "landing-action-grid mt-8 grid w-full max-w-2xl gap-px overflow-hidden border border-border bg-border sm:mt-10",
  actionLinks.length > 1 ? "sm:grid-cols-2" : "sm:grid-cols-1",
].join(" ")

const buildSteps: LandingPipelineStep[] = [
  {
    label: "01",
    title: "Parse source",
    detail:
      "Python modules, docstrings, Markdown, and docs.yaml become one content graph.",
  },
  {
    label: "02",
    title: "Compose docs",
    detail:
      "Reference pages, sidebar data, MDX components, and search stay in sync.",
  },
  {
    label: "03",
    title: "Export static",
    detail:
      "The output is a deployable static site with Pagefind search and LLM files included.",
  },
]

const LandingHero =
  landingHeroVariant === "heartbeat"
    ? HeartbeatLandingHero
    : landingHeroVariant === "build-pipeline"
      ? BuildPipelineLandingHero
      : landingHeroVariant === "source-pipeline"
        ? SourcePipelineLandingHero
        : DocsMapLandingHero

export default function Home() {
  return (
    <div className="landing-shell flex min-h-screen flex-col overflow-hidden">
      {/* the landing applies the reader's saved theme exactly like the docs
          pages do, so navigating between them never changes appearance */}
      <ThemeStyleBootstrap />
      <LandingNavbar
        pathToRoot={pathToRoot}
        productSwitcher={
          <FolioProductSwitcher current="docs" pathToRoot={pathToRoot} />
        }
      />

      <main id="main-content" className="flex-1">
        <LandingHero
          tagline={landingTagline}
          headline={landingHeadline}
          description={landingDescription}
          actionLinks={actionLinks}
          actionGridClassName={actionGridClassName}
          installCommands={installCommands}
          buildSteps={buildSteps}
          projectName={projectName}
          projectMonogram={projectMonogram}
          projectVersion={projectVersion}
          noticeText={landingNoticeText}
          noticeLink={landingNoticeLink}
          pathToRoot={pathToRoot}
        />

        <LandingSectionRenderer
          sections={landingSections}
          context={{ actionLinks, buildSteps, installCommands, pathToRoot }}
        />
      </main>

      <footer className="border-t border-border bg-muted/20">
        <div className="mx-auto flex max-w-site flex-col items-start justify-between gap-8 px-6 py-10 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3">
            <span
              className="grid size-9 place-items-center rounded-lg border border-border bg-card font-mono text-[11px] font-bold text-primary"
              aria-hidden="true"
            >
              {projectMonogram}
            </span>
            <p className="leading-none">
              <span className="block text-sm font-semibold text-foreground">
                Made with Folio
              </span>
              <span className="mt-1.5 block font-mono text-[10px] text-muted-foreground uppercase">
                docs from source
              </span>
            </p>
          </div>
          <nav className="flex gap-6">
            {footerLinks.map((link) => (
              <a
                key={link.title}
                href={link.href}
                target={link.external ? "_blank" : undefined}
                rel={link.external ? "noopener noreferrer" : undefined}
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {link.title}
              </a>
            ))}
          </nav>
        </div>
      </footer>
    </div>
  )
}
