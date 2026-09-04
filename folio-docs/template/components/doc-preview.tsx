"use client"

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  ArrowDown01Icon,
  ArrowRight01Icon,
  ArrowUpRight01Icon,
  FileCodeIcon,
  FolderOpenIcon,
  ViewIcon,
} from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

interface DocPreviewProps {
  src?: string
  example?: string
  title: string
  description?: string
  height?: number
}

type PreviewMode = "preview" | "source"
type SourceStatus = "idle" | "loading" | "loaded" | "error"

type SourceFile = {
  path: string
  route?: string
  url: string
  language: string
  title?: string
}

type SourceTreeFileNode = {
  type: "file"
  name: string
  file: SourceFile
}

type SourceTreeFolderNode = {
  type: "folder"
  name: string
  path: string
  children: SourceTreeNode[]
}

type SourceTreeNode = SourceTreeFolderNode | SourceTreeFileNode

const PREVIEW_THEME_VARIABLES = [
  "--background",
  "--foreground",
  "--card",
  "--card-foreground",
  "--popover",
  "--popover-foreground",
  "--primary",
  "--primary-foreground",
  "--secondary",
  "--secondary-foreground",
  "--muted",
  "--muted-foreground",
  "--accent",
  "--accent-foreground",
  "--border",
  "--input",
  "--ring",
  "--chart-1",
  "--chart-2",
  "--chart-3",
  "--chart-4",
  "--chart-5",
  "--folio-heading-font-family",
  "--folio-body-font-family",
  "--folio-code-font-family",
  "--folio-heading-letter-spacing",
  "--folio-heading-weight",
  "--folio-body-line-height",
  "--radius",
]

const FOLIO_BASE_PATH = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\/+$/, "") ?? ""
const FOLIO_DOCS_ROUTE_BASE =
  process.env.NEXT_PUBLIC_FOLIO_DOCS_ROUTE_BASE?.replace(/\/+$/, "") || "/docs"
const FOLIO_DOCS_ROUTE_SEGMENTS = FOLIO_DOCS_ROUTE_BASE.split("/").filter(Boolean)

function withFolioBasePath(path: string) {
  if (/^[a-z][a-z\d+.-]*:/i.test(path)) return path
  if (!path.startsWith("/")) return path
  if (!FOLIO_BASE_PATH || FOLIO_BASE_PATH === "/") return path
  if (path === FOLIO_BASE_PATH || path.startsWith(`${FOLIO_BASE_PATH}/`)) return path

  return `${FOLIO_BASE_PATH}${path}`
}

function docsRouteFromPathname(pathname: string) {
  const segments = pathname.split("/").filter(Boolean)
  for (let index = 0; index <= segments.length - FOLIO_DOCS_ROUTE_SEGMENTS.length; index++) {
    const matches = FOLIO_DOCS_ROUTE_SEGMENTS.every(
      (segment, offset) => segments[index + offset] === segment
    )
    if (matches) {
      const routeSegments = segments.slice(index + FOLIO_DOCS_ROUTE_SEGMENTS.length)
      return routeSegments.length ? routeSegments.join("/") : "index"
    }
  }

  return segments.length ? segments.join("/") : "index"
}

function titleFromRoute(route: string) {
  const segment = route.split("/").filter(Boolean).at(-1) ?? "index"
  return segment.replace(/[-_]/g, " ")
}

function examplePath(example: string) {
  return example
    .split("/")
    .map((segment) => encodeURIComponent(segment.trim()))
    .filter(Boolean)
    .join("/")
}

function exampleUrlForPreview(example: string) {
  return withFolioBasePath(`/_folio/examples/${examplePath(example)}/index.html`)
}

function exampleManifestUrl(example: string) {
  return withFolioBasePath(`/_folio/examples/${examplePath(example)}/manifest.json`)
}

function sourceFileForPreview(src?: string): SourceFile | null {
  if (!src) return null

  const currentUrl = new URL(window.location.href)
  const previewUrl = new URL(src, currentUrl)

  if (previewUrl.origin !== currentUrl.origin) return null

  const route = docsRouteFromPathname(previewUrl.pathname)
  const sourcePath = withFolioBasePath("/_folio/markdown/")

  return {
    path: `content/${route}.mdx`,
    route,
    url: new URL(`${sourcePath}${route}.md`, currentUrl).toString(),
    language: "mdx",
    title: titleFromRoute(route),
  }
}

function sourceUrlForPreview(src?: string) {
  return sourceFileForPreview(src)?.url ?? null
}

function normalizeExampleSourceFile(value: unknown): SourceFile | null {
  if (typeof value !== "object" || value === null) return null

  const file = value as Record<string, unknown>
  if (typeof file.path !== "string" || typeof file.url !== "string") {
    return null
  }

  return {
    path: file.path,
    url: withFolioBasePath(file.url),
    language: typeof file.language === "string" ? file.language : "text",
    title: typeof file.title === "string" ? file.title : file.path,
  }
}

function sourceTreePath(file: SourceFile) {
  return file.path.replace(/^content\//, "")
}

function folderPathsForSourceFile(file: SourceFile) {
  const parts = sourceTreePath(file).split("/")
  parts.pop()

  return parts.reduce<string[]>((paths, part) => {
    const parent = paths.at(-1)
    paths.push(parent ? `${parent}/${part}` : part)
    return paths
  }, [])
}

function folderPathsForSourceFiles(files: SourceFile[]) {
  return files.flatMap(folderPathsForSourceFile)
}

function sortSourceTree(nodes: SourceTreeNode[]) {
  return nodes
    .sort((a, b) => {
      if (a.type !== b.type) return a.type === "folder" ? -1 : 1
      return a.name.localeCompare(b.name)
    })
    .map((node) => {
      if (node.type === "folder") {
        node.children = sortSourceTree(node.children)
      }
      return node
    })
}

function buildSourceTree(files: SourceFile[]): SourceTreeNode[] {
  const tree: SourceTreeNode[] = []

  for (const file of files) {
    const parts = sourceTreePath(file).split("/")
    const fileName = parts.pop() ?? file.path
    let currentLevel = tree
    let folderPath = ""

    for (const part of parts) {
      folderPath = folderPath ? `${folderPath}/${part}` : part
      let folder = currentLevel.find(
        (node): node is SourceTreeFolderNode =>
          node.type === "folder" && node.path === folderPath
      )

      if (!folder) {
        folder = {
          type: "folder",
          name: part,
          path: folderPath,
          children: [],
        }
        currentLevel.push(folder)
      }

      currentLevel = folder.children
    }

    currentLevel.push({
      type: "file",
      name: fileName,
      file,
    })
  }

  return sortSourceTree(tree)
}

function renderHighlightedLine(line: string, language = "mdx"): ReactNode {
  const trimmed = line.trimStart()

  if (language === "json" && line.includes(":")) {
    const [key, ...rest] = line.split(":")
    return (
      <>
        <span className="text-primary">{key}</span>
        <span className="text-muted-foreground">:</span>
        <span className="text-foreground">{rest.join(":")}</span>
      </>
    )
  }

  if (trimmed.startsWith("#")) {
    return <span className="font-semibold text-primary">{line}</span>
  }

  if (trimmed.startsWith("```")) {
    return <span className="text-muted-foreground">{line}</span>
  }

  if (trimmed.startsWith("import ") || trimmed.startsWith("export ")) {
    return <span className="text-primary">{line}</span>
  }

  if (/^[-*]\s/.test(trimmed) || /^\d+\.\s/.test(trimmed)) {
    return <span className="text-foreground">{line}</span>
  }

  if (/<\/?[A-Z][A-Za-z0-9]*/.test(line)) {
    return <span className="text-primary">{line}</span>
  }

  if (/`[^`]+`/.test(line)) {
    return <span className="text-foreground">{line}</span>
  }

  return line || " "
}

function sourceDisplayPath(file: SourceFile | null, href: string | null) {
  if (file) return file.path
  if (href) return new URL(href, window.location.href).pathname
  return "Generated Markdown"
}

function syncPreviewFrameTheme(frame: HTMLIFrameElement | null) {
  if (!frame?.contentDocument) return

  try {
    const parentStyle = getComputedStyle(document.documentElement)
    const frameRoot = frame.contentDocument.documentElement

    for (const variable of PREVIEW_THEME_VARIABLES) {
      const value = parentStyle.getPropertyValue(variable)
      if (value.trim()) {
        frameRoot.style.setProperty(variable, value)
      }
    }
  } catch {
    // External previews cannot be themed from the docs page.
  }
}

export function DocPreview({
  src,
  example,
  title,
  description,
  height = 420,
}: DocPreviewProps) {
  const [mode, setMode] = useState<PreviewMode>("preview")
  const [sourceStatus, setSourceStatus] = useState<SourceStatus>("idle")
  const [sourceCode, setSourceCode] = useState("")
  const [sourceHref, setSourceHref] = useState<string | null>(null)
  const [sourceFiles, setSourceFiles] = useState<SourceFile[]>([])
  const [activeSourceFile, setActiveSourceFile] = useState<SourceFile | null>(null)
  const [sourceCache, setSourceCache] = useState<Record<string, string>>({})
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const previewFrameRef = useRef<HTMLIFrameElement | null>(null)
  const previewId = useId()

  const frameStyle = {
    "--folio-doc-preview-height": `${height}px`,
  } as CSSProperties

  const loadSourceCode = useCallback(
    (file: SourceFile | null) => {
      if (!file) {
        setSourceCode("")
        setSourceHref(null)
        setActiveSourceFile(null)
        setSourceStatus("error")
        return
      }

      setActiveSourceFile(file)
      setSourceHref(file.url)
      setExpandedFolders((current) => {
        const next = new Set(current)
        for (const folderPath of folderPathsForSourceFile(file)) {
          next.add(folderPath)
        }
        return next
      })
      const sourceUrl = file.url

      const cached = sourceCache[sourceUrl]
      if (cached !== undefined) {
        setSourceCode(cached)
        setSourceStatus("loaded")
        return
      }

      setSourceStatus("loading")
      void fetch(sourceUrl, { cache: "no-store" })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Unable to load source: ${response.status}`)
          }
          return response.text()
        })
        .then((text) => {
          const cleanText = text.trimEnd()
          setSourceCode(cleanText)
          setSourceCache((current) => ({
            ...current,
            [sourceUrl]: cleanText,
          }))
          setSourceStatus("loaded")
        })
        .catch(() => {
          setSourceCode("")
          setSourceStatus("error")
        })
    },
    [sourceCache]
  )

  const loadExampleWorkspace = useCallback(
    (exampleName: string) => {
      setSourceHref(null)
      setSourceFiles([])
      setSourceStatus("loading")

      void fetch(exampleManifestUrl(exampleName), { cache: "no-store" })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Unable to load example: ${response.status}`)
          }
          return response.json()
        })
        .then((manifest: unknown) => {
          const files =
            typeof manifest === "object" &&
            manifest !== null &&
            Array.isArray((manifest as { files?: unknown }).files)
              ? (manifest as { files: unknown[] }).files
                  .map(normalizeExampleSourceFile)
                  .filter((file): file is SourceFile => file !== null)
              : []

          if (files.length === 0) {
            throw new Error("Example has no source files")
          }

          setSourceFiles(files)
          setExpandedFolders(new Set(folderPathsForSourceFiles(files)))
          loadSourceCode(files[0])
        })
        .catch(() => {
          setSourceFiles([])
          setSourceCode("")
          setSourceStatus("error")
        })
    },
    [loadSourceCode]
  )

  const loadSourceWorkspace = useCallback(() => {
    if (example) {
      loadExampleWorkspace(example)
      return
    }

    const primaryFile = sourceFileForPreview(src)
    const sourceUrl = sourceUrlForPreview(src)
    setSourceHref(sourceUrl)

    if (!primaryFile) {
      loadSourceCode(null)
      return
    }

    setSourceFiles([primaryFile])
    loadSourceCode(primaryFile)
  }, [example, loadExampleWorkspace, loadSourceCode, src])

  const showPreview = useCallback(() => {
    setMode("preview")
  }, [])

  const syncPreviewTheme = useCallback(() => {
    syncPreviewFrameTheme(previewFrameRef.current)
  }, [])

  const showSource = useCallback(() => {
    setMode("source")
    if (sourceFiles.length > 0 && activeSourceFile) return
    loadSourceWorkspace()
  }, [activeSourceFile, loadSourceWorkspace, sourceFiles.length])

  const selectSourceFile = useCallback(
    (file: SourceFile) => {
      loadSourceCode(file)
    },
    [loadSourceCode]
  )

  const toggleSourceFolder = useCallback((path: string) => {
    setExpandedFolders((current) => {
      const next = new Set(current)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }, [])

  const tabButtonClass = (active: boolean) =>
    cn(
      "inline-flex h-8 items-center gap-1.5 rounded-sm px-2.5 text-xs font-medium",
      "outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring",
      active
        ? "bg-background text-foreground shadow-sm"
        : "text-muted-foreground hover:bg-background/70 hover:text-foreground"
    )

  const sourceFileButtonClass = (active: boolean) =>
    cn(
      "flex h-8 w-full items-center gap-2 rounded-sm px-2 text-left font-mono text-xs",
      "outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring",
      active
        ? "bg-primary/10 text-primary"
        : "text-muted-foreground hover:bg-muted hover:text-foreground"
    )

  const sourceLines = sourceCode ? sourceCode.split("\n") : [""]
  const sourceOpenHref = activeSourceFile?.url ?? sourceHref
  const sourceTree = buildSourceTree(sourceFiles)
  const previewHref = example ? exampleUrlForPreview(example) : src
  const previewPanelId = `${previewId}-preview-panel`
  const sourcePanelId = `${previewId}-source-panel`

  useEffect(() => {
    if (mode !== "preview") return

    syncPreviewTheme()
    const observer = new MutationObserver(syncPreviewTheme)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "style"],
    })
    observer.observe(document.head, {
      childList: true,
      subtree: true,
      characterData: true,
    })

    return () => {
      observer.disconnect()
    }
  }, [mode, previewHref, syncPreviewTheme])

  const previewModeTabs = (
    <div
      role="tablist"
      aria-label={`${title} preview mode`}
      className="mb-2 inline-flex rounded-md border border-border bg-muted p-0.5"
    >
      <button
        type="button"
        role="tab"
        aria-selected={mode === "preview"}
        aria-controls={previewPanelId}
        onClick={showPreview}
        className={tabButtonClass(mode === "preview")}
      >
        <HugeiconsIcon icon={ViewIcon} size={14} strokeWidth={2} />
        <span>Preview</span>
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "source"}
        aria-controls={sourcePanelId}
        onClick={showSource}
        className={tabButtonClass(mode === "source")}
      >
        <HugeiconsIcon icon={FileCodeIcon} size={14} strokeWidth={2} />
        <span>Source</span>
      </button>
    </div>
  )

  const renderSourceTree = (nodes: SourceTreeNode[], depth = 0): ReactNode =>
    nodes.map((node) => {
      const indentStyle = {
        paddingLeft: `${0.5 + depth * 0.85}rem`,
      }

      if (node.type === "folder") {
        const expanded = expandedFolders.has(node.path)

        return (
          <div key={node.path}>
            <button
              type="button"
              role="treeitem"
              aria-expanded={expanded}
              aria-selected={false}
              onClick={() => toggleSourceFolder(node.path)}
              className="source-folder-row flex h-8 w-full items-center gap-1.5 rounded-sm pr-2 text-left font-mono text-xs text-muted-foreground outline-none transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
              style={indentStyle}
            >
              <HugeiconsIcon
                icon={expanded ? ArrowDown01Icon : ArrowRight01Icon}
                size={12}
                strokeWidth={2}
                className="shrink-0"
              />
              <HugeiconsIcon
                icon={FolderOpenIcon}
                size={13}
                strokeWidth={2}
                className="shrink-0"
              />
              <span className="min-w-0 truncate">{node.name}</span>
            </button>
            {expanded && (
              <div role="group">{renderSourceTree(node.children, depth + 1)}</div>
            )}
          </div>
        )
      }

      const active = activeSourceFile?.path === node.file.path

      return (
        <button
          key={node.file.path}
          type="button"
          role="treeitem"
          aria-selected={active}
          aria-current={active ? "page" : undefined}
          title={node.file.path}
          onClick={() => selectSourceFile(node.file)}
          className={cn("source-file-row", sourceFileButtonClass(active))}
          style={indentStyle}
        >
          <HugeiconsIcon
            icon={FileCodeIcon}
            size={13}
            strokeWidth={2}
            className="shrink-0"
          />
          <span className="min-w-0 truncate">{node.name}</span>
        </button>
      )
    })

  return (
    <figure
      className="my-7 max-w-full overflow-hidden rounded-lg border border-border bg-card"
      style={frameStyle}
    >
      <figcaption className="flex flex-col gap-3 border-b border-border bg-muted/35 px-4 py-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          {previewModeTabs}
          <h3 className="m-0 text-base font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {previewHref && (
            <a
              href={previewHref}
              className="inline-flex h-8 w-fit shrink-0 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Open page
              <HugeiconsIcon icon={ArrowUpRight01Icon} size={12} strokeWidth={2} />
            </a>
          )}
        </div>
      </figcaption>
      {mode === "preview" ? (
        <div id={previewPanelId} role="tabpanel" className="bg-background">
          <iframe
            ref={previewFrameRef}
            title={`${title} preview`}
            src={previewHref}
            loading="lazy"
            referrerPolicy="strict-origin-when-cross-origin"
            onLoad={syncPreviewTheme}
            className="h-[var(--folio-doc-preview-height)] w-full border-0 bg-background"
          />
        </div>
      ) : (
        <div
          id={sourcePanelId}
          role="tabpanel"
          className="h-[var(--folio-doc-preview-height)] overflow-hidden bg-background"
        >
          <div className="grid h-full min-h-0 w-full min-w-0 grid-rows-[12rem_minmax(0,1fr)] overflow-hidden md:grid-cols-[16rem_minmax(0,1fr)] md:grid-rows-none">
            <aside className="source-file-drawer min-h-0 min-w-0 border-b border-border bg-muted/15 md:border-b-0 md:border-r">
              <div className="flex h-10 items-center gap-2 border-b border-border px-3 text-xs font-medium text-foreground">
                <HugeiconsIcon icon={FolderOpenIcon} size={14} strokeWidth={2} />
                <span className="truncate">content</span>
                <span className="ml-auto rounded border border-border bg-background px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
                  {sourceFiles.length}
                </span>
              </div>
              <div
                role="tree"
                aria-label="Source files"
                className="h-[calc(100%-2.5rem)] space-y-0.5 overflow-auto p-2"
              >
                {renderSourceTree(sourceTree)}
              </div>
            </aside>
            <div className="min-h-0 min-w-0">
              <div className="flex min-h-10 items-center justify-between gap-3 border-b border-border bg-muted/20 px-4">
                <span className="truncate font-mono text-xs text-muted-foreground">
                  {sourceDisplayPath(activeSourceFile, sourceHref)}
                </span>
                {sourceOpenHref && (
                  <a
                    href={sourceOpenHref}
                    className="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    Open source
                    <HugeiconsIcon icon={ArrowUpRight01Icon} size={12} strokeWidth={2} />
                  </a>
                )}
              </div>
              {sourceStatus === "loading" && (
                <div className="flex h-[calc(100%-2.5rem)] items-center px-4 text-sm text-muted-foreground">
                  Loading source...
                </div>
              )}
              {sourceStatus === "error" && (
                <div className="flex h-[calc(100%-2.5rem)] items-center px-4 text-sm text-muted-foreground">
                  Source is not available for this preview.
                </div>
              )}
              {sourceStatus === "loaded" && (
                <pre className="source-code-preview m-0 h-[calc(100%-2.5rem)] min-w-0 overflow-auto bg-background p-0 font-mono text-xs leading-6 text-foreground">
                  <code className="block min-w-full py-3">
                    {sourceLines.map((line, index) => {
                      const lineNumber = index + 1

                      return (
                        <span
                          key={`${lineNumber}-${line}`}
                          className="group flex min-w-max border-l-2 border-transparent px-4"
                        >
                          <span className="line-number mr-4 w-8 shrink-0 select-none text-right text-muted-foreground/70">
                            {lineNumber}
                          </span>
                          <span className="whitespace-pre pr-6">
                            {renderHighlightedLine(line, activeSourceFile?.language)}
                          </span>
                        </span>
                      )
                    })}
                  </code>
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </figure>
  )
}
