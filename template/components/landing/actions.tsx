"use client"

import { useCallback, useState } from "react"

import type { LandingLink } from "@/components/landing/types"

export function normalizeLandingHref(href: string) {
  return href.startsWith("/") ? `.${href}` : href
}

export function isGitHubHref(href: string) {
  return /^https?:\/\/(www\.)?github\.com(\/|$)/.test(href)
}

export function GitHubMark({ className = "size-4" }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className={className}
    >
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.03 1.76 2.69 1.25 3.35.96.1-.75.4-1.25.72-1.54-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.18-3.09-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.18a10.9 10.9 0 0 1 2.87-.39c.97 0 1.95.13 2.87.39 2.19-1.49 3.15-1.18 3.15-1.18.62 1.59.23 2.76.11 3.05.73.81 1.18 1.83 1.18 3.09 0 4.41-2.69 5.38-5.25 5.67.41.35.77 1.05.77 2.12 0 1.53-.01 2.76-.01 3.14 0 .3.2.66.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
    </svg>
  )
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
          <span className="flex items-center gap-1.5 text-sm font-semibold">
            {isGitHubHref(action.href) ? (
              <GitHubMark className="size-3.5" />
            ) : null}
            {action.title}
          </span>
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
      className={`landing-command relative flex w-full items-center justify-between gap-4 border border-border bg-card px-4 py-3 ${className}`}
    >
      <div className="landing-command-scroll min-w-0 flex-1 overflow-x-auto">
        {installCommands.map((command) => (
          <code
            key={command}
            className="block font-mono text-xs leading-6 whitespace-nowrap text-foreground"
          >
            <span className="text-muted-foreground">$ </span>
            {command}
          </code>
        ))}
      </div>
      {/* On phones the command always overflows; the scrollbar is hidden, so
          fade the clipped edge to signal there is more to scroll. */}
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-px right-16 w-10 bg-gradient-to-l from-card sm:hidden"
      />
      <CopyButton text={installCommands.join("\n")} />
    </div>
  )
}
