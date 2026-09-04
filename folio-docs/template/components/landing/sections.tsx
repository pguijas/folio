import { Fragment, type ReactElement, type ReactNode } from "react"

import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import {
  AiFileIcon,
  ArrowDown01Icon,
  FileSlidersIcon,
  FingerPrintIcon,
  FolderOpenIcon,
  KanbanIcon,
  LanguageSquareIcon,
  PythonIcon,
  QuillWrite01Icon,
  SearchList01Icon,
} from "@hugeicons/core-free-icons"

import { BrowserFrame } from "@/components/browser-frame"
import { ComparisonMatrix } from "@/components/comparison-matrix"
import { LandingCommand, normalizeLandingHref } from "@/components/landing/actions"
import { defaultRoutes } from "@/components/landing/defaults"
import { HeartbeatLandingHero } from "@/components/landing/hero"
import type {
  LandingCatalogItem,
  LandingFeature,
  LandingFunnelGuarantee,
  LandingFunnelInput,
  LandingFunnelOutput,
  LandingHarnessItem,
  LandingLink,
  LandingPipelineStep,
  LandingSection,
  LandingSectionContext,
  LandingSectionType,
} from "@/components/landing/types"
import { Roadmap } from "@/components/roadmap"
import { folioProject } from "@/lib/folio-template"
import { roadmapPhases } from "@/lib/roadmap-data"
import { cn } from "@/lib/utils"

type LandingSectionComponent = (props: {
  section: LandingSection
  context: LandingSectionContext
}) => ReactElement | null

function SectionHeading({
  eyebrow,
  title,
  description,
  centered = false,
  className,
}: {
  eyebrow: string
  title: string
  description?: string
  /** Centers the heading block — for sections whose body is a centered
   * exhibit rather than a left-anchored column. */
  centered?: boolean
  className?: string
}) {
  return (
    <div className={cn(centered && "mx-auto max-w-2xl text-center", className)}>
      <p className="font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
        {eyebrow}
      </p>
      <h2 className="mt-4 text-3xl font-bold text-balance text-foreground sm:text-4xl">
        {title}
      </h2>
      {description ? (
        <p
          className={cn(
            "mt-5 max-w-md text-sm leading-6 text-muted-foreground",
            centered && "mx-auto"
          )}
        >
          {description}
        </p>
      ) : null}
    </div>
  )
}

/**
 * The landing plugin drops actions without an href, but this data can also be
 * hand-authored, and a missing href used to abort the whole prerender on
 * `action.href.startsWith`. Render what is usable instead.
 *
 * `pathToRoot` travels with it because a landing served below the site root
 * has to climb back out of every configured "/path" href; the two concerns
 * meet here because both are about turning authored data into a href that
 * will actually resolve.
 */
function usableActions(
  actions: LandingLink[] | undefined,
  pathToRoot?: string
): LandingLink[] {
  return (actions ?? [])
    .filter((action) => typeof action?.href === "string" && action.href !== "")
    .map((action) => ({
      ...action,
      href: normalizeLandingHref(action.href, pathToRoot),
      external: action.external ?? action.href.startsWith("http"),
    }))
}

/**
 * Vignette band at the top of a "features" bento card — a quiet, token-only
 * illustration of the claim, ported from the funnel prototype's evidence
 * grid: an MDX tabs+callout collage, an llms.txt file card, a build receipt
 * terminal, deploy target chips, plugin sockets, and theme swatches.
 * Purely decorative; screen readers get the card copy instead. An unknown
 * kind renders nothing and the card degrades to copy-only.
 */
function FeatureVisual({ kind }: { kind?: string }) {
  const band =
    "flex min-h-[10.5rem] items-center justify-center border-b border-border/60 bg-muted/30 p-5"

  if (kind === "components") {
    return (
      <div className={band} aria-hidden="true">
        <div className="grid w-full max-w-md gap-3 sm:grid-cols-[1.1fr_1fr] sm:items-center">
          <div className="overflow-hidden rounded-md border border-border bg-background shadow-sm">
            <div className="flex gap-1 border-b border-border/60 px-1.5 pt-1 font-mono text-[9px] leading-none text-muted-foreground">
              <span className="border-b-2 border-primary px-2 pt-1 pb-1.5 font-semibold text-primary">
                pip
              </span>
              <span className="px-2 pt-1 pb-1.5">uv</span>
              <span className="px-2 pt-1 pb-1.5">poetry</span>
            </div>
            <div className="px-2.5 py-2 font-mono text-[10px] leading-relaxed text-muted-foreground">
              <span className="text-primary">$</span>{" "}
              <span className="font-semibold text-foreground">
                pip install folio-docs
              </span>
              <br />
              &lt;Tabs&gt; renders this switcher
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <div className="rounded-md border border-primary/25 border-l-[3px] border-l-primary bg-primary/5 px-2.5 py-2 text-[10.5px] leading-snug text-muted-foreground">
              <span className="font-semibold text-foreground">Note</span>{" "}
              &mdash; callouts share the site&apos;s theme tokens.
            </div>
            <div className="flex max-w-[10.5rem] flex-wrap gap-1.5 font-mono text-[9px] leading-none text-muted-foreground">
              {["<Steps>", "<FileTree>", "<Mermaid>", "<KaTeX>"].map((tag) => (
                <span
                  key={tag}
                  className="rounded border border-border/70 bg-background px-1.5 py-1"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (kind === "llms") {
    return (
      <div className={band} aria-hidden="true">
        <div className="relative w-full max-w-[15.5rem] rounded-md border border-border bg-background px-3.5 py-3 font-mono text-[10px] leading-loose text-muted-foreground">
          {/* dog-ear: the folded file corner */}
          <span className="absolute -top-px -right-px size-[15px] rounded-bl-md border-b border-l border-border bg-muted/60" />
          <span className="mb-1 block text-[9px] font-semibold tracking-[0.14em] text-primary uppercase">
            llms.txt
          </span>
          # <span className="font-semibold text-foreground">folio</span>
          <br />
          &gt; API docs, straight from source
          <br />
          - <span className="text-primary">[folio.config]</span>(/config)
          <br />
          - <span className="text-primary">[folio.build]</span>(/build)
        </div>
      </div>
    )
  }

  if (kind === "receipt") {
    return (
      <div className={band} aria-hidden="true">
        <div className="w-full max-w-xs overflow-hidden rounded-md border border-border bg-background">
          <div className="flex items-center gap-2 border-b border-border/60 bg-muted/40 px-2.5 py-1.5 font-mono text-[9px] leading-none text-muted-foreground">
            <span className="flex shrink-0 gap-1">
              <span className="size-[7px] rounded-full bg-border" />
              <span className="size-[7px] rounded-full bg-border" />
              <span className="size-[7px] rounded-full bg-border" />
            </span>
            folio build
          </div>
          <div className="px-3 py-2 font-mono text-[10px] leading-loose text-muted-foreground">
            <span className="font-semibold text-primary">&#10003;</span>{" "}
            <span className="font-semibold text-foreground">Pages</span>{" "}
            &#8250; 96 built
            <br />
            <span className="font-semibold text-primary">&#10003;</span>{" "}
            <span className="font-semibold text-foreground">Search</span>{" "}
            &#8250; indexed at build time
            <br />
            <span className="font-semibold text-primary">&#10003;</span>{" "}
            <span className="font-semibold text-foreground">Links</span>{" "}
            &#8250; 0 broken
            <br />
            <span className="font-semibold text-primary">&#10003;</span>{" "}
            <span className="font-semibold text-foreground">Done</span>{" "}
            &#8250; _site/ ready in 0.6s
          </div>
        </div>
      </div>
    )
  }

  if (kind === "deploy") {
    return (
      <div className={band} aria-hidden="true">
        <div className="flex w-full max-w-sm flex-col gap-3.5">
          <div className="flex flex-wrap gap-2 font-mono text-[10.5px] leading-none">
            <span className="rounded-full border border-primary/40 bg-primary/10 px-3 py-2 font-semibold whitespace-nowrap text-primary">
              &#10003; GitHub Pages
            </span>
            {["Vercel", "Netlify", "Docker", "S3"].map((target) => (
              <span
                key={target}
                className="rounded-full border border-border bg-background px-3 py-2 whitespace-nowrap text-muted-foreground"
              >
                {target}
              </span>
            ))}
          </div>
          <p className="m-0 border-t border-border/60 pt-2 font-mono text-[9.5px] text-muted-foreground">
            <span className="font-semibold text-foreground">
              base path inferred
            </span>{" "}
            &mdash; same export, every target
          </p>
        </div>
      </div>
    )
  }

  if (kind === "plugins") {
    return (
      <div className={band} aria-hidden="true">
        <div className="flex w-full max-w-sm flex-col gap-2.5">
          <div className="grid grid-cols-4 gap-2">
            {["roadmap", "kanban", "landing"].map((socket) => (
              <span
                key={socket}
                className="relative grid place-items-center rounded-md border border-border bg-background px-1 py-3.5 text-center font-mono text-[9.5px] font-semibold text-foreground"
              >
                {/* the plugged-in notch */}
                <span className="absolute inset-x-[22%] top-0 h-[3px] rounded-b-[3px] bg-primary" />
                {socket}
              </span>
            ))}
            <span className="grid place-items-center rounded-md border border-dashed border-border px-1 py-3.5 text-center font-mono text-[9.5px] text-muted-foreground">
              + yours
            </span>
          </div>
          <p className="m-0 border-t border-border/60 pt-2 font-mono text-[9.5px] text-muted-foreground">
            built on{" "}
            <span className="font-semibold text-foreground">pluggy</span>{" "}
            &mdash; one registry &middot; explicit contracts
          </p>
        </div>
      </div>
    )
  }

  if (kind === "theming") {
    const swatches = [
      { tint: "bg-primary", label: "ink" },
      { tint: "bg-primary/70", label: "70" },
      { tint: "bg-primary/45", label: "45" },
      { tint: "bg-primary/15", label: "15" },
      { tint: "bg-background", label: "paper" },
    ]
    return (
      <div className={band} aria-hidden="true">
        <div className="flex w-full max-w-sm flex-col gap-2.5">
          <div className="grid grid-cols-5 gap-2">
            {swatches.map((swatch) => (
              <span
                key={swatch.label}
                className="overflow-hidden rounded-md border border-border bg-background dark:border-foreground/25"
              >
                <span className={cn("block h-8", swatch.tint)} />
                <span className="block px-1 py-1 text-center font-mono text-[8.5px] leading-none text-muted-foreground">
                  {swatch.label}
                </span>
              </span>
            ))}
          </div>
          <p className="m-0 border-t border-border/60 pt-2 font-mono text-[9.5px] text-muted-foreground">
            <span className="font-semibold text-foreground">
              one accent token
            </span>{" "}
            &mdash; presets &middot; variants &middot; overlays
          </p>
        </div>
      </div>
    )
  }

  return null
}

/**
 * "features" with `variant: "bento"`: a two-column card grid where every
 * card opens on a FeatureVisual vignette and closes on a numbered No. 0X
 * copy block — the prototype's evidence grid. `wide: true` spans both
 * columns. Sits on the muted band like the funnel it argues for.
 */
function FeaturesBentoSection({
  section,
  features,
  context,
}: {
  section: LandingSection
  features: LandingFeature[]
  context: LandingSectionContext
}) {
  // Mintlify-style display header: a two-beat slogan set huge — the strong
  // beat in foreground ink, the continuation muted — with the section's
  // first action as a quiet button on the right. `title_muted` carries the
  // second beat; without it the title renders alone at the same scale.
  const action = (section.actions ?? [])[0]
  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto max-w-site px-6 py-20">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="min-w-0 max-w-3xl">
            <p className="font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
              {section.eyebrow ?? "Capability stack"}
            </p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-balance sm:text-4xl xl:text-[2.75rem] xl:leading-[1.12]">
              <span className="text-foreground">
                {section.title ?? "Everything a docs site needs, from one build."}
              </span>
              {section.title_muted ? (
                <>
                  {" "}
                  <span className="text-muted-foreground">
                    {section.title_muted}
                  </span>
                </>
              ) : null}
            </h2>
            {section.description ? (
              <p className="mt-5 max-w-xl text-sm leading-6 text-muted-foreground">
                {section.description}
              </p>
            ) : null}
          </div>
          {action ? (
            <a
              href={normalizeLandingHref(action.href, context.pathToRoot)}
              className="group mb-1 inline-flex shrink-0 items-center gap-1.5 rounded-md border border-border bg-background px-3.5 py-2 font-sans text-xs font-semibold text-foreground transition-colors hover:border-foreground/40"
            >
              {action.title}
              <span
                aria-hidden="true"
                className="transition-transform group-hover:translate-x-0.5"
              >
                &rarr;
              </span>
            </a>
          ) : null}
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className={cn(
                "flex min-w-0 flex-col overflow-hidden rounded-lg border border-border bg-card transition-colors hover:border-primary/40",
                feature.wide && "sm:col-span-2"
              )}
            >
              <FeatureVisual kind={feature.visual} />
              <div className="flex-1 p-5">
                <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-primary uppercase">
                  No. {String(index + 1).padStart(2, "0")}
                </p>
                <h3 className="mt-2 mb-0 text-base font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="mt-2 mb-0 text-sm leading-6 text-muted-foreground">
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

function FeaturesSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const features = section.features ?? []
  if (features.length === 0) {
    return null
  }

  if (section.variant === "bento") {
    return (
      <FeaturesBentoSection
        section={section}
        features={features}
        context={context}
      />
    )
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Capability stack"}
          title={section.title ?? "Less configuration, more finished docs."}
          description={section.description}
          className="lg:sticky lg:top-24 lg:self-start"
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

/**
 * "comparison" section. A project supplies `tools` and `rows` and the table is
 * entirely its own; the heading defaults stay neutral and no Folio route is
 * linked. Only the deprecated bundled matrix — the fallback when either is
 * missing — carries Folio's own framing, because it is Folio's own table.
 */
function ComparisonSection({ section }: { section: LandingSection }) {
  const configured = Boolean(section.tools?.length && section.rows?.length)

  return (
    <section className="comparison-evidence comparison-evidence-surface landing-section border-b border-border bg-muted/20">
      <div className="mx-auto max-w-site px-6 py-20">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,0.58fr)_minmax(24rem,0.42fr)] lg:items-end">
          <div className="max-w-3xl">
            <SectionHeading
              eyebrow={section.eyebrow ?? "Comparison"}
              title={
                section.title ??
                (configured
                  ? "How it compares."
                  : "Source-first docs, without the portal tax.")
              }
              description={
                section.description ??
                (configured
                  ? undefined
                  : "Folio covers the daily documentation path: pdoc-level setup, guides, static export, LLM-friendly files, extensibility, open source, and CI-ready builds. Roadmap gaps stay on the roadmap.")
              }
            />
            {configured ? null : (
              <a
                href="./roadmap/"
                className="mt-4 inline-flex text-sm font-semibold text-foreground underline decoration-foreground/30 underline-offset-4"
              >
                Roadmap
              </a>
            )}
          </div>
        </div>

        <ComparisonMatrix
          className="mt-10"
          includeSurface={false}
          caption={section.caption}
          tools={section.tools}
          rows={section.rows}
        />
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
    <section className="landing-section mx-auto max-w-site px-6 py-20">
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

function RoutesSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const routes = section.routes?.length ? section.routes : defaultRoutes

  /* The grid draws its hairlines by letting its own background show through
     one-pixel gaps, so a last row that does not fill shows as a slab of
     border colour rather than as a missing card. The final card takes the
     columns the row has left over, which keeps any count square. */
  const remainder = routes.length % 3
  const lastSpan =
    remainder === 1 ? "sm:col-span-3" : remainder === 2 ? "sm:col-span-2" : ""

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Docs map"}
          title={section.title ?? "Generated routes stay predictable."}
          description={
            section.description ??
            "Guide pages, API reference, and static search output keep stable URLs."
          }
        />

        <div className="grid gap-px overflow-hidden border border-border bg-border sm:grid-cols-3">
          {routes.map((route, index) => (
            <a
              key={route.path}
              href={normalizeLandingHref(route.href, context.pathToRoot)}
              className={cn(
                "bg-card p-5 transition-colors hover:bg-muted/50",
                index === routes.length - 1 && lastSpan
              )}
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
    <section className="landing-section border-b border-border bg-muted/20 dark:bg-muted/45">
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Pipeline"}
          title={section.title ?? "Source turns into a deployable docs site."}
          description={section.description}
          className="lg:sticky lg:top-24 lg:self-start"
        />

        <ol className="border-y border-border">
          {steps.map((step) => (
            <li
              key={step.label}
              className="grid gap-4 border-b border-border py-5 last:border-b-0 sm:grid-cols-[4rem_1fr]"
            >
              <span className="font-mono text-xs text-muted-foreground">
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
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
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
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Proof"}
          title={section.title ?? "A few numbers you can check."}
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
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
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
  const configured = usableActions(section.actions, context.pathToRoot)
  const actions = configured.length
    ? configured
    : usableActions(context.actionLinks, context.pathToRoot)

  return (
    <section className="landing-section border-t border-border bg-muted/20">
      <div className="mx-auto flex max-w-site flex-col gap-8 px-6 py-16 sm:flex-row sm:items-end sm:justify-between">
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

function LinkGridSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const links: LandingCatalogItem[] = section.links ?? section.items ?? []
  if (links.length === 0) {
    return null
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto grid max-w-site gap-10 px-6 py-20 lg:grid-cols-[0.34fr_0.66fr]">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Links"}
          title={section.title ?? "Route readers to the right source."}
          description={section.description}
        />
        <div className="grid gap-px overflow-hidden border border-border bg-border sm:grid-cols-2">
          {links.map((link) => {
            const href = normalizeLandingHref(link.href ?? "#", context.pathToRoot)
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

/**
 * Compact vignette drawn above a "cells" item's copy — a quiet, token-only
 * illustration of the claim (no images): a callout+tabs collage for the
 * component library, an llms.txt file card, a build→site receipt, plugin
 * sockets. Purely decorative; screen readers get the cell copy instead.
 */
function CellVisual({ kind }: { kind?: string }) {
  if (!kind) {
    return null
  }

  const shell =
    "mb-4 flex h-20 flex-col justify-center gap-1.5 overflow-hidden rounded-md border border-border bg-background/60 p-3"

  if (kind === "components") {
    return (
      <div className={shell} aria-hidden="true">
        <div className="flex items-center gap-2 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1.5">
          <span className="size-2 shrink-0 rounded-full bg-primary" />
          <span className="h-1.5 w-2/3 rounded-full bg-primary/40" />
        </div>
        <div className="flex items-end gap-1 font-mono text-[9px] leading-none">
          <span className="rounded-t border border-b-0 border-border bg-card px-2 py-1 font-semibold text-primary">
            Tabs
          </span>
          <span className="px-2 py-1 text-muted-foreground">Steps</span>
          <span className="px-2 py-1 text-muted-foreground">Callout</span>
          <span className="min-w-0 flex-1 border-b border-border" />
        </div>
      </div>
    )
  }

  if (kind === "llms") {
    return (
      <div className={shell} aria-hidden="true">
        <div className="flex items-center justify-between font-mono text-[10px] leading-none">
          <span className="text-foreground">llms.txt</span>
          <span className="text-primary">&#10003;</span>
        </div>
        <span className="h-1.5 w-11/12 rounded-full bg-muted-foreground/30" />
        <span className="h-1.5 w-3/4 rounded-full bg-muted-foreground/30" />
        <div className="flex items-center justify-between font-mono text-[10px] leading-none">
          <span className="text-muted-foreground">llms-full.txt</span>
          <span className="text-primary">&#10003;</span>
        </div>
      </div>
    )
  }

  if (kind === "export") {
    return (
      <div className={shell} aria-hidden="true">
        <p className="m-0 font-mono text-[10px] leading-relaxed">
          <span className="text-muted-foreground">$ </span>
          <span className="font-semibold text-foreground">folio build</span>
        </p>
        <p className="m-0 font-mono text-[10px] leading-relaxed text-muted-foreground">
          <span className="font-semibold text-primary">&#10003;</span> 100
          pages &middot; search indexed
        </p>
        <p className="m-0 font-mono text-[10px] leading-relaxed text-muted-foreground">
          <span className="font-semibold text-primary">&#10003;</span>{" "}
          _site/ &rarr; anywhere static
        </p>
      </div>
    )
  }

  if (kind === "plugins") {
    return (
      <div className={shell} aria-hidden="true">
        <div className="grid grid-cols-3 gap-1.5 font-mono text-[9px] leading-none">
          <span className="flex items-center justify-center gap-1 rounded border border-border bg-card px-1.5 py-2.5 text-foreground">
            <span className="size-1.5 rounded-full bg-primary" />
            roadmap
          </span>
          <span className="flex items-center justify-center gap-1 rounded border border-border bg-card px-1.5 py-2.5 text-foreground">
            <span className="size-1.5 rounded-full bg-primary" />
            kanban
          </span>
          <span className="flex items-center justify-center rounded border border-dashed border-border px-1.5 py-2.5 text-muted-foreground">
            + yours
          </span>
        </div>
      </div>
    )
  }

  return null
}

/**
 * "cells" section: a bento-style row of small feature cells. Each cell is a
 * mono micro-label, a short claim, a one-line description, and an optional
 * footer link — the whole cell becomes the link when `href` is set.
 */
function CellsSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const items = (section.items ?? []).filter((item) => item.title)
  if (items.length === 0) {
    return null
  }

  const hasHeading = Boolean(section.eyebrow || section.title)

  return (
    <section className="landing-section border-b border-border bg-muted/20">
      <div className="mx-auto max-w-site px-6 py-20">
        {hasHeading ? (
          <SectionHeading
            eyebrow={section.eyebrow ?? "Capabilities"}
            title={section.title ?? "The rest of the toolchain."}
            description={section.description}
          />
        ) : null}

        <div
          className={cn(
            "grid gap-4 sm:grid-cols-2",
            items.length % 3 === 0 ? "lg:grid-cols-3" : "lg:grid-cols-4",
            hasHeading && "mt-10"
          )}
        >
          {items.map((item) => {
            const href = item.href
              ? normalizeLandingHref(item.href, context.pathToRoot)
              : null
            const external = item.external ?? (href?.startsWith("http") ?? false)
            const body = (
              <>
                <CellVisual kind={item.visual} />
                {item.label ? (
                  <p className="m-0 font-mono text-[10px] tracking-[0.16em] text-muted-foreground uppercase">
                    {item.label}
                  </p>
                ) : null}
                <h3 className="mt-3 mb-0 text-base font-semibold text-foreground">
                  {item.title}
                </h3>
                {item.description ? (
                  <p className="mt-2 mb-0 text-sm leading-6 text-muted-foreground">
                    {item.description}
                  </p>
                ) : null}
                {href ? (
                  <p className="mt-auto mb-0 pt-5 font-mono text-xs text-primary">
                    {item.link_text || "Open"}{" "}
                    <span aria-hidden="true">&rarr;</span>
                  </p>
                ) : null}
              </>
            )
            const cellClassName =
              "flex min-w-0 flex-col rounded-lg border border-border bg-card p-5"
            return href ? (
              <a
                key={item.title}
                href={href}
                target={external ? "_blank" : undefined}
                rel={external ? "noopener noreferrer" : undefined}
                className={cn(
                  cellClassName,
                  "transition-colors hover:border-primary/40 hover:bg-muted/40"
                )}
              >
                {body}
              </a>
            ) : (
              <div key={item.title} className={cellClassName}>
                {body}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

/**
 * "boards" section: a live roadmap miniature inside browser chrome.
 */
function BoardsSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const hasRoadmap = roadmapPhases.length > 0
  if (!hasRoadmap) {
    return null
  }

  const roadmapUrl = section.roadmap_url || "/roadmap"
  const roadmapLinkText = section.roadmap_link_text || "Full roadmap"
  const centeredExhibit = section.narrow === true

  return (
    <section className="landing-section border-b border-border bg-muted/20 dark:bg-muted/45">
      <div className="mx-auto max-w-site px-6 py-20">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Boards"}
          title={section.title ?? "The plan is part of the site."}
          description={section.description}
          centered={centeredExhibit}
        />

        <div
          className={cn(
            "mt-10 grid gap-6",
            centeredExhibit && "mx-auto w-full max-w-3xl"
          )}
        >
          {hasRoadmap ? (
            <div className="min-w-0">
              <BrowserFrame
                url={roadmapUrl}
                footer={
                  <>
                    {folioProject.repo ? (
                      <a
                        href={`${folioProject.repo}/blob/${folioProject.repoRef || "main"}/docs.yaml`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex w-full items-center gap-1.5 py-2 font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground sm:w-auto sm:py-0"
                        title="The YAML that renders this board"
                      >
                        source: docs.yaml
                        <span aria-hidden="true">&#8599;</span>
                      </a>
                    ) : null}
                    <a
                      href={normalizeLandingHref(roadmapUrl, context.pathToRoot)}
                      className="inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-border bg-background px-3 py-2 font-sans text-xs font-semibold text-foreground transition-colors hover:border-foreground/40 sm:ml-auto sm:w-auto sm:py-1.5"
                    >
                      {roadmapLinkText}
                      <span aria-hidden="true">&rarr;</span>
                    </a>
                  </>
                }
              >
                <Roadmap compact moreLink={false} />
              </BrowserFrame>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

/**
 * One line of the mechanism section's code window. The diff convention is
 * purely positional: a line starting with "+ " is tinted as an addition and
 * "- " as a removal. Indented YAML list items ("  - foo") never match.
 */
function MechanismCodeLine({ line }: { line: string }) {
  const added = line.startsWith("+ ")
  const removed = line.startsWith("- ")
  return (
    <div
      className={cn(
        "border-l-2 border-transparent px-4 whitespace-pre",
        added &&
          "border-emerald-500/70 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
        removed &&
          "border-red-500/60 bg-red-500/[0.08] text-red-700 opacity-80 dark:text-red-400"
      )}
    >
      {line || " "}
    </div>
  )
}

/**
 * "mechanism" section: a config diff followed by its build pipeline.
 */
function MechanismSection({ section }: { section: LandingSection }) {
  const code = typeof section.code === "string" ? section.code : ""
  if (!code) {
    return null
  }

  const codeTitle = section.code_title || "docs.yaml"
  const commits = (section.commits ?? []).filter(
    (commit) => commit && (commit.hash || commit.message)
  )
  const pills = section.pills?.length
    ? section.pills
    : ["git push", "folio build", "deploy"]
  const accentPill = Math.floor(pills.length / 2)
  const caption = section.caption

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto max-w-site px-6 py-20">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Mechanism"}
          title={section.title ?? "The diff is the UI."}
          description={section.description}
        />

        <div className="mt-10 grid gap-6">
          {code ? (
            <figure className="not-prose m-0 flex min-w-0 flex-col self-stretch overflow-hidden rounded-lg border border-border bg-card shadow-[0_20px_50px_-18px_rgba(0,0,0,0.4)]">
              <div className="flex items-center gap-3 border-b border-border bg-muted/40 px-3.5 py-2.5">
                <span aria-hidden="true" className="flex shrink-0 gap-1.5">
                  <span className="size-[9px] rounded-full bg-border" />
                  <span className="size-[9px] rounded-full bg-border" />
                  <span className="size-[9px] rounded-full bg-border" />
                </span>
                <p className="m-0 truncate font-mono text-[11px] text-muted-foreground">
                  {codeTitle}
                </p>
              </div>
              <div className="flex-1 overflow-x-auto py-3 font-mono text-xs leading-[1.85] text-muted-foreground">
                {code.split("\n").map((line, index) => (
                  <MechanismCodeLine key={index} line={line} />
                ))}
              </div>
              {commits.length > 0 ? (
                <div className="border-t border-border bg-muted/40 px-4 py-3">
                  <p className="m-0 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/70">
                    git log --oneline
                  </p>
                  {commits.map((commit, index) => (
                    <p
                      key={`${commit.hash}-${index}`}
                      className="m-0 mt-1.5 flex items-baseline gap-3 font-mono text-[11px]"
                    >
                      <span className="shrink-0 text-primary">
                        {commit.hash}
                      </span>
                      <span
                        className={cn(
                          "truncate",
                          index === 0
                            ? "text-foreground"
                            : "text-muted-foreground"
                        )}
                      >
                        {commit.message}
                      </span>
                    </p>
                  ))}
                </div>
              ) : null}
            </figure>
          ) : null}

          {pills.length > 0 ? (
            <div
              aria-hidden="true"
              className="flex flex-wrap items-center justify-center gap-2"
            >
              {pills.map((pill, index) => (
                <Fragment key={`${pill}-${index}`}>
                  {index > 0 ? <span className="h-px w-4 bg-border" /> : null}
                  <span
                    className={cn(
                      "whitespace-nowrap rounded-full border px-3 py-1.5 font-mono text-[11px]",
                      index === accentPill
                        ? "border-primary/40 bg-primary/10 text-primary"
                        : "border-border bg-card text-muted-foreground"
                    )}
                  >
                    {pill}
                  </span>
                </Fragment>
              ))}
            </div>
          ) : null}
        </div>

        {caption ? (
          <p className="mx-auto mt-9 mb-0 max-w-2xl text-center text-sm leading-6 text-muted-foreground">
            {caption}
          </p>
        ) : null}
      </div>
    </section>
  )
}

const DEFAULT_HARNESSES: LandingHarnessItem[] = [
  { label: "Codex", detail: "works in the checkout" },
  { label: "Claude Code", detail: "follows repository rules" },
  { label: "Other harnesses", detail: "read the same project state" },
]

const DEFAULT_UNIFIED_SURFACES: LandingHarnessItem[] = [
  { label: "Context", detail: "source + Markdown" },
  { label: "Rules", detail: "contracts in the repo" },
  { label: "Board", detail: "git-backed work state" },
  { label: "Artifacts", detail: "durable session output" },
]

/** One compact node inside the meta-harness diagram. */
function HarnessNode({ item }: { item: LandingHarnessItem }) {
  return (
    <div className="min-w-0 rounded-md border border-border bg-background px-3 py-2.5">
      <p className="m-0 truncate font-mono text-[11px] font-semibold text-foreground">
        {item.label}
      </p>
      {item.detail ? (
        <p className="mt-1 mb-0 text-[11px] leading-4 text-muted-foreground">
          {item.detail}
        </p>
      ) : null}
    </div>
  )
}

/**
 * "harness" section: the product split in one diagram. Folio Docs remains the
 * docs generator. Folio for Agents is the containing frame around the coding
 * harnesses a team already uses and the repository surfaces they share.
 * The visual claims interoperability through repository files, not control,
 * orchestration, or a remote write path.
 */
function HarnessSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const configuredHarnesses = (section.harnesses ?? []).filter(
    (item) => item.label
  )
  const configuredSurfaces = (section.unifies ?? []).filter(
    (item) => item.label
  )
  const harnesses =
    configuredHarnesses.length > 0 ? configuredHarnesses : DEFAULT_HARNESSES
  const unifiedSurfaces =
    configuredSurfaces.length > 0
      ? configuredSurfaces
      : DEFAULT_UNIFIED_SURFACES
  const docsLabel = section.docs_label || "Folio Docs"
  const agentsLabel = section.agents_label || "Folio for Agents"

  return (
    <section className="landing-section border-b border-border bg-background">
      <div className="mx-auto max-w-site px-6 py-20">
        <SectionHeading
          eyebrow={section.eyebrow ?? "Two products. Two release cycles."}
          title={
            section.title ??
            "Docs for people. Artifacts and work for agents."
          }
          description={section.description}
        />

        <div className="mt-10 flex flex-col gap-5">
          <article className="grid min-w-0 gap-8 rounded-lg border border-border bg-card p-6 lg:grid-cols-[minmax(0,0.48fr)_minmax(0,1fr)] lg:items-stretch">
            <div className="flex min-w-0 flex-col">
              <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-primary uppercase">
                Docs generator
              </p>
              <h3 className="mt-3 mb-0 text-xl font-semibold text-foreground">
                {docsLabel}
              </h3>
              <p className="mt-3 mb-0 text-sm leading-6 text-muted-foreground">
                {section.docs_detail ||
                  "Source and guides become the HTML and Markdown people and agents read."}
              </p>

              <div
                className="mt-auto grid gap-2 pt-8 font-mono text-[10px] sm:grid-cols-[1fr_auto_1fr] sm:items-center"
                aria-hidden="true"
              >
                <div className="rounded-md border border-border bg-background px-3 py-2.5 text-foreground">
                  source + guides
                </div>
                <span className="text-center text-primary">&rarr;</span>
                <div className="rounded-md border border-primary/35 bg-primary/5 px-3 py-2.5 text-foreground">
                  HTML + Markdown
                </div>
              </div>
            </div>

            <HeartbeatLandingHero
              embedded
              tagline=""
              headline=""
              description=""
              actionLinks={[]}
              actionGridClassName=""
              installCommands={context.installCommands}
              buildSteps={context.buildSteps}
              projectName={docsLabel}
              projectMonogram={docsLabel.slice(0, 2).toLowerCase()}
              projectVersion={folioProject.version}
            />
          </article>

          <figure className="relative m-0 min-w-0 rounded-lg border border-primary/35 bg-primary/[0.03] p-6">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-primary/20 pb-5">
              <div>
                <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-primary uppercase">
                  Meta-harness
                </p>
                <h3 className="mt-2 mb-0 text-xl font-semibold text-foreground">
                  {agentsLabel}
                </h3>
              </div>
              <p className="m-0 rounded-full border border-primary/30 bg-background px-3 py-1.5 font-mono text-[10px] font-semibold text-primary">
                {section.thesis || "Independent product. Repository-native context."}
              </p>
            </div>

            <div className="flex flex-col gap-4 pt-5">
              <div>
                <p className="m-0 font-mono text-[10px] tracking-[0.12em] text-muted-foreground uppercase">
                  Harnesses already in use
                </p>
                <div className="mt-2 grid gap-2 sm:grid-cols-3">
                  {harnesses.map((item, index) => (
                    <HarnessNode key={`${item.label}-${index}`} item={item} />
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3" aria-hidden="true">
                <span className="h-px flex-1 bg-primary/20" />
                <span className="rounded-full border border-primary/30 bg-background px-3 py-1 font-mono text-[9px] tracking-[0.12em] text-primary uppercase">
                  one project contract
                </span>
                <span className="h-px flex-1 bg-primary/20" />
              </div>

              <div>
                <p className="m-0 font-mono text-[10px] tracking-[0.12em] text-muted-foreground uppercase">
                  Shared through the repository
                </p>
                <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                  {unifiedSurfaces.map((item, index) => (
                    <HarnessNode key={`${item.label}-${index}`} item={item} />
                  ))}
                </div>
              </div>
            </div>

            <figcaption className="mt-5 border-t border-primary/20 pt-4 text-sm leading-6 text-muted-foreground">
              {section.agents_detail ||
                "Portable files give each coding harness the same context, rules, board, and artifacts."}
            </figcaption>
          </figure>
        </div>
      </div>
    </section>
  )
}

/* Funnel node marks. Config supplies a semantic key; an unknown key
 * renders no mark, so a typo degrades instead of throwing. */
const FUNNEL_ICONS: Record<string, IconSvgElement> = {
  config: FileSlidersIcon,
  python: PythonIcon,
  markdown: QuillWrite01Icon,
  language: LanguageSquareIcon,
  folder: FolderOpenIcon,
  search: SearchList01Icon,
  agents: AiFileIcon,
  hash: FingerPrintIcon,
  board: KanbanIcon,
}

/**
 * A node mark on a funnel card. Color is inherited from the label row,
 * so a ghost card's mark dims with it. HugeiconsIcon does not set
 * aria-hidden itself and the label text is the accessible name.
 */
function FunnelMark({ icon }: { icon?: string }) {
  const glyph = icon ? FUNNEL_ICONS[icon] : undefined
  if (!glyph) return null
  return (
    <HugeiconsIcon
      icon={glyph}
      size={14}
      strokeWidth={1.8}
      className="shrink-0"
      aria-hidden="true"
    />
  )
}

/* "funnel" plate defaults — folio's own build funnel, mirroring the
 * approved prototype. The template owns these: when the config omits
 * inputs/outputs/guarantees the plate still tells folio's story. */
const DEFAULT_FUNNEL_INPUTS: LandingFunnelInput[] = [
  { label: "docs.yaml", icon: "config" },
  { label: "folio/**/*.py", icon: "python" },
  { label: "guides/*.md", icon: "markdown" },
  { label: "*.ts", icon: "language", ghost: true, chip: "roadmap" },
]

const DEFAULT_FUNNEL_OUTPUTS: LandingFunnelOutput[] = [
  { label: "_site/", icon: "folder" },
  { label: "Pagefind index", icon: "search" },
  { label: "llms.txt + llms-full.txt", icon: "agents" },
  { label: "SHA-256 manifest", icon: "hash" },
]

const DEFAULT_FUNNEL_NOTES = ["reads source · never runs it"]

const DEFAULT_FUNNEL_CAPTION =
  "Docstrings change → folio build → every page regenerates."

const DEFAULT_FUNNEL_GUARANTEES: LandingFunnelGuarantee[] = [
  {
    title: "Read, never run.",
    detail: "Google- and NumPy-style docstrings, type annotations, decorators.",
  },
  {
    title: "One structure.",
    detail: "Signatures are read from the current source on every build.",
  },
  {
    title: "Full pages, not stubs.",
    detail: "Signatures, parameter tables, and docstring prose.",
  },
  {
    title: "No server.",
    detail: "Plain files, no vendor in the serving path.",
  },
]

/**
 * A source card on the left of the funnel plate. Ghost inputs (roadmap
 * items) dim and go dashed; a `chip` rides the label as a small pill.
 */
function FunnelInputCard({ input }: { input: LandingFunnelInput }) {
  return (
    <div
      className={cn(
        "relative w-full rounded-md border bg-background px-4 py-3",
        input.ghost
          ? "border-dashed border-muted-foreground/50 opacity-70"
          : "border-border"
      )}
    >
      {/* the curve's departure dot, riding the card edge */}
      <span
        className={cn(
          "absolute top-1/2 -right-1 hidden size-1.5 -translate-y-1/2 rounded-full lg:block",
          input.ghost ? "bg-muted-foreground/50" : "bg-primary"
        )}
        aria-hidden="true"
      />
      <p
        className={cn(
          "m-0 flex items-center gap-2 font-mono text-xs font-semibold",
          input.ghost ? "text-muted-foreground" : "text-foreground"
        )}
      >
        <FunnelMark icon={input.icon} />
        <span className="truncate">{input.label}</span>
        {input.chip ? (
          <span className="shrink-0 rounded-full border border-dashed border-primary/40 bg-primary/5 px-2 py-px font-mono text-[9px] font-semibold whitespace-nowrap text-primary">
            {input.chip}
          </span>
        ) : null}
      </p>
      {input.detail ? (
        <p className="mt-1 mb-0 font-mono text-[10.5px] text-muted-foreground">
          {input.detail}
        </p>
      ) : null}
    </div>
  )
}

/**
 * "funnel" section: the build-funnel plate from the prototype — source
 * cards converge through the `folio build` node and fan out to the output
 * surfaces, drawn like a print figure ("Plate I", FIG. caption, a mono
 * guarantees strip). Each input/output may carry a whitelisted `icon`
 * node mark; an unknown key renders no mark. One responsive DOM: a
 * five-column grid at lg whose connector columns are stretched SVGs
 * (input/output rows are equal-height grid rows, so curve endpoints at
 * (i + 0.5) / n land exactly on each card's center), stacking to a single
 * column below lg where the connectors degrade to a hairline rule.
 */
function FunnelSection({ section }: { section: LandingSection }) {
  const configInputs = (section.inputs ?? []).filter((input) => input.label)
  const configOutputs = (section.outputs ?? []).filter((output) => output.label)
  const inputs = configInputs.length > 0 ? configInputs : DEFAULT_FUNNEL_INPUTS
  const outputs =
    configOutputs.length > 0 ? configOutputs : DEFAULT_FUNNEL_OUTPUTS
  const configGuarantees = (section.guarantees ?? []).filter(
    (guarantee) => guarantee.title
  )
  const guarantees =
    configGuarantees.length > 0 ? configGuarantees : DEFAULT_FUNNEL_GUARANTEES
  const command = section.command || "folio build"
  // `??`, not a length check: an explicit empty list means the node carries
  // no gloss, and only a missing key falls back to the bundled default.
  const notes = section.command_notes ?? DEFAULT_FUNNEL_NOTES
  // The default caption narrates the default plate; a custom plate without
  // a configured caption simply drops the FIG. line.
  const usingDefaultPlate =
    configInputs.length === 0 && configOutputs.length === 0
  const hasCaption = Boolean(section.caption) || usingDefaultPlate

  const connectorStroke = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.4,
    vectorEffect: "non-scaling-stroke",
  } as const

  return (
    <section className="landing-section border-b border-border bg-muted/20 dark:bg-muted/45">
      <div className="mx-auto max-w-site px-6 py-20">
        <SectionHeading
          eyebrow={section.eyebrow ?? "The mechanism"}
          title={section.title ?? "One build. Every output generated from it."}
          description={section.description}
        />

        <figure className="relative m-0 mt-10 rounded-lg border border-border bg-card p-5 pt-10 sm:p-7 sm:pt-10 lg:pt-7">
          <span
            className="absolute top-3 right-4 font-mono text-[10px] tracking-[0.14em] text-muted-foreground uppercase"
            aria-hidden="true"
          >
            Plate I
          </span>

          {/* cards flanking the build node, joined by drawn curves */}
          <div className="grid grid-cols-1 gap-y-2 lg:grid-cols-[minmax(0,16rem)_minmax(2.5rem,1fr)_minmax(0,16rem)_minmax(2.5rem,1fr)_minmax(0,16rem)] lg:items-stretch lg:gap-y-0">
            {/* group labels only below lg: the drawn funnel names its own
                flanks, a single stacked column does not. Hidden at lg so they
                never take a cell in the five-column grid. */}
            <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-muted-foreground uppercase lg:hidden">
              Source in
            </p>

            <div className="grid auto-rows-fr">
              {inputs.map((input) => (
                <div key={input.label} className="flex items-center py-1.5">
                  <FunnelInputCard input={input} />
                </div>
              ))}
            </div>

            <div
              className="relative flex min-w-0 justify-center py-1 lg:block lg:py-0"
              aria-hidden="true"
            >
              {/* below lg the drawn curves are gone, so the flow direction
                  rides a chevron instead — a mark, not a sentence */}
              <span className="flex flex-col items-center lg:hidden">
                <span className="block h-2 w-px bg-primary/40" />
                <HugeiconsIcon
                  icon={ArrowDown01Icon}
                  size={12}
                  strokeWidth={2}
                  className="text-primary/70"
                />
                <span className="block h-2 w-px bg-primary/40" />
              </span>
              <svg
                className="absolute inset-0 hidden h-full w-full lg:block"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
              >
                {/* faint funnel silhouette */}
                <path
                  d="M 0 6 L 100 34"
                  className="text-border"
                  {...connectorStroke}
                  strokeWidth={1}
                />
                <path
                  d="M 0 94 L 100 66"
                  className="text-border"
                  {...connectorStroke}
                  strokeWidth={1}
                />
                {/* converging hairlines: inputs → throat */}
                {inputs.map((input, index) => {
                  const y = ((index + 0.5) / inputs.length) * 100
                  return (
                    <path
                      key={`${input.label}-${index}`}
                      d={`M 0 ${y} C 45 ${y}, 55 50, 100 50`}
                      className={
                        input.ghost
                          ? "text-muted-foreground opacity-50"
                          : "text-primary"
                      }
                      strokeDasharray={input.ghost ? "4 6" : undefined}
                      {...connectorStroke}
                      strokeWidth={input.ghost ? 1.1 : 1.4}
                    />
                  )
                })}
              </svg>
            </div>

            {/* the throat: one build, one continuous flow */}
            <div className="flex flex-col justify-center">
              <p className="m-0 text-center font-mono text-xs font-semibold text-primary">
                $ {command}
              </p>
              <div className="mt-2 rounded-md border border-primary bg-background px-4 py-4 text-center">
                {notes[0] ? (
                  <p className="m-0 font-mono text-[11px] leading-relaxed font-semibold text-foreground">
                    {notes[0]}
                  </p>
                ) : null}
                <svg
                  viewBox="0 0 100 2"
                  preserveAspectRatio="none"
                  className={cn(
                    "h-0.5 w-full text-primary",
                    notes[0] && "mt-2.5"
                  )}
                  aria-hidden="true"
                >
                  <line
                    className="landing-funnel-flow"
                    x1="0"
                    y1="1"
                    x2="100"
                    y2="1"
                    {...connectorStroke}
                  />
                </svg>
                {notes.slice(1).map((note) => (
                  <p
                    key={note}
                    className="mt-2.5 mb-0 font-mono text-[10px] leading-relaxed text-muted-foreground"
                  >
                    {note}
                  </p>
                ))}
              </div>
              {/* invisible mirror of the command label so the node card
                  centers on the SVG columns' 50% line */}
              <p
                className="invisible m-0 mt-2 hidden text-center font-mono text-xs font-semibold lg:block"
                aria-hidden="true"
              >
                $ {command}
              </p>
            </div>

            <div
              className="relative flex min-w-0 justify-center py-1 lg:block lg:py-0"
              aria-hidden="true"
            >
              {/* below lg the drawn curves are gone, so the flow direction
                  rides a chevron instead — a mark, not a sentence */}
              <span className="flex flex-col items-center lg:hidden">
                <span className="block h-2 w-px bg-primary/40" />
                <HugeiconsIcon
                  icon={ArrowDown01Icon}
                  size={12}
                  strokeWidth={2}
                  className="text-primary/70"
                />
                <span className="block h-2 w-px bg-primary/40" />
              </span>
              <svg
                className="absolute inset-0 hidden h-full w-full lg:block"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
              >
                {/* faint funnel silhouette */}
                <path
                  d="M 0 34 L 100 6"
                  className="text-border"
                  {...connectorStroke}
                  strokeWidth={1}
                />
                <path
                  d="M 0 66 L 100 94"
                  className="text-border"
                  {...connectorStroke}
                  strokeWidth={1}
                />
                {/* diverging hairlines: throat → surfaces */}
                {outputs.map((output, index) => {
                  const y = ((index + 0.5) / outputs.length) * 100
                  return (
                    <path
                      key={`${output.label}-${index}`}
                      d={`M 0 50 C 45 50, 55 ${y}, 100 ${y}`}
                      className="text-primary"
                      {...connectorStroke}
                    />
                  )
                })}
              </svg>
            </div>

            <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-muted-foreground uppercase lg:hidden">
              Output
            </p>

            <div className="grid auto-rows-fr">
              {outputs.map((output) => (
                <div key={output.label} className="flex items-center py-1.5">
                  <div className="relative w-full rounded-md border border-border bg-background px-4 py-3">
                    {/* the curve's terminal dot, riding the card edge */}
                    <span
                      className="absolute top-1/2 -left-1 hidden size-1.5 -translate-y-1/2 rounded-full bg-primary lg:block"
                      aria-hidden="true"
                    />
                    <p className="m-0 flex items-center gap-2 font-mono text-xs font-semibold text-foreground">
                      <FunnelMark icon={output.icon} />
                      <span className="truncate">{output.label}</span>
                    </p>
                    {output.detail ? (
                      <p className="mt-1 mb-0 font-mono text-[10.5px] text-muted-foreground">
                        {output.detail}
                      </p>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {guarantees.length > 0 ? (
            <div className="mt-8">
              <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-primary uppercase">
                Guarantees
              </p>
              <ul
                className={cn(
                  "m-0 mt-3 grid list-none gap-x-6 gap-y-4 p-0 sm:grid-cols-2",
                  guarantees.length % 3 === 0
                    ? "lg:grid-cols-3"
                    : "lg:grid-cols-4"
                )}
              >
                {guarantees.map((guarantee) => (
                  <li
                    key={guarantee.title}
                    className="border-t border-border pt-2.5"
                  >
                    <p className="m-0 font-mono text-[11px] font-semibold text-foreground">
                      {guarantee.title}
                    </p>
                    {guarantee.detail ? (
                      <p className="mt-1 mb-0 font-mono text-[10px] leading-relaxed text-muted-foreground">
                        {guarantee.detail}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {hasCaption ? (
            <figcaption className="mt-6 border-t border-border/60 pt-4 font-mono text-[11px] leading-relaxed text-muted-foreground">
              <span className="font-semibold tracking-[0.14em] text-primary">
                FIG. 1
              </span>{" "}
              &mdash; {section.caption || DEFAULT_FUNNEL_CAPTION}
            </figcaption>
          ) : null}
        </figure>
      </div>
    </section>
  )
}

/**
 * "statement" section: a huge typographic closer with an optional
 * accent-highlighted substring and dual CTA links. `size: "md"` steps the
 * headline and padding down for a mid-page thesis block, and `description`
 * adds a reading-size lead paragraph under the headline.
 */
function StatementSection({
  section,
  context,
}: {
  section: LandingSection
  context: LandingSectionContext
}) {
  const text = typeof section.text === "string" ? section.text : ""
  if (!text) {
    return null
  }

  const accent = typeof section.accent === "string" ? section.accent : ""
  const actions = usableActions(section.actions, context.pathToRoot)
  const md = section.size === "md"

  let content: ReactNode = text
  if (accent) {
    const index = text.indexOf(accent)
    if (index !== -1) {
      content = (
        <>
          {text.slice(0, index)}
          {/* nowrap keeps the accent phrase on one line — a break inside it
              splits the color mid-phrase and reads as two ideas. */}
          <span className="text-primary whitespace-nowrap">{accent}</span>
          {text.slice(index + accent.length)}
        </>
      )
    }
  }

  return (
    <section className="landing-section border-b border-border bg-background">
      <div
        className={cn(
          "mx-auto max-w-site px-6 text-center",
          md ? "py-20 sm:py-24" : "py-24 sm:py-32"
        )}
      >
        {section.eyebrow ? (
          <p className="font-mono text-[11px] tracking-[0.14em] text-primary uppercase">
            {section.eyebrow}
          </p>
        ) : null}
        <h2
          className={cn(
            "mx-auto mt-6 mb-0 max-w-4xl font-bold tracking-tight text-balance text-foreground",
            md
              ? "text-3xl sm:text-4xl lg:text-5xl"
              : "text-4xl sm:text-5xl lg:text-6xl"
          )}
        >
          {content}
        </h2>
        {section.description ? (
          <p className="mx-auto mt-6 mb-0 max-w-2xl text-lg leading-8 text-pretty text-muted-foreground">
            {section.description}
          </p>
        ) : null}
        {actions.length > 0 ? (
          <nav className="mt-10 flex flex-wrap items-center justify-center gap-3">
            {actions.map((action, index) => (
              <a
                key={action.title}
                href={action.href}
                target={action.external ? "_blank" : undefined}
                rel={action.external ? "noopener noreferrer" : undefined}
                className={
                  (action.primary ?? index === 0)
                    ? "rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground"
                    : "rounded-md border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
                }
              >
                {action.title}
              </a>
            ))}
          </nav>
        ) : null}
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
  "cells": CellsSection,
  "boards": BoardsSection,
  "mechanism": MechanismSection,
  "harness": HarnessSection,
  "statement": StatementSection,
  "funnel": FunnelSection,
}

function sectionStageLabel(section: LandingSection): string {
  return typeof section.stage === "string" ? section.stage.trim() : ""
}

/**
 * Numbered stage rule above a staged section — a plate-style index: the
 * number in mono primary, the label in quiet sans, hairline underneath.
 * Rendered by LandingSectionRenderer as an overlay riding the section's own
 * top padding, so it sits on whatever band the section draws and enters on
 * the same landing-section animation.
 */
function StageRail({
  label,
  index,
}: {
  label: string
  index: number
  total: number
}) {
  const position = String(index).padStart(2, "0")
  return (
    <div className="flex items-baseline gap-3 border-b border-border/60 pb-3">
      <span className="font-mono text-[11px] font-semibold tabular-nums text-primary">
        {position}
      </span>
      <span className="text-[13px] font-medium tracking-tight text-muted-foreground">
        {label}
      </span>
    </div>
  )
}

export function LandingSectionRenderer({
  sections,
  context,
  heroStage,
}: {
  sections: LandingSection[]
  context: LandingSectionContext
  /** `landing.hero.stage`: when set, the hero opens the numbered stage
   * sequence — sections shift to 02… and the hero counts toward the 0N
   * total. (The hero renders its own rail.) */
  heroStage?: string | null
}) {
  const visibleSections = sections.filter(
    (section) =>
      section.enabled !== false &&
      Boolean(LANDING_SECTION_COMPONENTS[section.type as LandingSectionType])
  )
  const heroStaged =
    typeof heroStage === "string" && heroStage.trim() !== ""
  // Stage numbers are assigned in document order — the hero takes 01 when
  // staged, then every staged section in turn; 0 marks "no rail".
  let stageCursor = heroStaged ? 1 : 0
  const stageNumbers: number[] = []
  for (const section of visibleSections) {
    if (sectionStageLabel(section) !== "") {
      stageCursor += 1
      stageNumbers.push(stageCursor)
    } else {
      stageNumbers.push(0)
    }
  }
  const stageTotal = stageCursor

  return (
    <>
      {visibleSections.map((section, index) => {
        const Component =
          LANDING_SECTION_COMPONENTS[section.type as LandingSectionType]
        const stageLabel = sectionStageLabel(section)
        const body = <Component section={section} context={context} />
        if (!stageLabel) {
          return (
            <Fragment key={`${section.type}-${index}`}>{body}</Fragment>
          )
        }
        return (
          <div key={`${section.type}-${index}`} className="relative">
            {/* z-10: animated sections form stacking contexts that would
                otherwise paint over this rail on opaque backgrounds. */}
            <div className="landing-section pointer-events-none absolute inset-x-0 top-0 z-10">
              <div className="mx-auto max-w-site px-6 pt-7">
                <StageRail
                  label={stageLabel}
                  index={stageNumbers[index]}
                  total={stageTotal}
                />
              </div>
            </div>
            {body}
          </div>
        )
      })}
    </>
  )
}
