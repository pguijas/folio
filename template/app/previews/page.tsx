import type { Metadata } from "next"

import { PreviewsList } from "@/components/previews-list"

export const metadata: Metadata = {
  title: "Branch previews",
  description: "Documentation preview builds for open pull requests.",
  robots: { index: false, follow: false },
}

export default function PreviewsPage() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Branch previews
        </h1>
        <p className="mt-2 text-muted-foreground">
          Documentation preview builds for open pull requests. Previews are
          garbage-collected automatically once their pull request is merged or
          closed.
        </p>
      </header>

      <PreviewsList />
    </section>
  )
}
