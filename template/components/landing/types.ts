export type LandingHeroVariant = "docs-map" | "source-pipeline"

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

export type LandingSection = {
  type: LandingSectionType | string
  enabled?: boolean
  eyebrow?: string
  title?: string
  description?: string
  features?: LandingFeature[]
  items?: LandingCatalogItem[]
  links?: LandingCatalogItem[]
  actions?: LandingLink[]
  commands?: string[]
  routes?: LandingRouteItem[]
  steps?: LandingPipelineStep[]
}

export type LandingSectionContext = {
  actionLinks: LandingLink[]
  buildSteps: LandingPipelineStep[]
  installCommands: string[]
}
