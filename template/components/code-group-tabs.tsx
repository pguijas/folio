"use client"

import React from "react"
import { cn } from "@/lib/utils"

// The tab strip of a CodeGroup. The labels come from the server-side
// CodeGroup, which can still read each block's language.
export function CodeGroupTabs({
  labels,
  children,
}: {
  labels: string[]
  children: React.ReactNode
}) {
  const [active, setActive] = React.useState(0)
  const codeGroupId = React.useId().replace(/:/g, "")
  const tabRefs = React.useRef<Array<HTMLButtonElement | null>>([])

  const blocks: { label: string; content: React.ReactNode }[] = []

  React.Children.forEach(children, (child) => {
    if (!React.isValidElement(child)) return
    const label = labels[blocks.length] || `Tab ${blocks.length + 1}`
    blocks.push({ label, content: child })
  })

  if (blocks.length === 0) return <>{children}</>

  const activateTab = (index: number) => {
    setActive(index)
    tabRefs.current[index]?.focus()
  }

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    index: number
  ) => {
    let nextIndex: number | null = null

    if (event.key === "ArrowRight") {
      nextIndex = (index + 1) % blocks.length
    } else if (event.key === "ArrowLeft") {
      nextIndex = (index - 1 + blocks.length) % blocks.length
    } else if (event.key === "Home") {
      nextIndex = 0
    } else if (event.key === "End") {
      nextIndex = blocks.length - 1
    }

    if (nextIndex === null) return

    event.preventDefault()
    activateTab(nextIndex)
  }

  return (
    <div className="my-5 rounded-lg border border-border overflow-hidden bg-card">
      <div role="tablist" className="flex border-b border-border bg-muted/40">
        {blocks.map((block, i) => (
          <button
            key={i}
            ref={(node) => {
              tabRefs.current[i] = node
            }}
            id={`${codeGroupId}-tab-${i}`}
            type="button"
            role="tab"
            aria-selected={i === active}
            aria-controls={`${codeGroupId}-panel-${i}`}
            tabIndex={i === active ? 0 : -1}
            onClick={() => setActive(i)}
            onKeyDown={(e) => handleKeyDown(e, i)}
            className={cn(
              "relative px-4 py-2 text-sm font-medium transition-colors duration-150",
              "hover:text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
              i === active ? "text-primary" : "text-muted-foreground"
            )}
          >
            {block.label}
            {i === active && (
              <span className="absolute inset-x-0 bottom-0 h-0.5 bg-primary rounded-full" />
            )}
          </button>
        ))}
      </div>
      {blocks.map((block, i) => (
        <div
          key={i}
          role="tabpanel"
          id={`${codeGroupId}-panel-${i}`}
          aria-labelledby={`${codeGroupId}-tab-${i}`}
          tabIndex={0}
          hidden={i !== active}
          className="[&_pre]:!my-0 [&_pre]:!rounded-none [&_pre]:!border-0"
        >
          {block.content}
        </div>
      ))}
    </div>
  )
}
