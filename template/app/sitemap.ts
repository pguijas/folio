import type { MetadataRoute } from "next"
import { existsSync, readdirSync } from "fs"
import { join, relative } from "path"

export const dynamic = "force-static"

const SITE_URL: string = "__SITE_URL__"
const CONTENT_DIR = join(process.cwd(), "content")
const INCLUDE_DOCS_INDEX: string = "__INCLUDE_DOCS_INDEX__"
const includeDocsIndex = INCLUDE_DOCS_INDEX !== "false"

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

  if (route === "index") return includeDocsIndex ? "/docs/" : ""
  if (route.endsWith("/index")) {
    return `/docs/${route.slice(0, -"/index".length)}/`
  }
  return `/docs/${route}/`
}

function collectRoutePaths() {
  const routes = new Set<string>(["/"])
  if (includeDocsIndex) {
    routes.add("/docs/")
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
  if (a === "/docs/") return -1
  if (b === "/docs/") return 1
  return a.localeCompare(b)
}

function absoluteUrl(routePath: string) {
  return routePath === "/" ? `${SITE_URL}/` : `${SITE_URL}${routePath}`
}

export default function sitemap(): MetadataRoute.Sitemap {
  if (!SITE_URL || !SITE_URL.startsWith("http")) {
    return []
  }

  return collectRoutePaths().map((routePath) => ({
    url: absoluteUrl(routePath),
    changeFrequency: "weekly",
    priority: routePath === "/" ? 1 : routePath === "/docs/" ? 0.8 : 0.6,
  }))
}
