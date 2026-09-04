"use client"

import { Fragment, useCallback, useState } from "react"
import Image from "next/image"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  AiChat02Icon,
  ArrowDown01Icon,
  ArrowUpRight01Icon,
  CodeCircleIcon,
  CopyCheckIcon,
  CopyIcon,
} from "@hugeicons/core-free-icons"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

type PageAction =
  | {
      label: "Copy page"
      kind: "copy"
    }
  | {
      label: "View Markdown"
      kind: "view"
    }
  | {
      label: "ChatGPT"
      kind: "assistant"
      url: string
      promptParam: "q"
      icon: string
      invertIcon?: boolean
    }
  | {
      label: "MCP JSON"
      kind: "mcp"
    }

const PAGE_ACTIONS: PageAction[] = [
  {
    label: "Copy page",
    kind: "copy",
  },
  {
    label: "View Markdown",
    kind: "view",
  },
  {
    label: "ChatGPT",
    kind: "assistant",
    url: "https://chatgpt.com/",
    promptParam: "q",
    icon: "/icons/chatgpt.svg",
    invertIcon: true,
  },
  {
    label: "MCP JSON",
    kind: "mcp",
  },
]

const CHATGPT_ACTION = PAGE_ACTIONS.find(
  (action): action is Extract<PageAction, { kind: "assistant" }> =>
    action.kind === "assistant"
)

const FOLIO_BASE_PATH = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\/+$/, "") ?? ""
const FOLIO_DOCS_ROUTE_BASE =
  process.env.NEXT_PUBLIC_FOLIO_DOCS_ROUTE_BASE?.replace(/\/+$/, "") || "/docs"
const FOLIO_DOCS_ROUTE_SEGMENTS = FOLIO_DOCS_ROUTE_BASE.split("/").filter(Boolean)

function withFolioBasePath(path: string) {
  if (/^[a-z][a-z\d+.-]*:/i.test(path)) return path
  if (!path.startsWith("/")) return path
  if (!FOLIO_BASE_PATH || FOLIO_BASE_PATH === "/") return path
  if (path === FOLIO_BASE_PATH || path.startsWith(`${FOLIO_BASE_PATH}/`)) {
    return path
  }

  return `${FOLIO_BASE_PATH}${path}`
}

function getPageContext() {
  const article = document.querySelector("article")
  let articleText = article?.textContent || ""
  if (article instanceof HTMLElement) {
    articleText = article.innerText
  }
  const title =
    article?.querySelector("h1")?.textContent?.trim() ||
    document.title.split(" - ")[0]?.trim() ||
    document.title
  const url = window.location.href
  const content =
    articleText.replace(/\n{3,}/g, "\n\n").trim() ||
    document.body.textContent?.replace(/\n{3,}/g, "\n\n").trim() ||
    ""

  return { title, url, content }
}

function getDocsRoute() {
  const segments = window.location.pathname.split("/").filter(Boolean)
  let routeSegments: string[] = []
  for (let index = 0; index <= segments.length - FOLIO_DOCS_ROUTE_SEGMENTS.length; index++) {
    const matches = FOLIO_DOCS_ROUTE_SEGMENTS.every(
      (segment, offset) => segments[index + offset] === segment
    )
    if (matches) {
      routeSegments = segments.slice(index + FOLIO_DOCS_ROUTE_SEGMENTS.length)
      break
    }
  }
  return routeSegments.length ? routeSegments.join("/") : "index"
}

function getMarkdownUrl() {
  return new URL(
    withFolioBasePath(`/_folio/markdown/${getDocsRoute()}.md`),
    window.location.href
  ).toString()
}

function createAssistantReadPrompt() {
  return `Read from ${getMarkdownUrl()} so I can ask questions about it.`
}

function createMcpPayload() {
  const { title, url, content } = getPageContext()
  return JSON.stringify(
    {
      type: "folio.page_context",
      version: 1,
      resource: {
        uri: url,
        name: title,
        mimeType: "text/plain",
        text: content,
      },
    },
    null,
    2
  )
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textarea = document.createElement("textarea")
  textarea.value = text
  textarea.setAttribute("readonly", "")
  textarea.style.position = "fixed"
  textarea.style.left = "-9999px"
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand("copy")
  document.body.removeChild(textarea)
}

function actionText(action: PageAction) {
  if (action.kind === "copy") {
    return getPageContext().content
  }
  if (action.kind === "view") {
    return getMarkdownUrl()
  }
  if (action.kind === "mcp") {
    return createMcpPayload()
  }
  return createAssistantReadPrompt()
}

function actionStatus(action: PageAction) {
  if (action.kind === "copy") return "Copied"
  if (action.kind === "view") return ""
  if (action.kind === "mcp") return "MCP copied"
  return "Prompt opened"
}

function actionIcon(action: PageAction) {
  if (action.kind === "copy") return CopyIcon
  if (action.kind === "view") return CodeCircleIcon
  if (action.kind === "mcp") return CodeCircleIcon
  return AiChat02Icon
}

function AssistantIcon({ action }: { action: Extract<PageAction, { kind: "assistant" }> }) {
  return (
    <Image
      src={withFolioBasePath(action.icon)}
      alt=""
      width={16}
      height={16}
      unoptimized
      className={cn(
        "size-4 shrink-0 opacity-85 transition-opacity group-hover:opacity-100",
        action.invertIcon && "dark:invert"
      )}
    />
  )
}

function buildAssistantUrl(
  action: Extract<PageAction, { kind: "assistant" }>,
  prompt: string
) {
  const url = new URL(action.url)
  url.searchParams.set(action.promptParam, prompt)
  return url.toString()
}

function buildAssistantHref(action: Extract<PageAction, { kind: "assistant" }>) {
  const text = actionText(action)
  return buildAssistantUrl(action, text)
}

export function PageActionsButton() {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<string>("")
  const [assistantHref, setAssistantHref] = useState(
    CHATGPT_ACTION?.url || "https://chatgpt.com/"
  )
  const isSuccess = Boolean(status && status !== "Copy failed")

  const copyActionText = useCallback((action: PageAction) => {
    const text = actionText(action)
    void copyText(text)
      .then(() => {
        setStatus(actionStatus(action))
        window.setTimeout(() => setStatus(""), 2000)
      })
      .catch(() => {
        setStatus("Copy failed")
        window.setTimeout(() => setStatus(""), 2000)
      })
  }, [])

  const handleOpenChange = useCallback((nextOpen: boolean) => {
    if (nextOpen && CHATGPT_ACTION) {
      setAssistantHref(buildAssistantHref(CHATGPT_ACTION))
    }
    setOpen(nextOpen)
  }, [])

  const handleSelect = useCallback((action: PageAction) => {
    setOpen(false)
    if (action.kind === "view") {
      window.open(getMarkdownUrl(), "_blank", "noopener,noreferrer")
      return
    }

    copyActionText(action)
  }, [copyActionText])

  const handleAssistantSelect = useCallback(
    (action: Extract<PageAction, { kind: "assistant" }>) => {
      setOpen(false)
      copyActionText(action)
    },
    [copyActionText]
  )

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          title="Page actions"
          aria-label={status || "Ask AI page actions"}
          aria-expanded={open}
          className={cn(
            "data-[state=open]:bg-muted data-[state=open]:text-foreground",
            isSuccess && "text-primary hover:text-primary"
          )}
        >
          <HugeiconsIcon
            icon={isSuccess ? CopyCheckIcon : AiChat02Icon}
            size={16}
            strokeWidth={2}
            className="mr-1.5 size-4"
          />
          <span>Ask AI</span>
          <HugeiconsIcon
            icon={ArrowDown01Icon}
            size={12}
            strokeWidth={2}
            className="ml-1 size-3"
          />
          <span className="sr-only" aria-live="polite">
            {status}
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-44 p-1.5" align="end">
        <div role="menu" aria-label="Page actions" className="space-y-0.5">
          {PAGE_ACTIONS.map((action) => (
            <Fragment key={action.label}>
              {action.kind === "mcp" ? (
                <div className="-mx-1 my-1 h-px bg-border" />
              ) : null}
              {action.kind === "assistant" ? (
                <a
                  href={assistantHref}
                  role="menuitem"
                  onClick={() => handleAssistantSelect(action)}
                  className={cn(
                    "group flex h-8 w-full items-center gap-2 rounded-sm px-2 text-left",
                    "text-xs text-foreground outline-none transition-colors",
                    "hover:bg-accent hover:text-accent-foreground",
                    "focus-visible:bg-accent focus-visible:text-accent-foreground"
                  )}
                >
                  <AssistantIcon action={action} />
                  <span className="flex-1 truncate">{action.label}</span>
                  <HugeiconsIcon
                    icon={ArrowUpRight01Icon}
                    size={12}
                    strokeWidth={2}
                    className="ml-auto size-3 shrink-0 text-muted-foreground transition-colors group-hover:text-accent-foreground group-focus-visible:text-accent-foreground"
                  />
                </a>
              ) : (
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => handleSelect(action)}
                  className={cn(
                    "group flex h-8 w-full items-center gap-2 rounded-sm px-2 text-left",
                    "text-xs text-foreground outline-none transition-colors",
                    "hover:bg-accent hover:text-accent-foreground",
                    "focus-visible:bg-accent focus-visible:text-accent-foreground"
                  )}
                >
                  <HugeiconsIcon
                    icon={actionIcon(action)}
                    size={16}
                    strokeWidth={2}
                    className="size-4 shrink-0 text-muted-foreground transition-colors group-hover:text-accent-foreground group-focus-visible:text-accent-foreground"
                  />
                  <span className="flex-1 truncate">{action.label}</span>
                </button>
              )}
            </Fragment>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
