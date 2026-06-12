"use client"

import { useCallback, useState } from "react"

import type { LandingLink } from "@/components/landing/types"

export function normalizeLandingHref(href: string) {
  return href.startsWith("/") ? `.${href}` : href
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [text])

  return (
    <button
      onClick={handleCopy}
      className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      aria-label="Copy install commands"
    >
      {copied ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
          <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
        </svg>
      )}
    </button>
  )
}

export function LandingActions({
  actionLinks,
  actionGridClassName,
}: {
  actionLinks: LandingLink[]
  actionGridClassName: string
}) {
  return (
    <div className={actionGridClassName}>
      {actionLinks.map((action, index) => (
        <a
          key={action.title}
          href={action.href}
          target={action.external ? "_blank" : undefined}
          rel={action.external ? "noopener noreferrer" : undefined}
          className={
            action.primary
              ? "landing-action landing-action-primary"
              : "landing-action"
          }
          style={{ animationDelay: `${140 + index * 70}ms` }}
        >
          <span className="font-mono text-[10px] text-current opacity-55">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="text-sm font-semibold">{action.title}</span>
          {action.detail ? (
            <span className="text-xs opacity-70">{action.detail}</span>
          ) : null}
        </a>
      ))}
    </div>
  )
}

export function LandingCommand({
  installCommands,
  className = "",
}: {
  installCommands: string[]
  className?: string
}) {
  if (installCommands.length === 0) {
    return null
  }

  return (
    <div
      className={`landing-command flex w-full items-center justify-between gap-4 border border-border bg-card px-4 py-3 ${className}`}
    >
      <code className="truncate font-mono text-sm text-foreground">
        <span className="text-muted-foreground">$ </span>
        {installCommands[0]}
      </code>
      <CopyButton text={installCommands.join("\n")} />
    </div>
  )
}
