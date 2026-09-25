import { Fragment, type ReactElement, type ReactNode } from "react"

import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import {
  AiFileIcon,
  ApiIcon,
  ArrowDown01Icon,
  BookOpen01Icon,
  FileSlidersIcon,
  Files01Icon,
  FingerPrintIcon,
  FolderOpenIcon,
  JavaScriptIcon,
  LanguageSquareIcon,
  PythonIcon,
  QuillWrite01Icon,
  SearchList01Icon,
} from "@hugeicons/core-free-icons"

import { ComparisonMatrix } from "@/components/comparison-matrix"
import { LandingCommand, normalizeLandingHref } from "@/components/landing/actions"
import { defaultRoutes } from "@/components/landing/defaults"
import type {
  LandingCatalogItem,
  LandingFeature,
  LandingFunnelInput,
  LandingFunnelOutput,
  LandingLink,
  LandingPipelineStep,
  LandingSection,
  LandingSectionContext,
  LandingSectionType,
} from "@/components/landing/types"
import { cn } from "@/lib/utils"

type LandingSectionComponent = (props: {
  section: LandingSection
  context: LandingSectionContext
}) => ReactElement | null

/** Exported so a theme page can put a configured section's heading above a
 * body it renders itself. The Folio site does that for the roadmap card, which
 * is a component rather than a `landing.sections` entry. */
export function SectionHeading({
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
                pip install my-lib
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
            &#8250; built
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
            &#8250; _site/ ready
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
          <div className="grid grid-cols-3 gap-2">
            {["roadmap", "openapi", "landing"].map((socket) => (
              <span
                key={socket}
                className="relative grid place-items-center rounded-md border border-border bg-background px-1 py-3.5 text-center font-mono text-[9.5px] font-semibold text-foreground"
              >
                {/* the plugged-in notch */}
                <span className="absolute inset-x-[22%] top-0 h-[3px] rounded-b-[3px] bg-primary" />
                {socket}
              </span>
            ))}
          </div>
          <p className="m-0 border-t border-border/60 pt-2 font-mono text-[9.5px] text-muted-foreground">
            built in &middot; one registry
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
  // beat in foreground ink, the continuation in the accent — with the
  // section's first action as a quiet button on the right. `title_muted`
  // carries the second beat; without it the title renders alone at the same
  // scale.
  //
  // The second beat is `--primary`, not `--muted-foreground`. Grey is the tone
  // this theme uses for things that matter less, and the continuation of a
  // display slogan is the half doing the work, not an aside. The config key
  // keeps its name because renaming it would break every docs.yaml that sets
  // it; read `title_muted` as "the quieter beat", which it still is by weight.
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
                  <span className="text-primary">{section.title_muted}</span>
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
/* A photograph in a cell, treated so it belongs on this page.
 *
 * Everything else here is hairlines, one accent and near-monochrome value, so
 * a photograph dropped in raw becomes the only saturated thing on the screen
 * and pulls every eye to whichever cell happens to have one. The treatment is
 * a duotone: the image is desaturated, then a solid `--primary` layer in
 * `mix-blend-mode: color` puts the brand hue back. Luminosity comes from the
 * photograph, hue and saturation from the token, so it tracks light and dark
 * without a second asset and without a hex anywhere.
 *
 * `isolate` on the frame matters: `mix-blend-mode` blends against everything
 * below it in the stacking context, so without it the colour layer reaches
 * past the frame and tints the card and the section behind it.
 *
 * A plain `img`, not `next/image`: this template ships as a static export, so
 * the optimiser would need `unoptimized` anyway, and the band is a fixed 80px
 * strip rather than a layout-shifting hero. */
function CellImage({ src, alt }: { src: string; alt?: string }) {
  return (
    <div className="relative isolate mb-4 h-20 overflow-hidden rounded-md border border-border bg-muted">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt ?? ""}
        loading="lazy"
        decoding="async"
        className="size-full object-cover grayscale"
      />
      <span
        aria-hidden="true"
        className="absolute inset-0 bg-primary mix-blend-color"
      />
      {/* Sits the band back into the card. A duotone at full luminosity still
          reads brighter than the hairline drawings beside it, and in dark mode
          a light photograph glares. */}
      <span
        aria-hidden="true"
        className="absolute inset-0 bg-background/20 dark:bg-background/45"
      />
    </div>
  )
}

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
          <span className="font-semibold text-primary">&#10003;</span> pages
          built &middot; search indexed
        </p>
        <p className="m-0 font-mono text-[10px] leading-relaxed text-muted-foreground">
          <span className="font-semibold text-primary">&#10003;</span>{" "}
          _site/ &rarr; anywhere static
        </p>
      </div>
    )
  }

  /* The "Who picks Folio" cells. Same vocabulary as the four above:
     hairline panes, rounded bars standing in for text, one accent marking the
     thing that moved. Drawn rather than photographed because everything else
     on these pages is drawn, and a photograph next to line art is a different
     medium no filter reconciles. */

  if (kind === "maintainers") {
    return (
      <div className={`${shell} flex-row items-center gap-2.5`} aria-hidden="true">
        <span className="flex h-full min-w-0 flex-1 flex-col justify-center gap-1 rounded border border-border bg-card px-2">
          <span className="h-1 w-1/2 rounded-full bg-muted-foreground/45" />
          <span className="h-1 w-full rounded-full bg-muted-foreground/25" />
          <span className="h-1 w-4/5 rounded-full bg-muted-foreground/25" />
        </span>
        <span className="h-px w-4 shrink-0 bg-primary" />
        <span className="flex h-full min-w-0 flex-1 flex-col justify-center gap-1 rounded border border-primary/40 bg-primary/[0.06] px-2">
          <span className="h-1.5 w-2/3 rounded-full bg-primary/70" />
          <span className="h-1 w-full rounded-full bg-primary/25" />
          <span className="h-1 w-full rounded-full bg-primary/25" />
          <span className="h-1 w-3/5 rounded-full bg-primary/25" />
        </span>
      </div>
    )
  }

  if (kind === "agents") {
    return (
      <div className={`${shell} flex-row items-center gap-2.5`} aria-hidden="true">
        <span className="relative flex h-full w-[38%] shrink-0 flex-col justify-center gap-[3px] rounded border border-border bg-card px-2">
          <span className="h-1 w-3/4 rounded-full bg-muted-foreground/25" />
          <span className="h-1 w-full rounded-full bg-muted-foreground/25" />
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-px shrink-0 bg-primary" />
            <span className="h-1 w-2/3 rounded-full bg-muted-foreground/25" />
          </span>
          <span className="h-1 w-4/5 rounded-full bg-muted-foreground/25" />
        </span>
        <span className="grid min-w-0 flex-1 grid-cols-3 gap-1.5">
          {[0, 1, 2].map((page) => (
            <span
              key={page}
              className="flex flex-col gap-[3px] rounded border border-primary/35 bg-primary/[0.06] px-1.5 py-2"
            >
              <span className="h-1 w-2/3 rounded-full bg-primary/60" />
              <span className="h-[3px] w-full rounded-full bg-primary/25" />
              <span className="h-[3px] w-4/5 rounded-full bg-primary/25" />
            </span>
          ))}
        </span>
      </div>
    )
  }

  if (kind === "migrating") {
    return (
      <div className={`${shell} flex-row items-center gap-2.5`} aria-hidden="true">
        <span className="flex h-full min-w-0 flex-1 flex-col justify-center gap-[3px] pl-1">
          {[0, 1, 2].map((row) => (
            <span key={row} className="flex items-center gap-1.5">
              <span
                className={
                  row === 1
                    ? "ml-2 h-1.5 w-1.5 shrink-0 rounded-[2px] border border-primary/60"
                    : "h-1.5 w-1.5 shrink-0 rounded-[2px] border border-muted-foreground/40"
                }
              />
              <span
                className={
                  row === 1
                    ? "h-1 w-1/2 rounded-full bg-primary/50"
                    : "h-1 w-2/3 rounded-full bg-muted-foreground/30"
                }
              />
            </span>
          ))}
        </span>
        <span className="flex h-full min-w-0 flex-1 flex-col justify-center gap-1 rounded border border-border bg-card px-2">
          <span className="h-1.5 w-1/2 rounded-full bg-primary/50" />
          <span className="h-1 w-full rounded-full bg-muted-foreground/25" />
          <span className="h-1 w-full rounded-full bg-muted-foreground/25" />
          <span className="h-1 w-2/3 rounded-full bg-muted-foreground/25" />
        </span>
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
            openapi
          </span>
          <span className="flex items-center justify-center gap-1 rounded border border-border bg-card px-1.5 py-2.5 text-foreground">
            <span className="size-1.5 rounded-full bg-primary" />
            landing
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
                {/* One band per cell. A photograph replaces the drawn vignette
                    rather than stacking with it. */}
                {item.image ? (
                  <CellImage src={item.image} alt={item.image_alt} />
                ) : (
                  <CellVisual kind={item.visual} />
                )}
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
        added && "border-primary bg-primary/10 text-primary",
        removed && "border-border bg-muted/40 text-muted-foreground opacity-80"
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
            <figure className="not-prose m-0 flex min-w-0 flex-col self-stretch overflow-hidden rounded-lg border border-border bg-card">
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

/* The free icon set has no Rust glyph, so this is the Rust gear traced from
 * Simple Icons (CC0), in the same tuple shape the set uses. It is a filled
 * shape, and FunnelMark reads the `fill` to know not to stroke it. */
const RUST_MARK: IconSvgElement = [
  [
    "path",
    {
      d: "M23.8346 11.7033l-1.0073-.6236a13.7268 13.7268 0 00-.0283-.2936l.8656-.8069a.3483.3483 0 00-.1154-.578l-1.1066-.414a8.4958 8.4958 0 00-.087-.2856l.6904-.9587a.3462.3462 0 00-.2257-.5446l-1.1663-.1894a9.3574 9.3574 0 00-.1407-.2622l.49-1.0761a.3437.3437 0 00-.0274-.3361.3486.3486 0 00-.3006-.154l-1.1845.0416a6.7444 6.7444 0 00-.1873-.2268l.2723-1.153a.3472.3472 0 00-.417-.4172l-1.1532.2724a14.0183 14.0183 0 00-.2278-.1873l.0415-1.1845a.3442.3442 0 00-.49-.328l-1.076.491c-.0872-.0476-.1742-.0952-.2623-.1407l-.1903-1.1673A.3483.3483 0 0016.256.955l-.9597.6905a8.4867 8.4867 0 00-.2855-.086l-.414-1.1066a.3483.3483 0 00-.5781-.1154l-.8069.8666a9.2936 9.2936 0 00-.2936-.0284L12.2946.1683a.3462.3462 0 00-.5892 0l-.6236 1.0073a13.7383 13.7383 0 00-.2936.0284L9.9803.3374a.3462.3462 0 00-.578.1154l-.4141 1.1065c-.0962.0274-.1903.0567-.2855.086L7.744.955a.3483.3483 0 00-.5447.2258L7.009 2.348a9.3574 9.3574 0 00-.2622.1407l-1.0762-.491a.3462.3462 0 00-.49.328l.0416 1.1845a7.9826 7.9826 0 00-.2278.1873L3.8413 3.425a.3472.3472 0 00-.4171.4171l.2713 1.1531c-.0628.075-.1255.1509-.1863.2268l-1.1845-.0415a.3462.3462 0 00-.328.49l.491 1.0761a9.167 9.167 0 00-.1407.2622l-1.1662.1894a.3483.3483 0 00-.2258.5446l.6904.9587a13.303 13.303 0 00-.087.2855l-1.1065.414a.3483.3483 0 00-.1155.5781l.8656.807a9.2936 9.2936 0 00-.0283.2935l-1.0073.6236a.3442.3442 0 000 .5892l1.0073.6236c.008.0982.0182.1964.0283.2936l-.8656.8079a.3462.3462 0 00.1155.578l1.1065.4141c.0273.0962.0567.1914.087.2855l-.6904.9587a.3452.3452 0 00.2268.5447l1.1662.1893c.0456.088.0922.1751.1408.2622l-.491 1.0762a.3462.3462 0 00.328.49l1.1834-.0415c.0618.0769.1235.1528.1873.2277l-.2713 1.1541a.3462.3462 0 00.4171.4161l1.153-.2713c.075.0638.151.1255.2279.1863l-.0415 1.1845a.3442.3442 0 00.49.327l1.0761-.49c.087.0486.1741.0951.2622.1407l.1903 1.1662a.3483.3483 0 00.5447.2268l.9587-.6904a9.299 9.299 0 00.2855.087l.414 1.1066a.3452.3452 0 00.5781.1154l.8079-.8656c.0972.0111.1954.0203.2936.0294l.6236 1.0073a.3472.3472 0 00.5892 0l.6236-1.0073c.0982-.0091.1964-.0183.2936-.0294l.8069.8656a.3483.3483 0 00.578-.1154l.4141-1.1066a8.4626 8.4626 0 00.2855-.087l.9587.6904a.3452.3452 0 00.5447-.2268l.1903-1.1662c.088-.0456.1751-.0931.2622-.1407l1.0762.49a.3472.3472 0 00.49-.327l-.0415-1.1845a6.7267 6.7267 0 00.2267-.1863l1.1531.2713a.3472.3472 0 00.4171-.416l-.2713-1.1542c.0628-.0749.1255-.1508.1863-.2278l1.1845.0415a.3442.3442 0 00.328-.49l-.49-1.076c.0475-.0872.0951-.1742.1407-.2623l1.1662-.1893a.3483.3483 0 00.2258-.5447l-.6904-.9587.087-.2855 1.1066-.414a.3462.3462 0 00.1154-.5781l-.8656-.8079c.0101-.0972.0202-.1954.0283-.2936l1.0073-.6236a.3442.3442 0 000-.5892zm-6.7413 8.3551a.7138.7138 0 01.2986-1.396.714.714 0 11-.2997 1.396zm-.3422-2.3142a.649.649 0 00-.7715.5l-.3573 1.6685c-1.1035.501-2.3285.7795-3.6193.7795a8.7368 8.7368 0 01-3.6951-.814l-.3574-1.6684a.648.648 0 00-.7714-.499l-1.473.3158a8.7216 8.7216 0 01-.7613-.898h7.1676c.081 0 .1356-.0141.1356-.088v-2.536c0-.074-.0536-.0881-.1356-.0881h-2.0966v-1.6077h2.2677c.2065 0 1.1065.0587 1.394 1.2088.0901.3533.2875 1.5044.4232 1.8729.1346.413.6833 1.2381 1.2685 1.2381h3.5716a.7492.7492 0 00.1296-.0131 8.7874 8.7874 0 01-.8119.9526zM6.8369 20.024a.714.714 0 11-.2997-1.396.714.714 0 01.2997 1.396zM4.1177 8.9972a.7137.7137 0 11-1.304.5791.7137.7137 0 011.304-.579zm-.8352 1.9813l1.5347-.6824a.65.65 0 00.33-.8585l-.3158-.7147h1.2432v5.6025H3.5669a8.7753 8.7753 0 01-.2834-3.348zm6.7343-.5437V8.7836h2.9601c.153 0 1.0792.1772 1.0792.8697 0 .575-.7107.7815-1.2948.7815zm10.7574 1.4862c0 .2187-.008.4363-.0243.651h-.9c-.09 0-.1265.0586-.1265.1477v.413c0 .973-.5487 1.1846-1.0296 1.2382-.4576.0517-.9648-.1913-1.0275-.4717-.2704-1.5186-.7198-1.8436-1.4305-2.4034.8817-.5599 1.799-1.386 1.799-2.4915 0-1.1936-.819-1.9458-1.3769-2.3153-.7825-.5163-1.6491-.6195-1.883-.6195H5.4682a8.7651 8.7651 0 014.907-2.7699l1.0974 1.151a.648.648 0 00.9182.0213l1.227-1.1743a8.7753 8.7753 0 016.0044 4.2762l-.8403 1.8982a.652.652 0 00.33.8585l1.6178.7188c.0283.2875.0425.577.0425.8717zm-9.3006-9.5993a.7128.7128 0 11.984 1.0316.7137.7137 0 01-.984-1.0316zm8.3389 6.71a.7107.7107 0 01.9395-.3625.7137.7137 0 11-.9405.3635z",
      fill: "currentColor",
      key: "rust",
    },
  ],
]

/* Funnel tile marks. Config supplies a semantic key; an unknown key renders
 * no mark, so a typo degrades instead of throwing. */
const FUNNEL_ICONS: Record<string, IconSvgElement> = {
  config: FileSlidersIcon,
  python: PythonIcon,
  javascript: JavaScriptIcon,
  rust: RUST_MARK,
  markdown: QuillWrite01Icon,
  language: LanguageSquareIcon,
  guides: BookOpen01Icon,
  api: ApiIcon,
  pages: Files01Icon,
  folder: FolderOpenIcon,
  search: SearchList01Icon,
  agents: AiFileIcon,
  hash: FingerPrintIcon,
}

/**
 * The mark on a funnel tile. Color is inherited from the tile, so a ghost
 * tile's mark dims with it. HugeiconsIcon does not set aria-hidden itself
 * and the label text is the accessible name.
 */
function FunnelMark({ icon }: { icon?: string }) {
  const glyph = icon ? FUNNEL_ICONS[icon] : undefined
  if (!glyph) return null
  // HugeiconsIcon outlines every path it is given a stroke width for, which
  // would fur a filled glyph; those get none and draw with their own fill.
  const filled = glyph.some(([, attrs]) => attrs.fill === "currentColor")
  return (
    <HugeiconsIcon
      icon={glyph}
      size={18}
      strokeWidth={filled ? undefined : 1.8}
      className="shrink-0"
      aria-hidden="true"
    />
  )
}

/* "funnel" plate defaults — folio's own build, so a bare `- type: funnel`
 * still tells folio's story. Every reader in the binary is a solid tile; a
 * ghost tile is dashed, so unshipped work never renders as shipped. */
const DEFAULT_FUNNEL_INPUTS: LandingFunnelInput[] = [
  { label: "Config file", icon: "config" },
  { label: "Python", icon: "python" },
  { label: "Markdown", icon: "markdown" },
  { label: "JavaScript", icon: "javascript" },
  { label: "Rust", icon: "rust" },
]

const DEFAULT_FUNNEL_OUTPUTS: LandingFunnelOutput[] = [
  { label: "Guides", icon: "guides" },
  { label: "API reference", icon: "api" },
  { label: "llms.txt", icon: "agents" },
  { label: "Markdown pages", icon: "pages" },
]

/* Tile geometry in px, shared by the tile classes and the connector math: a
 * tile is `h-15`, the grid gap is `gap-3`, and the far column hangs `pt-9`
 * below the near one — half a pitch, so every far tile's center lands in a
 * gap between two near tiles and its hairline can pass through to the edge. */
const TILE_H = 60
const TILE_GAP = 12
const TILE_PITCH = TILE_H + TILE_GAP
const FAR_OFFSET = TILE_PITCH / 2

type TileLayout = {
  /* the column nearest the build node; the first half of the items */
  near: LandingFunnelInput[]
  /* the column behind it, hung half a pitch lower; the second half */
  far: LandingFunnelInput[]
  /* block height in px */
  height: number
  /* each item's vertical center in px, in item order */
  centers: number[]
}

/** Split the tiles into the two columns and place them. */
function layoutTiles(items: LandingFunnelInput[]): TileLayout {
  const split = Math.ceil(items.length / 2)
  const near = items.slice(0, split)
  const far = items.slice(split)
  const column = (count: number) =>
    count > 0 ? count * TILE_H + (count - 1) * TILE_GAP : 0
  const height = Math.max(
    column(near.length),
    far.length > 0 ? FAR_OFFSET + column(far.length) : 0
  )
  const centers = items.map((_, index) =>
    index < split
      ? index * TILE_PITCH + TILE_H / 2
      : FAR_OFFSET + (index - split) * TILE_PITCH + TILE_H / 2
  )
  return { near, far, height, centers }
}

/**
 * One tile: a mark on a tinted square, a plain label, and for a roadmap item
 * a dashed border and a small pill in the corner. A product, not a path. The
 * square is the plate's one touch of color beyond the curves, so it takes
 * the accent at a tenth and goes grey on a ghost. Fixed height, so the
 * connector math above holds; a long label truncates instead of wrapping.
 */
function FunnelTile({ item }: { item: LandingFunnelInput }) {
  return (
    <div
      className={cn(
        "flex h-15 flex-col justify-center gap-1.5 rounded-md border bg-background px-2.5",
        item.ghost
          ? "border-dashed border-muted-foreground/50 text-muted-foreground"
          : "border-border text-foreground"
      )}
    >
      <div className="flex items-start justify-between gap-1">
        <span
          className={cn(
            "grid size-7 shrink-0 place-items-center rounded-md",
            item.ghost
              ? "bg-muted text-muted-foreground"
              : "bg-primary/10 text-primary"
          )}
        >
          <FunnelMark icon={item.icon} />
        </span>
        {item.chip ? (
          <span className="rounded-full border border-dashed border-primary/40 bg-primary/5 px-1.5 py-px font-mono text-[8px] font-semibold whitespace-nowrap text-primary">
            {item.chip}
          </span>
        ) : null}
      </div>
      <span className="min-w-0 truncate text-xs font-medium">{item.label}</span>
    </div>
  )
}

/**
 * One side of the plate: tiles in two columns with alternating margins. The
 * column nearest the build node starts at the top; the one behind it hangs
 * half a pitch lower. At lg a far tile sends a hairline through the gap
 * between two near tiles to the block's node-side edge, where its connector
 * curve picks it up, so every tile visibly reaches the build.
 */
function FunnelTileBlock({
  layout,
  side,
}: {
  layout: TileLayout
  side: "inputs" | "outputs"
}) {
  // Below lg there are no curves, so the near/far split has no reader; the
  // shipped column goes first there and the hung column follows.
  const column = (items: LandingFunnelInput[], hung: boolean) => (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-3",
        hung ? "order-last pt-9 lg:order-none" : "order-first lg:order-none"
      )}
    >
      {items.map((item) => (
        <FunnelTile key={item.label} item={item} />
      ))}
    </div>
  )
  // inputs: the node is to the right, so the near column is the right one
  const nearOnLeft = side === "outputs"
  return (
    <div
      className="relative grid grid-cols-2 gap-3"
      style={{ minHeight: layout.height }}
    >
      {nearOnLeft ? column(layout.near, false) : column(layout.far, true)}
      {nearOnLeft ? column(layout.far, true) : column(layout.near, false)}
      {layout.far.map((item, index) => {
        const y = layout.centers[layout.near.length + index]
        return (
          <span
            key={item.label}
            className={cn(
              "absolute hidden h-0 border-t lg:block",
              item.ghost
                ? "border-dashed border-muted-foreground/50"
                : "border-primary"
            )}
            style={
              nearOnLeft
                ? { top: y, left: 0, right: `calc(50% - ${TILE_GAP / 2}px)` }
                : { top: y, left: `calc(50% - ${TILE_GAP / 2}px)`, right: 0 }
            }
            aria-hidden="true"
          />
        )
      })}
    </div>
  )
}

/**
 * "funnel" section: the build-funnel plate — source tiles converge through
 * the `folio build` node and fan out to the output tiles. Each side is a
 * two-column block of icon-and-label tiles with alternating margins; ghost
 * tiles are the roadmap, dashed. One responsive DOM: a five-column grid at
 * lg whose connector columns are stretched SVGs drawn in px (curve endpoints
 * come from the same tile geometry the blocks are laid out with), stacking
 * to a single column below lg where the connectors degrade to a chevron.
 */
function FunnelSection({ section }: { section: LandingSection }) {
  const configInputs = (section.inputs ?? []).filter((input) => input.label)
  const configOutputs = (section.outputs ?? []).filter((output) => output.label)
  const inputs = configInputs.length > 0 ? configInputs : DEFAULT_FUNNEL_INPUTS
  const outputs =
    configOutputs.length > 0 ? configOutputs : DEFAULT_FUNNEL_OUTPUTS
  const command = section.command || "folio build"

  const inLayout = layoutTiles(inputs)
  const outLayout = layoutTiles(outputs)
  // The grid row is as tall as the taller block; the shorter one and the
  // node are centered in it, and the curves are drawn in the same px space.
  const rowHeight = Math.max(inLayout.height, outLayout.height)
  const inTop = (rowHeight - inLayout.height) / 2
  const outTop = (rowHeight - outLayout.height) / 2
  const nodeY = rowHeight / 2

  const connectorStroke = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.4,
    vectorEffect: "non-scaling-stroke",
  } as const

  const chevron = (
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
  )

  return (
    <section className="landing-section border-b border-border bg-muted/20 dark:bg-muted/45">
      <div className="mx-auto max-w-site px-6 py-20">
        <SectionHeading
          eyebrow={section.eyebrow ?? "From source"}
          title={section.title ?? "One build. Every output generated from it."}
          description={section.description}
        />

        <figure className="relative m-0 mt-10 rounded-lg border border-border bg-card p-5 sm:p-7">
          <div className="grid grid-cols-1 gap-y-2 lg:grid-cols-[minmax(0,18rem)_minmax(2.5rem,1fr)_minmax(0,16rem)_minmax(2.5rem,1fr)_minmax(0,18rem)] lg:items-stretch lg:gap-y-0">
            {/* group labels only below lg: the drawn funnel names its own
                flanks, a single stacked column does not. */}
            <p className="m-0 font-mono text-[10px] tracking-[0.14em] text-muted-foreground uppercase lg:hidden">
              Source in
            </p>

            <div className="lg:flex lg:items-center">
              <div className="w-full">
                <FunnelTileBlock layout={inLayout} side="inputs" />
              </div>
            </div>

            <div
              className="relative flex min-w-0 justify-center py-1 lg:block lg:py-0"
              aria-hidden="true"
            >
              {chevron}
              <svg
                className="absolute inset-0 hidden h-full w-full lg:block"
                viewBox={`0 0 100 ${rowHeight}`}
                preserveAspectRatio="none"
              >
                {/* converging curves: every tile → throat */}
                {inputs.map((input, index) => {
                  const y = inTop + inLayout.centers[index]
                  return (
                    <path
                      key={`${input.label}-${index}`}
                      d={`M 0 ${y} C 45 ${y}, 55 ${nodeY}, 100 ${nodeY}`}
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
              <div className="mt-2 rounded-md border border-primary bg-primary/5 px-4 py-4 text-center">
                <svg
                  viewBox="0 0 100 2"
                  preserveAspectRatio="none"
                  className="h-0.5 w-full text-primary"
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
              </div>
              {/* invisible mirror of the command label so the node card
                  centers on the connector columns' midline */}
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
              {chevron}
              <svg
                className="absolute inset-0 hidden h-full w-full lg:block"
                viewBox={`0 0 100 ${rowHeight}`}
                preserveAspectRatio="none"
              >
                {/* diverging curves: throat → every tile */}
                {outputs.map((output, index) => {
                  const y = outTop + outLayout.centers[index]
                  return (
                    <path
                      key={`${output.label}-${index}`}
                      d={`M 0 ${nodeY} C 45 ${nodeY}, 55 ${y}, 100 ${y}`}
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

            <div className="lg:flex lg:items-center">
              <div className="w-full">
                <FunnelTileBlock layout={outLayout} side="outputs" />
              </div>
            </div>
          </div>
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
  "mechanism": MechanismSection,
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
