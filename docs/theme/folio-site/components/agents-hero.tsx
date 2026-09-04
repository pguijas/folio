"use client"

import {
  GitHubMark,
  isGitHubHref,
  LandingCommand,
} from "@/components/landing/actions"
import type { LandingLink } from "@/components/landing/types"

import { AgentsHeroChat } from "./agents-hero-chat"

/** Built to match the docs landing's heartbeat hero rather than to invent a
 * second treatment: the same column split, the same kicker, the same
 * headline scale, the same pair of rounded buttons, the same install strip
 * under them. One thing differs, and only because it has to. All four
 * shipped hero variants render a Docs-specific right panel, so this one
 * carries the agents animation, and it sits on the unbordered plate this
 * page uses for every figure rather than in the heartbeat hero's bordered
 * card. */
export function AgentsHero({
  kicker,
  headline,
  description,
  actionLinks,
  installCommands,
}: {
  kicker: string
  headline: string
  description: string
  actionLinks: LandingLink[]
  installCommands: string[]
}) {
  return (
    <section className="landing-surface border-b border-border/60">
      <div className="mx-auto grid max-w-site gap-12 px-6 pt-20 pb-16 sm:pt-24 lg:grid-cols-[minmax(0,0.94fr)_minmax(380px,1fr)] xl:gap-16">
        <div className="landing-hero-copy min-w-0 max-w-2xl">
          {/* The tracking is what made this read as a kicker, not the code face.
              JetBrains Mono is for commands, paths and program output; a product
              name and a version numeral are neither. */}
          <p className="landing-kicker text-[11.5px] font-semibold tracking-[0.14em] text-primary uppercase">
            {kicker}
          </p>
          <h1 className="mt-5 text-4xl leading-[1.02] font-extrabold text-foreground sm:text-5xl xl:text-6xl">
            {headline}
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-muted-foreground">
            {description}
          </p>

          <div
            className={`mt-8 grid w-full max-w-xl gap-3 ${
              actionLinks.length > 1 ? "grid-cols-2" : "grid-cols-1"
            }`}
          >
            {actionLinks.map((action) => (
              <a
                key={action.title}
                href={action.href}
                target={action.external ? "_blank" : undefined}
                rel={action.external ? "noopener noreferrer" : undefined}
                className={
                  action.primary
                    ? "inline-flex items-center justify-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground"
                    : "inline-flex items-center justify-center gap-2 rounded-md border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
                }
              >
                {isGitHubHref(action.href) ? (
                  <GitHubMark className="size-4" />
                ) : null}
                {action.title}
              </a>
            ))}
          </div>

          {installCommands.length > 0 ? (
            <LandingCommand
              installCommands={installCommands}
              className="mt-7 max-w-xl rounded-md"
            />
          ) : null}
        </div>

        {/* An unbordered tinted ground, the same one the kit's Plate gives every
            other figure on this page. The animation draws its own hairline
            panes, so a frame around it was a box holding three boxes, which is
            the thing this page removes everywhere else. */}
        <aside className="landing-artifact min-w-0 overflow-hidden rounded-xl bg-muted/45 dark:bg-muted/25 lg:flex lg:flex-col">
          <AgentsHeroChat />
        </aside>
      </div>
    </section>
  )
}
