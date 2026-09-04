"use client"

import { useState, useCallback } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { ThumbsUpIcon, ThumbsDownIcon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

export function PageFeedback() {
  const [submitted, setSubmitted] = useState(false)
  const [choice, setChoice] = useState<boolean | null>(null)

  const handleFeedback = useCallback((helpful: boolean) => {
    const path = window.location.pathname
    const feedback = JSON.parse(localStorage.getItem("page-feedback") || "{}")
    feedback[path] = { helpful, timestamp: Date.now() }
    localStorage.setItem("page-feedback", JSON.stringify(feedback))
    setChoice(helpful)
    setSubmitted(true)
  }, [])

  return (
    <div
      className={cn(
        "flex items-center justify-center gap-3 mt-12 mb-4 py-5",
        "border-t border-border"
      )}
    >
      {submitted ? (
        <p className="text-sm text-muted-foreground transition-opacity duration-200">
          {choice ? "Glad it helped." : "Thanks, we'll improve this page."}
        </p>
      ) : (
        <>
          <span className="text-sm text-muted-foreground">
            Was this page helpful?
          </span>
          <div className="flex gap-1.5">
            <button
              onClick={() => handleFeedback(true)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-3.5 py-2.5",
                "text-sm text-muted-foreground border border-border",
                "transition-all duration-150",
                "hover:text-primary hover:border-primary/30 hover:bg-primary/5"
              )}
            >
              <HugeiconsIcon icon={ThumbsUpIcon} size={14} strokeWidth={2} />
              Yes
            </button>
            <button
              onClick={() => handleFeedback(false)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-3.5 py-2.5",
                "text-sm text-muted-foreground border border-border",
                "transition-all duration-150",
                "hover:text-foreground hover:border-foreground/20 hover:bg-muted"
              )}
            >
              <HugeiconsIcon icon={ThumbsDownIcon} size={14} strokeWidth={2} />
              No
            </button>
          </div>
        </>
      )}
    </div>
  )
}
