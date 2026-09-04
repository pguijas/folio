"use client"

import { AgentsAsk } from "@/components/agents-ask"
import { AgentsBoardCanvas } from "@/components/agents-board-canvas"
import { AgentsDerivation } from "@/components/agents-derivation"
import { AgentsHero } from "@/components/agents-hero"
import { AgentsIndex } from "@/components/agents-index"
import { Band, Measure } from "@/components/agents-kit"
import { AgentsRoadmap } from "@/components/agents-roadmap"
import { AgentsStoreMap } from "@/components/agents-store-map"
import { AgentsTrail } from "@/components/agents-trail"
import { FolioProductSwitcher } from "@/components/folio-product-switcher"
import { normalizeLandingHref } from "@/components/landing/actions"
import type { LandingLink } from "@/components/landing/types"
import { LandingNavbar } from "@/components/landing-navbar"
import { ThemeStyleBootstrap } from "@/components/theme-configurator"

/* This page carries no `__LANDING_*__` markers on purpose. The injector reads
 * one `landing:` block from docs.yaml into one flat replacement map and applies
 * it to every theme page that contains a marker, so a second marker-carrying
 * page would render the Docs landing's copy verbatim. Omitting the markers
 * makes the injector skip the file, exactly as the cover at app/page.tsx does,
 * and the sections below are literal instead. Copy lives here until the config
 * grows a way to describe more than one landing. */

/* The page argues one thing, in this order: there is a place for each kind of
 * thing (the map), nothing has to be registered because placement is the
 * registration (the derivation), here is one place opened and read (the trail),
 * here is the whole store handed back as routes (the index), here is how a
 * change enters it (the writes), here is what is built and what is only named
 * (the roadmap), and here is one way of reading it back (the board).
 *
 * The board arrives last and it arrives as an example. It used to be five of
 * the six sections, which made the page argue the smallest true thing about
 * the product.
 *
 * The order also alternates shape on purpose. The map, the index and the
 * roadmap are all hairline row lists, and three of those in a row is the
 * failure mode of a page built out of measured facts: the code frame and the
 * eighteen-file table sit between the first two, the dated document and the
 * terminals between the rest. Do not reorder them adjacent. */

/* This landing is served from /folio-agents/, one route below the site root,
   so every href it builds from a configured "/path" has to climb back out
   first. The root cover leaves this at its "." default. */
const pathToRoot = ".."

const heroActions: LandingLink[] = [
  {
    title: "Read the guide",
    href: normalizeLandingHref("/docs/agents/", pathToRoot),
    primary: true,
  },
  {
    title: "View source",
    href: "https://github.com/pguijas/folio",
    external: true,
  },
]

/* One distribution puts the mirrors, the indexes, the contract and the board
 * commands in a checkout. There is no separate package to offer. */
const installCommands = [
  "curl -LsSf https://pguijas.github.io/folio/install.sh | sh",
]

const footerLinks: LandingLink[] = [
  { title: "Folio Docs", href: normalizeLandingHref("/folio-docs/", pathToRoot) },
  {
    title: "The protocol",
    href: normalizeLandingHref("/docs/agents/board/agents/", pathToRoot),
  },
  /* `?product=agents` opens the roadmap on this product's card and collapses
     the other. Without it the page opens with both expanded and a reader who
     came from here lands on Folio Docs' plan first. */
  {
    title: "Roadmap",
    href: normalizeLandingHref("/roadmap/?product=agents", pathToRoot),
  },
  {
    title: "GitHub",
    href: "https://github.com/pguijas/folio",
    external: true,
  },
]

export default function FolioAgents() {
  return (
    <div className="landing-shell flex min-h-screen flex-col overflow-hidden">
      <ThemeStyleBootstrap />
      <LandingNavbar
        pathToRoot={pathToRoot}
        productSwitcher={
          <FolioProductSwitcher current="agents" pathToRoot={pathToRoot} />
        }
      />

      <main id="main-content" className="flex-1">
        <AgentsHero
          kicker="Folio for Agents 0.1"
          headline="Everything has a place, and the place is the index."
          description="Folio for Agents proposes where work, decisions and produced files live in a repository. Nothing is registered: putting a file where it belongs is the registration. The board is one reading of it."
          actionLinks={heroActions}
          installCommands={installCommands}
        />

        {/* The one tinted band on the page, and it holds the figure every other
            section is a detail of. */}
        <Band tint seam={false}>
          <Measure>
            <AgentsStoreMap />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <AgentsDerivation />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <AgentsTrail />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <AgentsIndex />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <AgentsAsk />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <AgentsRoadmap />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <AgentsBoardCanvas />
          </Measure>
        </Band>

        <Band>
          <Measure>
            <div className="flex flex-col items-start gap-8">
              <p className="m-0 max-w-3xl text-[30px] leading-[1.16] font-semibold tracking-[-0.024em] text-balance text-foreground sm:text-[42px]">
                A transcript is not a decision.{" "}
                <span className="text-muted-foreground">
                  A file is, and the next session can open it.
                </span>
              </p>
              <div className="flex flex-wrap gap-3">
                <a
                  href="https://github.com/pguijas/folio/tree/board/folio-agents/board"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground"
                >
                  Open the store
                </a>
                <a
                  href={normalizeLandingHref("/docs/agents/board/agents/", pathToRoot)}
                  className="inline-flex items-center justify-center rounded-md border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
                >
                  The agent protocol
                </a>
              </div>
            </div>
          </Measure>
        </Band>
      </main>

      {/* One hairline, no fill. The page has exactly one tinted band and it is
          the one holding the map, so the footer is separated the way every
          section seam above it is. */}
      <footer className="border-t border-border/60">
        <div className="mx-auto flex max-w-site flex-col items-start justify-between gap-8 px-6 py-10 sm:flex-row sm:items-center">
          <div className="flex items-center gap-3">
            <span
              className="grid size-9 place-items-center rounded-lg border border-border bg-card font-mono text-[11px] font-bold text-primary"
              aria-hidden="true"
            >
              fo
            </span>
            <p className="leading-none">
              <span className="block text-sm font-semibold text-foreground">
                Folio for Agents
              </span>
              <span className="mt-1.5 block font-mono text-[10px] text-muted-foreground">
                0.1.0
              </span>
            </p>
          </div>
          <nav className="flex gap-6">
            {footerLinks.map((link) => (
              <a
                key={link.title}
                href={link.href}
                target={link.external ? "_blank" : undefined}
                rel={link.external ? "noopener noreferrer" : undefined}
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {link.title}
              </a>
            ))}
          </nav>
        </div>
      </footer>
    </div>
  )
}
