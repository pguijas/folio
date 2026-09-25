import type { LandingRouteItem } from "@/components/landing/types"

const docsRouteBase =
  process.env.NEXT_PUBLIC_FOLIO_DOCS_ROUTE_BASE?.replace(/\/+$/, "") || "/docs"

export const defaultRoutes: LandingRouteItem[] = [
  {
    label: "Guide",
    href: `.${docsRouteBase}/`,
    path: docsRouteBase,
    detail: "Markdown pages",
  },
  {
    label: "API",
    href: `.${docsRouteBase}/api-reference/`,
    path: `${docsRouteBase}/api-reference`,
    detail: "From source",
  },
  {
    label: "Search",
    href: `.${docsRouteBase}/?q=`,
    path: "/_pagefind",
    detail: "Static index",
  },
]
