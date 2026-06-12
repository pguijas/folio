import type { ReactElement } from "react"

import { ComparisonMatrix } from "@/components/comparison-matrix"
import { LandingCommand, normalizeLandingHref } from "@/components/landing/actions"
import { defaultRoutes } from "@/components/landing/defaults"
import type {
  LandingCatalogItem,
  LandingLink,
  LandingPipelineStep,
  LandingSection,
  LandingSectionContext,
  LandingSectionType,
} from "@/components/landing/types"

type LandingSectionComponent = (props: {
  section: LandingSection
  context: LandingSectionContext
}) => ReactElement | null

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description?: string
}) {
  return (
    <div>
      <p className="font-mono text-xs text-primary uppercase">{eyebrow}</p>
      <h2 className="mt-4 text-3xl font-bold text-foreground sm:text-4xl">
        {title}
      </h2>
      {description ? (
        <p className="mt-5 max-w-md text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      ) : null}
    </div>
  )
}

function normalizeAction(action: LandingLink): LandingLink {
  return {
    ...action,
    href: normalizeLandingHref(action.href),
    external: action.external ?? action.href.startsWith("http"),
  }
}

function FeaturesSection({ section }: { section: LandingSection }) {
  const features = section.features ?? []
  if (features.length === 0) {
    return null
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Capability stack"}
          title={section.title ?? "Less configuration, more finished docs."}
          description={section.description}
        />

        <div className="border-y border-border">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="grid gap-4 border-b border-border py-5 last:border-b-0 sm:grid-cols-[4rem_1fr]"
            >
              <span className="font-mono text-xs text-muted-foreground">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="text-base font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function ComparisonSection({ section }: { section: LandingSection }) {
  return (
    <section className="comparison-evidence comparison-evidence-surface landing-section border-b border-border bg-muted/20">
      <div className="mx-auto max-w-7xl px-6 py-20">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,0.58fr)_minmax(24rem,0.42fr)] lg:items-end">
          <div className="max-w-3xl">
            <SectionHeading
              eyebrow={section.eyebrow ?? "Comparison"}
              title={section.title ?? "Source-first docs, without the portal tax."}
              description={
                section.description ??
                "Folio covers the daily Python path: pdoc-level setup, guides, static export, LLM-friendly files, extensibility, open source, and CI-ready builds. Roadmap gaps stay on the roadmap."
              }
            />
            <a
              href="./roadmap/"
              className="mt-4 inline-flex text-sm font-semibold text-foreground underline decoration-foreground/30 underline-offset-4"
            >
              Roadmap
            </a>
          </div>
        </div>

        <ComparisonMatrix className="mt-10" includeSurface={false} />
      </div>
    </section>
  )
}

function OutputSection({ section }: { section: LandingSection }) {
  const items = section.items?.length
    ? section.items
    : [
        { title: "API reference" },
        { title: "Search" },
        { title: "LLM files" },
      ]

  return (
    <section className="landing-section mx-auto max-w-7xl px-6 py-20">
      <SectionHeading
        eyebrow={section.eyebrow ?? "Output"}
        title={section.title ?? "A finished docs site, not a pile of generated files."}
        description={section.description}
      />

      <div className="mt-10 grid gap-px overflow-hidden border border-border bg-border lg:grid-cols-[0.8fr_1.2fr]">
        <div className="bg-card p-6">
          <p className="font-mono text-[10px] text-muted-foreground uppercase">
            Ship target
          </p>
          <p className="mt-4 max-w-md text-lg leading-7 font-semibold text-foreground">
            Static export, search index, API reference, guides, and LLM files
            generated from one command.
          </p>
        </div>
        <div className="grid gap-px bg-border sm:grid-cols-3">
          {items.map((item) => (
            <div key={item.title ?? item.label} className="bg-card p-6">
              <span className="font-mono text-[10px] text-muted-foreground uppercase">
                {item.label ?? "included"}
              </span>
              <p className="mt-3 text-sm font-semibold text-foreground">
                {item.title}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function RoutesSection({ section }: { section: LandingSection }) {
  const routes = section.routes?.length ? section.routes : defaultRoutes

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Docs map"}
          title={section.title ?? "Generated routes stay predictable."}
          description={
            section.description ??
            "Guide pages, API reference, and static search output keep stable URLs."
          }
        />

        <div className="grid gap-px overflow-hidden border border-border bg-border sm:grid-cols-3">
          {routes.map((route) => (
            <a
              key={route.path}
              href={route.href}
              className="bg-card p-5 transition-colors hover:bg-muted/50"
            >
              <span className="font-mono text-[10px] text-muted-foreground uppercase">
                {route.label}
              </span>
              <p className="mt-3 font-mono text-xs text-primary">{route.path}</p>
              <p className="mt-4 text-sm leading-6 text-muted-foreground">
                {route.detail}
              </p>
            </a>
          ))}
        </div>
      </div>
    </section>
  )
}

function PipelineSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const steps: LandingPipelineStep[] = section.steps?.length
    ? section.steps
    : context.buildSteps
  if (steps.length === 0) {
    return null
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Pipeline"}
          title={section.title ?? "Source turns into a deployable docs site."}
          description={section.description}
        />

        <ol className="border-y border-border">
          {steps.map((step) => (
            <li
              key={step.label}
              className="grid gap-4 border-b border-border py-5 last:border-b-0 sm:grid-cols-[4rem_1fr]"
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
      </div>
    </section>
  )
}

function InstallSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const commands = section.commands?.length
    ? section.commands
    : context.installCommands

  return (
    <section className="landing-section border-b border-border bg-muted/20">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Install"}
          title={section.title ?? "Start with the same commands locally and in CI."}
          description={section.description}
        />
        <LandingCommand installCommands={commands} />
      </div>
    </section>
  )
}

function StatsSection({ section }: { section: LandingSection }) {
  const items = section.items ?? []
  if (items.length === 0) {
    return null
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Proof"}
          title={section.title ?? "A small surface for measurable proof."}
          description={section.description}
        />
        <div className="grid gap-px overflow-hidden border border-border bg-border sm:grid-cols-3">
          {items.map((item) => (
            <div key={`${item.value}-${item.label}`} className="bg-card p-6">
              <p className="text-3xl font-bold text-foreground">
                {item.value}
              </p>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {item.label ?? item.title}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function UseCasesSection({ section }: { section: LandingSection }) {
  const items = section.items ?? []
  if (items.length === 0) {
    return null
  }

  return (
    <section className="landing-section border-b border-border bg-muted/20">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Use cases"}
          title={section.title ?? "Pick the proof that matches the project."}
          description={section.description}
        />
        <div className="grid gap-px overflow-hidden border border-border bg-border sm:grid-cols-2">
          {items.map((item) => (
            <div key={item.title} className="bg-card p-6">
              <h3 className="text-base font-semibold text-foreground">
                {item.title}
              </h3>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {item.description ?? item.detail}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CtaSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const actions = (section.actions?.length ? section.actions : context.actionLinks)
    .map(normalizeAction)

  return (
    <section className="landing-section border-t border-border bg-muted/20">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-16 sm:flex-row sm:items-end sm:justify-between">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Next"}
          title={section.title ?? "Open the generated docs."}
          description={section.description}
        />
        <nav className="flex flex-wrap gap-3">
          {actions.map((action) => (
            <a
              key={action.title}
              href={action.href}
              target={action.external ? "_blank" : undefined}
              rel={action.external ? "noopener noreferrer" : undefined}
              className={
                action.primary
                  ? "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground"
                  : "rounded-md border border-border bg-card px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
              }
            >
              {action.title}
            </a>
          ))}
        </nav>
      </div>
    </section>
  )
}

function LinkGridSection({ section }: { section: LandingSection }) {
  const links: LandingCatalogItem[] = section.links ?? section.items ?? []
  if (links.length === 0) {
    return null
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Links"}
          title={section.title ?? "Route readers to the right source."}
          description={section.description}
        />
        <div className="grid gap-px overflow-hidden border border-border bg-border sm:grid-cols-2">
          {links.map((link) => {
            const href = normalizeLandingHref(link.href ?? "#")
            const external = link.external ?? href.startsWith("http")
            return (
              <a
                key={`${link.title}-${href}`}
                href={href}
                target={external ? "_blank" : undefined}
                rel={external ? "noopener noreferrer" : undefined}
                className="bg-card p-6 transition-colors hover:bg-muted/50"
              >
                <h3 className="text-base font-semibold text-foreground">
                  {link.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {link.description ?? link.detail ?? link.href}
                </p>
              </a>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export const LANDING_SECTION_COMPONENTS: Record<
  LandingSectionType,
  LandingSectionComponent
> = {
  "features": FeaturesSection,
  "comparison": ComparisonSection,
  "output": OutputSection,
  "routes": RoutesSection,
  "pipeline": PipelineSection,
  "install": InstallSection,
  "stats": StatsSection,
  "use-cases": UseCasesSection,
  "cta": CtaSection,
  "link-grid": LinkGridSection,
}

export function LandingSectionRenderer({
  sections,
  context,
}: {
  sections: LandingSection[]
  context: LandingSectionContext
}) {
  return (
    <>
      {sections.map((section, index) => {
        if (section.enabled === false) {
          return null
        }
        const Component =
          LANDING_SECTION_COMPONENTS[section.type as LandingSectionType]
        if (!Component) {
          return null
        }
        return (
          <Component
            key={`${section.type}-${index}`}
            section={section}
            context={context}
          />
        )
      })}
    </>
  )
}
