"use client"

import { useEffect, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const FOLIO_BASE_PATH =
  process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\/+$/, "") ?? ""

interface PreviewEntry {
  name: string
  href: string
  title: string
  pr_number: string
  branch: string
  commit: string
  commit_url: string
  pr_url: string
  repo: string
  repo_url: string
  author: string
  author_url: string
  avatar_url: string
  updated_at: string
}

type LoadState = "loading" | "ready" | "error"

function formatDate(value: string): string {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function PreviewCard({ entry }: { entry: PreviewEntry }) {
  const heading = entry.title || entry.name
  return (
    <Card className="transition-colors hover:border-primary/60">
      <CardHeader>
        <div className="flex items-start gap-3">
          {entry.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={entry.avatar_url}
              alt={entry.author ? `@${entry.author}` : ""}
              width={40}
              height={40}
              className="mt-0.5 size-10 shrink-0 rounded-full border border-border"
            />
          ) : null}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              {entry.pr_number ? (
                <Badge variant="secondary" className="font-mono">
                  #{entry.pr_number}
                </Badge>
              ) : null}
              <CardTitle className="truncate text-base">{heading}</CardTitle>
            </div>
            {entry.author ? (
              <p className="mt-1 text-xs text-muted-foreground">
                by{" "}
                {entry.author_url ? (
                  <a
                    href={entry.author_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground hover:underline"
                  >
                    @{entry.author}
                  </a>
                ) : (
                  <span>@{entry.author}</span>
                )}
              </p>
            ) : null}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-wrap gap-x-6 gap-y-1.5 text-xs text-muted-foreground">
        {entry.branch ? (
          <span className="inline-flex items-center gap-1.5">
            <span className="text-muted-foreground/70">Branch</span>
            <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-foreground/90">
              {entry.branch}
            </code>
          </span>
        ) : null}
        {entry.commit ? (
          <span className="inline-flex items-center gap-1.5">
            <span className="text-muted-foreground/70">Commit</span>
            {entry.commit_url ? (
              <a
                href={entry.commit_url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-foreground/90 hover:text-primary hover:underline"
              >
                {entry.commit.slice(0, 7)}
              </a>
            ) : (
              <code className="font-mono text-foreground/90">
                {entry.commit.slice(0, 7)}
              </code>
            )}
          </span>
        ) : null}
        {entry.updated_at ? (
          <span className="inline-flex items-center gap-1.5">
            <span className="text-muted-foreground/70">Updated</span>
            <time dateTime={entry.updated_at}>{formatDate(entry.updated_at)}</time>
          </span>
        ) : null}
      </CardContent>

      <CardFooter className="gap-2">
        <Button asChild size="sm">
          <a href={entry.href}>Open preview</a>
        </Button>
        {entry.pr_url ? (
          <Button asChild size="sm" variant="ghost">
            <a href={entry.pr_url} target="_blank" rel="noopener noreferrer">
              View pull request ↗
            </a>
          </Button>
        ) : null}
      </CardFooter>
    </Card>
  )
}

export function PreviewsList() {
  const [entries, setEntries] = useState<PreviewEntry[]>([])
  const [state, setState] = useState<LoadState>("loading")

  useEffect(() => {
    let cancelled = false
    fetch(`${FOLIO_BASE_PATH}/previews/previews.json`, { cache: "no-store" })
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((data: PreviewEntry[]) => {
        if (cancelled) return
        setEntries(Array.isArray(data) ? data : [])
        setState("ready")
      })
      .catch(() => {
        if (!cancelled) setState("error")
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (state === "loading") {
    return <p className="text-sm text-muted-foreground">Loading previews…</p>
  }

  if (state === "error" || entries.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-10 text-center text-sm text-muted-foreground">
        No branch previews are deployed right now.
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {entries.map((entry) => (
        <PreviewCard key={entry.name} entry={entry} />
      ))}
    </div>
  )
}
