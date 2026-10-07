"use client"

import { useConfig, useThemeConfig } from "nextra-theme-docs"

type FeedbackConfig = ReturnType<typeof useThemeConfig>["feedback"]

export function feedbackHref(
  feedback: FeedbackConfig,
  repository: string,
  pageTitle?: string,
): string | null {
  if (!feedback.content) return null
  if (feedback.link != null) return feedback.link

  const { origin, pathname } = new URL(repository)
  const [, owner, name] = pathname.split("/", 3)
  const title = encodeURIComponent(`Feedback for “${pageTitle}”`)
  const { labels } = feedback
  if (origin.includes("gitlab")) {
    const description = labels ? `&issue[description]=/label${encodeURIComponent(` ~${labels}\n`)}` : ""
    return `${origin}/${owner}/${name}/-/issues/new?issue[title]=${title}${description}`
  }
  if (origin.includes("github")) {
    return `${origin}/${owner}/${name}/issues/new?title=${title}&labels=${labels || ""}`
  }
  return "#"
}

export function FloatingFeedback() {
  const { feedback, docsRepositoryBase } = useThemeConfig()
  const { activeMetadata } = useConfig().normalizePagesResult
  const href = feedbackHref(feedback, docsRepositoryBase, activeMetadata?.title)
  if (href === null) return null

  return <a className="folioh-feedback" href={href} target="_blank" rel="noreferrer">Feedback</a>
}
