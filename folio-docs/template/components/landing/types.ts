import type { ComparisonRow } from "@/components/comparison-matrix"

export type LandingHeroVariant =
  | "docs-map"
  | "source-pipeline"
  | "build-pipeline"
  | "heartbeat"

export type LandingLink = {
  href: string
  title: string
  detail?: string
  primary?: boolean
  external?: boolean
}

export type LandingFeature = {
  title: string
  description: string
  wide?: boolean
  /* "bento" variant vignette kind drawn above the copy: one of
   * "components" | "llms" | "receipt" | "deploy" | "plugins" | "theming" */
  visual?: string
}

/* "funnel" section: a source card on the left of the plate. */
export type LandingFunnelInput = {
  label: string
  detail?: string
  /* node mark, one of: "config" | "python" | "markdown" | "language"
   * | "folder" | "search" | "agents" | "hash" | "board" */
  icon?: string
  /* dashed + dimmed "on the roadmap" treatment */
  ghost?: boolean
  /* small pill riding the card, e.g. "roadmap" */
  chip?: string
}

/* "funnel" section: an artifact card on the right of the plate. */
export type LandingFunnelOutput = {
  label: string
  detail?: string
  /* node mark; same vocabulary as LandingFunnelInput.icon */
  icon?: string
}

/* "funnel" section: a guarantee note in the plate's apparatus strip. */
export type LandingFunnelGuarantee = {
  title: string
  detail?: string
}

/* "harness" section: one tool or one shared project surface in the diagram. */
export type LandingHarnessItem = {
  label: string
  detail?: string
}

export type LandingRouteItem = {
  label: string
  href: string
  path: string
  detail: string
}

export type LandingPipelineStep = {
  label: string
  title: string
  detail: string
}

export type LandingCatalogItem = {
  title?: string
  label?: string
  value?: string
  description?: string
  detail?: string
  href?: string
  path?: string
  external?: boolean
  /* "cells" section footer link text */
  link_text?: string
  /* "cells" section vignette kind drawn above the copy */
  visual?: string
}

export type LandingCommit = {
  hash: string
  message: string
}

export type LandingSectionType =
  | "features"
  | "comparison"
  | "output"
  | "routes"
  | "pipeline"
  | "install"
  | "stats"
  | "use-cases"
  | "cta"
  | "link-grid"
  | "cells"
  | "boards"
  | "mechanism"
  | "harness"
  | "statement"
  | "funnel"

export type LandingSection = {
  type: LandingSectionType | string
  enabled?: boolean
  eyebrow?: string
  title?: string
  title_muted?: string
  description?: string
  /* short stage label ("The mechanism") — staged sections render the
   * numbered StageRail; numbering is computed at render time */
  stage?: string
  /* "features" section: "bento" renders the vignette card grid */
  variant?: string
  features?: LandingFeature[]
  items?: LandingCatalogItem[]
  links?: LandingCatalogItem[]
  actions?: LandingLink[]
  commands?: string[]
  routes?: LandingRouteItem[]
  steps?: LandingPipelineStep[]
  /* "boards" section */
  roadmap_url?: string
  roadmap_link_text?: string
  narrow?: boolean
  /* "mechanism" section */
  code_title?: string
  code?: string
  commits?: LandingCommit[]
  pills?: string[]
  caption?: string
  /* "harness" section */
  thesis?: string
  docs_label?: string
  docs_detail?: string
  agents_label?: string
  agents_detail?: string
  harnesses?: LandingHarnessItem[]
  unifies?: LandingHarnessItem[]
  /* "funnel" section */
  command?: string
  command_notes?: string[]
  inputs?: LandingFunnelInput[]
  outputs?: LandingFunnelOutput[]
  guarantees?: LandingFunnelGuarantee[]
  /* "comparison" section: the project's own table. Without both `tools` and
   * `rows` the section falls back to Folio's deprecated bundled matrix. */
  tools?: string[]
  rows?: ComparisonRow[]
  /* "statement" section */
  text?: string
  accent?: string
  size?: "md" | "lg"
}

export type LandingSectionContext = {
  actionLinks: LandingLink[]
  buildSteps: LandingPipelineStep[]
  installCommands: string[]
  /** Relative path from the page rendering these sections back to the site
   * root — "." on the landing itself, ".." for a landing served one route
   * below it. Every section that turns a configured "/path" into an href
   * needs it; omitted, the hrefs assume the root. */
  pathToRoot?: string
}
