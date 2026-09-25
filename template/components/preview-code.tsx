"use client"

import React, { useId, type ReactElement, type ReactNode } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { FileCodeIcon, ViewIcon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

type PreviewCodeMode = "preview" | "code"

type PreviewCodeProps = {
  title?: string
  description?: string
  defaultMode?: PreviewCodeMode
  children: ReactNode
}

function isWhitespaceNode(child: ReactNode) {
  return typeof child === "string" && child.trim() === ""
}

function toMeaningfulChildren(children: ReactNode) {
  return React.Children.toArray(children).filter(
    (child) => !isWhitespaceNode(child)
  )
}

function elementProps(element: ReactElement) {
  return element.props as Record<string, unknown>
}

function classNameIncludesLanguage(className: unknown) {
  return (
    typeof className === "string" && /(?:^|\s)language-[\w-]+/.test(className)
  )
}

function classNameIncludesNextraCode(className: unknown) {
  return (
    typeof className === "string" &&
    /(?:^|\s)nextra-code(?:\s|$)/.test(className)
  )
}

function hasPreDescendant(node: ReactNode): boolean {
  if (!React.isValidElement(node)) return false
  if (node.type === "pre") return true

  const props = elementProps(node)
  return React.Children.toArray(props.children as ReactNode).some(
    hasPreDescendant
  )
}

function hasCodeSignal(element: ReactElement): boolean {
  const props = elementProps(element)
  if (props["data-language"] || classNameIncludesLanguage(props.className)) {
    return true
  }

  if (
    classNameIncludesNextraCode(props.className) &&
    hasPreDescendant(element)
  ) {
    return true
  }

  const nestedChildren = React.Children.toArray(props.children as ReactNode)
  return nestedChildren.some((child) => {
    if (!React.isValidElement(child)) return false
    const childProps = elementProps(child)
    return (
      childProps["data-language"] ||
      classNameIncludesLanguage(childProps.className)
    )
  })
}

function isCodeBlock(child: ReactNode): child is ReactElement {
  return React.isValidElement(child) && hasCodeSignal(child)
}

export function PreviewCode({
  title,
  description,
  defaultMode = "preview",
  children,
}: PreviewCodeProps) {
  const id = useId().replace(/:/g, "")
  const previewId = `${id}-preview`
  const codeId = `${id}-code`
  const previewLabelId = `${id}-preview-label`
  const codeLabelId = `${id}-code-label`
  const previewPanelId = `${id}-preview-panel`
  const codePanelId = `${id}-code-panel`
  const items = toMeaningfulChildren(children)
  const codeIndex = items.findIndex(isCodeBlock)
  const codeBlock = codeIndex === -1 ? null : (items[codeIndex] as ReactElement)
  const previewChildren =
    codeIndex === -1 ? items : items.filter((_, index) => index !== codeIndex)
  const tabClass = cn(
    "preview-code-tab inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-sm px-2.5 text-xs font-medium",
    "transition-colors outline-none"
  )

  return (
    <figure className="preview-code my-7 overflow-hidden rounded-lg border border-border bg-card">
      <input
        id={previewId}
        name={id}
        type="radio"
        className="preview-code-radio preview-code-radio--preview sr-only"
        defaultChecked={defaultMode === "preview"}
        aria-label="Preview"
        aria-controls={previewPanelId}
      />
      <input
        id={codeId}
        name={id}
        type="radio"
        className="preview-code-radio preview-code-radio--code sr-only"
        defaultChecked={defaultMode === "code"}
        aria-label="Code"
        aria-controls={codePanelId}
      />
      <figcaption className="flex flex-col items-start gap-3 border-b border-border bg-muted/35 px-4 py-3">
        <div
          role="radiogroup"
          aria-label={title ? `${title} example view` : "Example view"}
          className="inline-flex w-fit shrink-0 rounded-md border border-border bg-muted p-0.5"
        >
          <label
            id={previewLabelId}
            htmlFor={previewId}
            data-preview-code-tab="preview"
            className={tabClass}
          >
            <HugeiconsIcon icon={ViewIcon} size={14} strokeWidth={2} />
            <span>Preview</span>
          </label>
          <label
            id={codeLabelId}
            htmlFor={codeId}
            data-preview-code-tab="code"
            className={tabClass}
          >
            <HugeiconsIcon icon={FileCodeIcon} size={14} strokeWidth={2} />
            <span>Code</span>
          </label>
        </div>
        <div className="min-w-0">
          {title && (
            <h3 className="m-0 text-base font-semibold text-foreground">
              {title}
            </h3>
          )}
          {description && (
            <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      </figcaption>
      <div
        id={previewPanelId}
        role="region"
        aria-labelledby={previewLabelId}
        data-preview-code-panel="preview"
        className="preview-code-preview bg-background p-4 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0"
      >
        {previewChildren.length > 0 ? (
          previewChildren
        ) : (
          <p className="m-0 text-sm text-muted-foreground">
            Preview unavailable.
          </p>
        )}
      </div>
      <div
        id={codePanelId}
        role="region"
        aria-labelledby={codeLabelId}
        data-preview-code-panel="code"
        className="preview-code-source bg-background [&_pre]:!m-0 [&_pre]:!rounded-none [&_pre]:!border-0"
      >
        {codeBlock ? (
          codeBlock
        ) : (
          <pre className="m-0 overflow-auto bg-transparent p-4 font-mono text-xs leading-6 text-foreground">
            <code>No source provided.</code>
          </pre>
        )}
      </div>
    </figure>
  )
}
