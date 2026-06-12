import type { LandingRouteItem } from "@/components/landing/types"

export const defaultRoutes: LandingRouteItem[] = [
  {
    label: "Guide",
    href: "./docs/",
    path: "/docs",
    detail: "Markdown pages",
  },
  {
    label: "API",
    href: "./docs/api-reference/",
    path: "/docs/api-reference",
    detail: "Python source",
  },
  {
    label: "Search",
    href: "./docs/?q=",
    path: "/_pagefind",
    detail: "Static index",
  },
]
