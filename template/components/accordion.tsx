"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Accordion({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-accordion-root
      className="my-6 divide-y divide-border overflow-hidden rounded-lg border border-border"
    >
      {children}
    </div>
  )
}

export function AccordionItem({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = React.useState(defaultOpen)
  const itemId = React.useId().replace(/:/g, "")
  const triggerId = `${itemId}-trigger`
  const panelId = `${itemId}-panel`

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (
      event.key !== "ArrowDown" &&
      event.key !== "ArrowUp" &&
      event.key !== "Home" &&
      event.key !== "End"
    ) {
      return
    }

    const root = event.currentTarget.closest("[data-accordion-root]")
    if (!root) return

    const triggers = Array.from(
      root.querySelectorAll<HTMLButtonElement>("[data-accordion-trigger]")
    ).filter(
      (trigger) =>
        !trigger.disabled && trigger.closest("[data-accordion-root]") === root
    )
    const currentIndex = triggers.indexOf(event.currentTarget)
    if (currentIndex === -1) return

    let nextIndex = currentIndex
    if (event.key === "ArrowDown") {
      nextIndex = (currentIndex + 1) % triggers.length
    } else if (event.key === "ArrowUp") {
      nextIndex = (currentIndex - 1 + triggers.length) % triggers.length
    } else if (event.key === "Home") {
      nextIndex = 0
    } else if (event.key === "End") {
      nextIndex = triggers.length - 1
    }

    event.preventDefault()
    triggers[nextIndex]?.focus()
  }

  return (
    <div>
      <button
        id={triggerId}
        data-accordion-trigger
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleKeyDown}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-inset"
      >
        {title}
        <svg
          aria-hidden="true"
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200",
            open && "rotate-180"
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      <div
        id={panelId}
        role="region"
        aria-labelledby={triggerId}
        hidden={!open}
        className="px-4 pb-4 text-sm text-muted-foreground [&>p:first-child]:mt-0 [&>p:last-child]:mb-0"
      >
        {children}
      </div>
    </div>
  )
}

AccordionItem.displayName = "AccordionItem"
