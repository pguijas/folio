import Link from "next/link"
import { ThemeStyleBootstrap } from "@/components/theme-configurator"
import { folioDocs } from "@/lib/folio-template"

// Next marks a 404 noindex on its own; saying it here keeps the root
// layout's "index, follow" from contradicting it.
export const metadata = {
  title: "Page not found",
  robots: {
    index: false,
    follow: true,
  },
}

export default function NotFound() {
  const docsHref = `${folioDocs.routeBase.replace(/\/+$/, "")}/`

  return (
    <main
      id="main-content"
      className="flex min-h-[70vh] flex-col items-center justify-center gap-5 px-6 py-24 text-center"
    >
      <ThemeStyleBootstrap />
      <p className="font-mono text-sm text-muted-foreground">404</p>
      <h1 className="text-3xl font-semibold tracking-tight text-foreground">
        Page not found
      </h1>
      <p className="max-w-md text-muted-foreground">
        There is no page at this address. It may have moved, or the link may
        be mistyped.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link
          href={docsHref}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground no-underline transition-opacity hover:opacity-90"
        >
          Read the docs
        </Link>
        <Link
          href="/"
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground no-underline transition-colors hover:bg-muted"
        >
          Home
        </Link>
      </div>
    </main>
  )
}
