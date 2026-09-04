"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface Tab {
  label: string
  children: React.ReactNode
}

interface TabItemProps {
  label: string
  children: React.ReactNode
}

interface TabsProps {
  children: React.ReactNode
  "aria-label"?: string
}

export function Tabs({
  children,
  "aria-label": ariaLabel = "Content tabs",
}: TabsProps) {
  const [activeIndex, setActiveIndex] = React.useState(0)
  const tabSetId = React.useId().replace(/:/g, "")
  const tabRefs = React.useRef<Array<HTMLButtonElement | null>>([])

  const tabs: Tab[] = []
  React.Children.forEach(children, (child) => {
    if (!React.isValidElement<TabItemProps>(child)) return

    const isTabItem =
      child.type === TabItem ||
      (child.type as { displayName?: string }).displayName === "TabItem" ||
      typeof child.props.label === "string"

    if (!isTabItem || typeof child.props.label !== "string") return

    tabs.push({ label: child.props.label, children: child.props.children })
  })

  if (tabs.length === 0) return null

  const activateTab = (index: number) => {
    setActiveIndex(index)
    tabRefs.current[index]?.focus()
  }

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    index: number
  ) => {
    let nextIndex: number | null = null

    if (event.key === "ArrowRight") {
      nextIndex = (index + 1) % tabs.length
    } else if (event.key === "ArrowLeft") {
      nextIndex = (index - 1 + tabs.length) % tabs.length
    } else if (event.key === "Home") {
      nextIndex = 0
    } else if (event.key === "End") {
      nextIndex = tabs.length - 1
    }

    if (nextIndex === null) return

    event.preventDefault()
    activateTab(nextIndex)
  }

  return (
    <div className="my-6 overflow-hidden rounded-lg border border-border">
      <div
        role="tablist"
        aria-label={ariaLabel}
        aria-orientation="horizontal"
        className="flex border-b border-border bg-muted/50"
      >
        {tabs.map((tab, i) => (
          <button
            key={i}
            ref={(node) => {
              tabRefs.current[i] = node
            }}
            id={`${tabSetId}-tab-${i}`}
            type="button"
            role="tab"
            aria-selected={i === activeIndex}
            aria-controls={`${tabSetId}-panel-${i}`}
            tabIndex={i === activeIndex ? 0 : -1}
            onClick={() => setActiveIndex(i)}
            onKeyDown={(event) => handleKeyDown(event, i)}
            className={cn(
              "relative px-4 py-2.5 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-inset",
              i === activeIndex
                ? "bg-background text-foreground"
                : "text-muted-foreground hover:bg-background/50 hover:text-foreground"
            )}
          >
            {tab.label}
            {i === activeIndex && (
              <span className="absolute right-0 bottom-0 left-0 h-0.5 bg-primary" />
            )}
          </button>
        ))}
      </div>
      {tabs.map((tab, i) => (
        <div
          key={i}
          id={`${tabSetId}-panel-${i}`}
          role="tabpanel"
          aria-labelledby={`${tabSetId}-tab-${i}`}
          tabIndex={0}
          hidden={i !== activeIndex}
          className="p-4 text-sm [&>p:first-child]:mt-0 [&>p:last-child]:mb-0"
        >
          {tab.children}
        </div>
      ))}
    </div>
  )
}

export function TabItem({ children }: TabItemProps) {
  return <>{children}</>
}

TabItem.displayName = "TabItem"
