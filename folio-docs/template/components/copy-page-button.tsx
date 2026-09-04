"use client"

import { useState, useCallback } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { CopyIcon, CopyCheckIcon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

export function CopyPageButton() {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    const content = document.querySelector("article")?.innerText
    if (content) {
      navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [])

  return (
    <button
      onClick={handleCopy}
      title="Copy page content"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5",
        "text-xs font-medium text-muted-foreground",
        "transition-all duration-150",
        "hover:text-foreground hover:bg-muted",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        copied && "text-primary"
      )}
    >
      <HugeiconsIcon
        icon={copied ? CopyCheckIcon : CopyIcon}
        size={14}
        strokeWidth={2}
      />
      <span>{copied ? "Copied" : "Copy"}</span>
    </button>
  )
}
