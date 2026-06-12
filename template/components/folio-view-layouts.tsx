import type { ReactNode } from "react"

interface PublicLayoutProps {
  title?: string
  eyebrow?: string
  description?: string
  children: ReactNode
}

export function PublicLayout({
  title,
  eyebrow,
  description,
  children,
}: PublicLayoutProps) {
  return (
    <main className="min-h-screen bg-background text-foreground">
      {(title || eyebrow || description) && (
        <section className="border-b border-border bg-card">
          <div className="mx-auto max-w-7xl px-6 py-12 sm:py-16">
            {eyebrow && (
              <p className="font-mono text-xs uppercase text-muted-foreground">
                {eyebrow}
              </p>
            )}
            {title && (
              <h1 className="mt-4 max-w-3xl text-4xl font-bold tracking-normal text-foreground sm:text-5xl">
                {title}
              </h1>
            )}
            {description && (
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </section>
      )}
      <section className="mx-auto max-w-7xl px-6 py-10">{children}</section>
    </main>
  )
}
