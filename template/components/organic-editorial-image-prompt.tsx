"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

export const DEFAULT_ORGANIC_EDITORIAL_PROMPT =
  "Create an abstract editorial image for an internal AI training program. Use cobalt blue organic forms suspended on a warm white photographic field, soft pigment diffusion, subtle analog film grain, generous negative space, premium institutional art direction, no typography, no logos, no UI, no people, no devices. The image should feel tactile, calm, technical, and refined. Composition: wide crop, irregular biomorphic shapes, crisp white margins, gallery poster quality."

export function OrganicEditorialImagePrompt({
  title = "Organic Editorial image prompt",
  prompt = DEFAULT_ORGANIC_EDITORIAL_PROMPT,
  model = "Image model",
  ratio = "16:9",
  className,
}: {
  title?: string
  prompt?: string
  model?: string
  ratio?: string
  className?: string
}) {
  const [copied, setCopied] = useState(false)

  async function copyPrompt() {
    await navigator.clipboard.writeText(prompt)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }

  return (
    <figure
      className={cn(
        "my-8 overflow-hidden rounded-md border border-border bg-card text-card-foreground",
        "shadow-[0_18px_60px_-48px_var(--foreground)]",
        className
      )}
    >
      <div className="border-b border-border px-4 py-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <figcaption className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Organic Editorial
            </figcaption>
            <h3 className="mt-1 text-base font-semibold text-foreground">{title}</h3>
          </div>
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-muted-foreground">
            <span>{model}</span>
            <span className="h-3 w-px bg-border" aria-hidden="true" />
            <span>{ratio}</span>
          </div>
        </div>
      </div>

      <div className="grid gap-0 md:grid-cols-[minmax(0,1fr)_12rem]">
        <pre className="m-0 min-h-40 overflow-x-auto whitespace-pre-wrap border-0 bg-background p-4 text-sm leading-relaxed text-foreground">
          <code>{prompt}</code>
        </pre>
        <div className="flex flex-col justify-between border-t border-border bg-muted/45 p-4 md:border-l md:border-t-0">
          <p className="text-xs leading-5 text-muted-foreground">
            Use this prompt in an image-generation model, then place the generated bitmap as a hero or section image.
          </p>
          <button
            type="button"
            onClick={copyPrompt}
            className={cn(
              "mt-4 h-9 border border-border bg-background px-3 text-xs font-semibold text-foreground transition-colors",
              "hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            )}
          >
            {copied ? "Copied" : "Copy prompt"}
          </button>
        </div>
      </div>
    </figure>
  )
}
