"use client"

import { useCallback, useState, type ReactNode } from "react"
import { CopyCheckIcon, CopyIcon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { cn } from "@/lib/utils"

type TerminalStatus = "neutral" | "success" | "error"

interface TerminalSessionProps {
  command: string
  output?: string | string[]
  cwd?: string
  title?: string
  prompt?: string
  status?: TerminalStatus
  children?: ReactNode
}

const statusStyles: Record<TerminalStatus, string> = {
  neutral: "bg-muted-foreground/45",
  success: "bg-primary",
  error: "bg-destructive",
}

function lines(value?: string | string[]) {
  if (!value) return []
  return Array.isArray(value) ? value : value.trim().split("\n")
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {}
  }

  const textarea = document.createElement("textarea")
  textarea.value = text
  textarea.setAttribute("readonly", "")
  textarea.style.position = "fixed"
  textarea.style.top = "-9999px"
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand("copy")
  document.body.removeChild(textarea)
  return copied
}

export function TerminalSession({
  command,
  output,
  cwd,
  title = "Terminal",
  prompt = "$",
  status = "neutral",
  children,
}: TerminalSessionProps) {
  const outputLines = lines(output)
  const [copied, setCopied] = useState(false)

  const copyCommand = useCallback(() => {
    void copyText(command).then((didCopy) => {
      if (didCopy) {
        setCopied(true)
        window.setTimeout(() => setCopied(false), 1600)
      }
    })
  }, [command])

  return (
    <figure className="my-6 overflow-hidden rounded-lg border border-border bg-card">
      <figcaption className="flex items-center justify-between gap-3 border-b border-border bg-muted/40 px-4 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <button
            type="button"
            onClick={copyCommand}
            aria-label={`Copy command: ${title}`}
            title={copied ? "Copied command" : "Copy command"}
            className={cn(
              "inline-flex size-7 shrink-0 items-center justify-center rounded-md border border-border bg-background/70 text-muted-foreground",
              "transition-colors duration-150 hover:bg-muted hover:text-foreground",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
              copied && "border-primary/50 text-primary"
            )}
          >
            <HugeiconsIcon
              icon={copied ? CopyCheckIcon : CopyIcon}
              size={14}
              strokeWidth={2}
            />
          </button>
          <span
            className={cn(
              "h-2.5 w-2.5 shrink-0 rounded-full",
              statusStyles[status]
            )}
            aria-hidden="true"
          />
          <span className="truncate text-sm font-medium text-foreground">
            {title}
          </span>
        </div>
        {cwd && (
          <span className="truncate font-mono text-xs text-muted-foreground">
            {cwd}
          </span>
        )}
      </figcaption>
      <pre className="m-0 overflow-x-auto !rounded-none !border-0 bg-transparent p-4 font-mono text-sm leading-6 !shadow-none">
        <code>
          <span className="text-muted-foreground select-none">{prompt} </span>
          <span className="text-foreground">{command}</span>
          {outputLines.length > 0 && (
            <>
              {"\n"}
              {outputLines.map((line, index) => (
                <span key={index} className="block text-foreground/75">
                  {line}
                </span>
              ))}
            </>
          )}
        </code>
      </pre>
      {children && (
        <div className="border-t border-border bg-muted/20 px-4 py-3 text-sm text-muted-foreground [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
          {children}
        </div>
      )}
    </figure>
  )
}
