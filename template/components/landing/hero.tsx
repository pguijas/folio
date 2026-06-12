"use client"

import { LandingActions, LandingCommand } from "@/components/landing/actions"
import { defaultRoutes } from "@/components/landing/defaults"
import type { LandingLink, LandingPipelineStep } from "@/components/landing/types"

type LandingHeroProps = {
  tagline: string
  headline: string
  description: string
  actionLinks: LandingLink[]
  actionGridClassName: string
  installCommands: string[]
  buildSteps: LandingPipelineStep[]
}

type LandingHeroCopyProps = Omit<LandingHeroProps, "buildSteps"> & {
  className?: string
}

function LandingHeroCopy({
  tagline,
  headline,
  description,
  actionLinks,
  actionGridClassName,
  installCommands,
  className,
}: LandingHeroCopyProps) {
  const copyClassName = [
    "landing-hero-copy max-w-3xl min-w-0",
    className,
  ]
    .filter(Boolean)
    .join(" ")

  return (
    <div className={copyClassName}>
      <p className="landing-kicker font-mono text-xs text-primary uppercase">
        {tagline}
      </p>
      <h1 className="mt-5 text-[2.35rem] leading-[0.94] font-extrabold text-foreground sm:text-6xl xl:text-[4.55rem]">
        {headline}
      </h1>
      <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground sm:text-xl">
        {description}
      </p>
      <LandingActions
        actionLinks={actionLinks}
        actionGridClassName={actionGridClassName}
      />
      <LandingCommand
        installCommands={installCommands}
        className="mt-6 max-w-2xl sm:mt-8"
      />
    </div>
  )
}

export function DocsMapLandingHero({
  tagline,
  headline,
  description,
  actionLinks,
  actionGridClassName,
  installCommands,
}: LandingHeroProps) {
  return (
    <section className="landing-surface border-b border-border">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 pt-24 pb-16 sm:pt-28 lg:min-h-[700px] lg:grid-cols-[minmax(0,0.9fr)_minmax(340px,0.72fr)] lg:items-end xl:gap-16">
        <LandingHeroCopy
          tagline={tagline}
          headline={headline}
          description={description}
          actionLinks={actionLinks}
          actionGridClassName={actionGridClassName}
          installCommands={installCommands}
          className="pb-4 lg:pb-16"
        />

        <aside
          className="border border-border bg-card"
          aria-label="Documentation routes"
        >
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <p className="font-mono text-[10px] text-muted-foreground uppercase">
              Documentation routes
            </p>
            <span className="size-2 bg-primary" aria-hidden="true" />
          </div>

          <div className="grid gap-px bg-border">
            {defaultRoutes.map((route, index) => (
              <a
                key={route.path}
                href={route.href}
                className="group grid grid-cols-[4.5rem_1fr] gap-4 bg-card px-5 py-5 transition-colors hover:bg-muted/50"
                style={{ animationDelay: `${220 + index * 80}ms` }}
              >
                <span className="font-mono text-xs font-semibold text-primary">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span>
                  <span className="block text-base font-semibold text-foreground">
                    {route.label}
                  </span>
                  <span className="mt-2 block font-mono text-[11px] text-muted-foreground">
                    {route.path}
                  </span>
                  <span className="mt-3 block text-sm leading-6 text-muted-foreground">
                    {route.detail}
                  </span>
                </span>
              </a>
            ))}
          </div>

          <div className="grid gap-px bg-border sm:grid-cols-3">
            {["docs.yaml", "Markdown", "Python"].map((item) => (
              <div key={item} className="bg-card p-5">
                <span className="font-mono text-[10px] text-muted-foreground uppercase">
                  input
                </span>
                <p className="mt-3 text-sm font-semibold text-foreground">
                  {item}
                </p>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </section>
  )
}

export function SourcePipelineLandingHero({
  tagline,
  headline,
  description,
  actionLinks,
  actionGridClassName,
  installCommands,
  buildSteps,
}: LandingHeroProps) {
  return (
    <section className="landing-surface border-b border-border">
      <div className="mx-auto grid max-w-7xl gap-12 px-6 pt-24 pb-20 sm:pt-28 lg:min-h-[760px] lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.78fr)] lg:items-center xl:gap-16">
        <LandingHeroCopy
          tagline={tagline}
          headline={headline}
          description={description}
          actionLinks={actionLinks}
          actionGridClassName={actionGridClassName}
          installCommands={installCommands}
        />

        <aside
          className="landing-artifact border border-border bg-card"
          aria-label="Build pipeline overview"
        >
          <div className="landing-artifact-top flex items-center justify-between gap-4 border-b border-border px-5 py-4">
            <div className="flex items-center gap-2 font-mono text-[10px] text-muted-foreground uppercase">
              <span className="size-2 bg-primary" aria-hidden="true" />
              source
              <span className="text-border">/</span>
              site
            </div>
            <span className="font-mono text-[10px] text-muted-foreground uppercase">
              build ready
            </span>
          </div>

          <div className="landing-artifact-stage grid gap-px bg-border md:grid-cols-[0.95fr_1.05fr]">
            <div className="bg-card p-5">
              <p className="font-mono text-[10px] text-muted-foreground uppercase">
                Python source
              </p>
              <div className="mt-5 space-y-2 font-mono text-xs">
                <div className="landing-code-line w-[76%]" />
                <div className="landing-code-line w-[58%]" />
                <div className="landing-code-line w-[88%]" />
                <div className="landing-code-line landing-code-line-muted w-[64%]" />
                <div className="landing-code-line w-[44%]" />
              </div>
            </div>

            <div className="relative overflow-hidden bg-card p-5">
              <div className="landing-scan" aria-hidden="true" />
              <p className="font-mono text-[10px] text-muted-foreground uppercase">
                Generated docs
              </p>
              <div className="mt-5 space-y-3">
                <div className="h-6 w-3/4 bg-foreground" />
                <div className="h-2 w-full bg-muted" />
                <div className="h-2 w-5/6 bg-muted" />
                <div className="grid grid-cols-3 gap-2 pt-2">
                  <span className="h-8 border border-border bg-background" />
                  <span className="h-8 border border-border bg-background" />
                  <span className="h-8 border border-border bg-background" />
                </div>
              </div>
            </div>
          </div>

          <ol className="landing-sequence divide-y divide-border">
            {buildSteps.map((step) => (
              <li
                key={step.label}
                className="grid grid-cols-[3rem_1fr] gap-4 px-5 py-5"
                style={{ animationDelay: `${240 + Number(step.label) * 90}ms` }}
              >
                <span className="font-mono text-xs font-semibold text-primary">
                  {step.label}
                </span>
                <div>
                  <h3 className="text-base font-semibold text-foreground">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {step.detail}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </section>
  )
}
