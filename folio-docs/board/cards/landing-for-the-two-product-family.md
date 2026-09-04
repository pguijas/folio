---
title: Landing for the two-product family
status: in-progress
priority: high
parent: public-launch-plan
tags: [landing, product, design]
size: L
source: folio#design/landing-v2
type: feature
created: '2026-08-30'
artifacts:
  - doc: landing-direction.md
    label: Direction brief
  - file: candidate-a-family-gateway.html
    label: Candidate A — family gateway
  - file: candidate-b-docs-led.html
    label: Candidate B — Docs-led front door
  - file: hero-gallery.html
    label: Hero gallery — eight alternatives
  - file: hero-01-dual-canvas.html
    label: Hero 01 — Dual canvas
  - file: hero-02-repository-orbit.html
    label: Hero 02 — Repository orbit
  - file: hero-03-stacked-surfaces.html
    label: Hero 03 — Stacked surfaces
  - file: hero-04-split-sheet.html
    label: Hero 04 — Split sheet
  - file: hero-05-signal-rail.html
    label: Hero 05 — Signal rail
  - file: hero-06-living-index.html
    label: Hero 06 — Living index
  - file: hero-07-product-portals.html
    label: Hero 07 — Product portals
  - file: hero-08-editorial-totem.html
    label: Hero 08 — Editorial totem
  - file: hero-v2-gallery.html
    label: Hero V2 gallery — Quiver-informed directions
  - file: hero-v2-01-vector-specimen.html
    label: Hero V2 01 — Vector specimen
  - file: hero-v2-02-editorial-ink.html
    label: Hero V2 02 — Editorial ink
  - file: hero-v2-03-modular-atlas.html
    label: Hero V2 03 — Modular atlas
  - file: hero-v2-04-night-edition.html
    label: Hero V2 04 — Night edition
  - file: architecture-a-prelanding.html
    label: Architecture A — Folio pre-landing
  - file: architecture-b-shared-landing.html
    label: Architecture B — Shared landing with bifurcation
---

Compare two ways to introduce the Folio product family while Folio Docs is
available and Folio for Agents is not: a compact family pre-landing, or a
shared landing that bifurcates below an unchanged hero. Keep their roadmaps,
boards, and release state independent in either architecture.

## Acceptance criteria

- [x] Standalone candidates make the product split legible without changing Folio product files
- [ ] The selected direction gives Folio Docs and Folio for Agents distinct jobs, proofs, and next actions
- [ ] Every present-tense claim maps to shipped behavior and every future surface is visibly marked as roadmap
- [ ] Desktop, mobile, keyboard, reduced-motion, light, and dark presentations pass review
- [ ] The integrated landing keeps Docs navigation and roadmap independent from the Agents board

## Trail

- 2026-08-30 @codex (feat/landing-refresh): opened the isolated worktree and began the Stage 1 source, product, and information-architecture audit.
- 2026-08-30 @codex (board): attached two standalone landing candidates and a decision brief; product files remain unchanged pending owner selection.
- 2026-08-30 @codex (board): HTML validation and board link checks pass; all three rendered artifact URLs respond with HTTP 200 on the local board site.
- 2026-08-30 @codex (cb31fe9f7): owner replaced the artifact round with direct hero guidance; removed the kicker and noisy prefix, sharpened the docs.yaml promise, and moved the heartbeat into Folio Docs; full tests and static build passed.
- 2026-08-30 @codex (1082bad4d): removed the rejected slogan and ships-twice prefix from the remaining README and CLI help surfaces; CLI tests pass.
- 2026-08-30 @codex (board): added eight hero-only illustration alternatives and a comparison gallery; each keeps the visual left, exposes the product selector, and marks Folio for Agents as coming soon.
- 2026-08-30 @codex (board): added a Quiver-informed V2 gallery with four art directions; hero copy remains fixed and product navigation is reserved for the following sections.
- 2026-08-30 @codex (design/landing-v2): froze the pre-refresh landing as design/landing-v1 and made the current refresh the V2 line for direct layout iteration.
- 2026-08-30 @codex (board): added flat, animated prototypes for a Folio pre-landing and a shared landing with post-hero product bifurcation; product files remain unchanged.
- 2026-08-30 @codex (d5eb51718): integrated the pre-landing into the real Folio theme package and the shared bifurcation at 132ab8467; both generated Next workspaces pass TypeScript, ESLint, and live-route checks.
