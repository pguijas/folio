"use client"

import { usePathname } from "next/navigation"

interface Version {
  label: string
  path: string
  defaultPath?: string
}

const versions: Version[] = __VERSIONS__
const configuredCurrentPath: string = __CURRENT_VERSION_PATH__

export function VersionSelector() {
  const pathname = usePathname()

  if (versions.length === 0) return null

  const currentVersion =
    versions.find((v) => v.path === configuredCurrentPath) ||
    versions.find((v) => pathname.startsWith(`/${v.path}/`)) ||
    versions[0]

  const getVersionSubpath = () => {
    const currentPrefix = currentVersion?.path ? `/${currentVersion.path}/` : ""
    const prefixIndex = currentPrefix ? pathname.indexOf(currentPrefix) : -1
    const rawSubpath = prefixIndex >= 0
      ? pathname.slice(prefixIndex + currentPrefix.length)
      : pathname.replace(/^\/+/, "")
    return normalizeSubpath(rawSubpath)
  }

  const normalizeSubpath = (subpath: string) => {
    const normalized = subpath
      .replace(/^\/+/, "")
      .replace(/(^|\/)index\.html$/, "$1")
    return normalized && !normalized.endsWith("/") ? `${normalized}/` : normalized
  }

  const getRelativePrefix = () => {
    const depth = getVersionSubpath().split("/").filter(Boolean).length + 1
    return "../".repeat(depth)
  }

  const getVersionHref = (version: Version) => {
    const subpath = version.defaultPath
      ? normalizeSubpath(version.defaultPath)
      : getVersionSubpath()
    return `${getRelativePrefix()}${version.path}/${subpath}`
  }

  return (
    <details
      className="group relative"
      aria-label="Select documentation version"
    >
      <summary className="flex cursor-pointer list-none items-center rounded-md border border-border bg-background px-2 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-1 focus:ring-ring [&::-webkit-details-marker]:hidden">
        {currentVersion?.label}
      </summary>
      <div className="absolute right-0 z-50 mt-2 min-w-36 overflow-hidden rounded-md border border-border bg-background py-1 shadow-lg">
        {versions.map((v) => {
          const active = v.path === currentVersion?.path
          return (
            <a
              key={v.path}
              href={getVersionHref(v)}
              aria-current={active ? "page" : undefined}
              className={`block px-3 py-2 text-xs transition-colors ${
                active
                  ? "bg-muted font-medium text-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {v.label}
            </a>
          )
        })}
      </div>
    </details>
  )
}
