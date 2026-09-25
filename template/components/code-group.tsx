import React from "react"
import { CodeGroupTabs } from "@/components/code-group-tabs"

function extractLabel(child: React.ReactElement, index: number): string {
  const props = child.props as Record<string, unknown>
  if (props.title) return props.title as string
  if (props["data-language"]) return props["data-language"] as string

  const className = (props.className as string) || ""
  const langMatch = className.match(/language-(\w+)/)
  if (langMatch) return langMatch[1]

  // Recurse into nested children to find a code/pre with language info
  const nested = props.children
  if (React.isValidElement(nested)) {
    const nestedProps = (nested as React.ReactElement).props as Record<string, unknown>
    if (nestedProps["data-language"]) return nestedProps["data-language"] as string
    const nestedClass = (nestedProps.className as string) || ""
    const nestedMatch = nestedClass.match(/language-(\w+)/)
    if (nestedMatch) return nestedMatch[1]
  }

  return `Tab ${index + 1}`
}

// A server component on purpose: here the children are still the MDX code
// block elements, whose data-language names each tab. A client component
// receives Nextra's rendered code block instead, which carries no language,
// so every tab fell back to "Tab N".
export function CodeGroup({
  labels,
  children,
}: {
  labels?: string[]
  children: React.ReactNode
}) {
  const tabLabels: string[] = []
  React.Children.forEach(children, (child) => {
    if (!React.isValidElement(child)) return
    const index = tabLabels.length
    tabLabels.push(labels?.[index] || extractLabel(child, index))
  })
  return <CodeGroupTabs labels={tabLabels}>{children}</CodeGroupTabs>
}
