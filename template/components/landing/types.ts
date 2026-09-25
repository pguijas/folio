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

/* "funnel" section: a source tile — a mark and a plain label. */
export type LandingFunnelInput = {
  label: string
  /* tile mark, one of: "config" | "python" | "javascript" | "rust"
   * | "markdown" | "language" | "guides" | "api" | "pages" | "folder"
   * | "search" | "agents" | "hash" */
  icon?: string
  /* dashed + dimmed "on the roadmap" treatment */
  ghost?: boolean
  /* small pill riding the tile, e.g. "roadmap" */
  chip?: string
}

/* "funnel" section: an output tile; same vocabulary as the input's icon. */
export type LandingFunnelOutput = Pick<LandingFunnelInput, "label" | "icon">

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
  /* "cells" section photograph, drawn above the copy in place of `visual`.
     Rendered as a duotone so a photograph does not become the only saturated
     thing on an otherwise near-monochrome page. */
  image?: string
  /* Alt text for `image`. Omit for a decorative photograph: the cell's title
     and description already carry the meaning, and a caption repeated to a
     screen reader is noise. */
  image_alt?: string
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
  | "mechanism"
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
  /* "mechanism" section */
  code_title?: string
  code?: string
  commits?: LandingCommit[]
  pills?: string[]
  caption?: string
  /* "funnel" section */
  command?: string
  inputs?: LandingFunnelInput[]
  outputs?: LandingFunnelOutput[]
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
