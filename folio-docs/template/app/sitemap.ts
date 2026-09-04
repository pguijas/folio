import type { MetadataRoute } from "next"
import { existsSync, readdirSync } from "fs"
import { join, relative } from "path"

export const dynamic = "force-static"

const SITE_URL: string = "__SITE_URL__"
const CONTENT_DIR = join(process.cwd(), "content")
const INCLUDE_DOCS_INDEX: string = "__INCLUDE_DOCS_INDEX__"
const includeDocsIndex = INCLUDE_DOCS_INDEX !== "false"
const DOCS_ROUTE_BASE: string = "__DOCS_ROUTE_BASE__"
const docsRouteBase = DOCS_ROUTE_BASE.replace(/\/+$/, "") || "/docs"
const docsIndexRoute = `${docsRouteBase}/`

function contentMdxFiles(directory: string): string[] {
  if (!existsSync(directory)) return []

  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = join(directory, entry.name)
    if (entry.isDirectory()) return contentMdxFiles(entryPath)
    if (entry.isFile() && entry.name.endsWith(".mdx")) return [entryPath]
    return []
  })
}

function docsRouteForContentFile(filePath: string) {
  const relativePath = relative(CONTENT_DIR, filePath).replace(/\\/g, "/")
  const route = relativePath.replace(/\.mdx$/, "")

  if (route === "index") return includeDocsIndex ? docsIndexRoute : ""
  if (route.endsWith("/index")) {
    return `${docsRouteBase}/${route.slice(0, -"/index".length)}/`
  }
  return `${docsRouteBase}/${route}/`
}

// Every page the build writes also gets a Markdown mirror under
// public/_folio/markdown, named after the content file (content/plugins/index.mdx
// mirrors to plugins/index.md). Listing the mirrors gives them a pointer that
// does not depend on running the site's JavaScript.
function markdownMirrorPath(filePath: string) {
  const relativePath = relative(CONTENT_DIR, filePath).replace(/\\/g, "/")
  return `/_folio/markdown/${relativePath.replace(/\.mdx$/, ".md")}`
}

function collectMarkdownMirrorPaths() {
  return contentMdxFiles(CONTENT_DIR).map(markdownMirrorPath).sort()
}

function collectRoutePaths() {
  const routes = new Set<string>(["/"])
  if (includeDocsIndex) {
    routes.add(docsIndexRoute)
  }
  for (const filePath of contentMdxFiles(CONTENT_DIR)) {
    const routePath = docsRouteForContentFile(filePath)
    if (routePath) {
      routes.add(routePath)
    }
  }
  return Array.from(routes).sort(compareRoutePaths)
}

function compareRoutePaths(a: string, b: string) {
  if (a === b) return 0
  if (a === "/") return -1
  if (b === "/") return 1
  if (a === docsIndexRoute) return -1
  if (b === docsIndexRoute) return 1
  return a.localeCompare(b)
}

function absoluteUrl(routePath: string) {
  return routePath === "/" ? `${SITE_URL}/` : `${SITE_URL}${routePath}`
}

export default function sitemap(): MetadataRoute.Sitemap {
  if (!SITE_URL || !SITE_URL.startsWith("http")) {
    return []
  }

  const pages: MetadataRoute.Sitemap = collectRoutePaths().map((routePath) => ({
    url: absoluteUrl(routePath),
    changeFrequency: "weekly",
    priority: routePath === "/" ? 1 : routePath === docsIndexRoute ? 0.8 : 0.6,
  }))
  const markdownMirrors: MetadataRoute.Sitemap =
    collectMarkdownMirrorPaths().map((mirrorPath) => ({
      url: absoluteUrl(mirrorPath),
      changeFrequency: "weekly",
      priority: 0.3,
    }))

  return [...pages, ...markdownMirrors]
}
