# Landing direction: two products, one repository truth

## Objective

Make the split between Folio Docs and Folio for Agents legible from the first viewport without discarding the landing's approved hero, editorial tone, or artifact-first proof style.

## What is fixed

- The approved kicker, headline, and one-sentence description remain unchanged unless the owner opens a deliberate copy round.
- Folio Docs is a docs generator. Folio for Agents is a repository-native meta-harness, not an orchestrator and not a replacement for coding tools.
- Present-tense claims need shipped proof. Future work stays visibly marked as roadmap.
- The page should show generated output, repository files, or the real board instead of decorative icon grids.
- The two products are being split into independent installs and releases: `folio-docs` 0.3 and `folio-agents` 0.1.

## Current landing audit

The existing landing has strong raw material:

- The heartbeat hero demonstrates source becoming a real documentation page.
- The funnel explains inputs, the build, and static outputs without relying on abstract brand art.
- The harness section already names both products and avoids orchestration claims.
- All sections are config-driven, responsive, theme-aware, and covered by reduced-motion rules.

The split exposes four structural mismatches:

1. The navbar, hero action, install command, and footer all lead to one undifferentiated Folio surface.
2. The product split appears only after the Docs build funnel, so it reads as a secondary feature rather than the page's organizing model.
3. The harness diagram assumes a shared core while the active product work now creates separately installed and released packages.
4. Docs outputs, agent work state, and their optional integration are shown in one flow, which blurs which product owns each result.

There is also one source-of-truth conflict to resolve before integration: `PRODUCT.md` says the 0.3 distinction does not require separate packages, while the active split implements independent packages and releases. The landing should follow the confirmed product model after that text and code agree.

## Candidate A: family gateway

[Open the rendered family-gateway prototype](/_folio/kanban/landing-for-the-two-product-family/candidate-a-family-gateway.html)

The root URL represents the Folio family. The first viewport keeps the approved Docs promise but places a product map beside it. The next section gives Docs and Agents equal weight, with separate jobs, installs, proofs, and next actions.

Choose this when `pguijas.github.io/folio/` is the public front door for both products.

Strengths:

- The product split is visible before scrolling.
- Independent packages and releases are explicit.
- The optional Docs integration is shown as a boundary, not a shared runtime.
- Both products can grow without turning one into a feature of the other.

Cost:

- The Docs-specific approved headline still anchors a family page. A later deliberate copy round may decide whether that remains desirable.
- Navigation and release proof need stable Agents destinations, not placeholder routes.

## Candidate B: Docs-led front door

[Open the rendered Docs-led prototype](/_folio/kanban/landing-for-the-two-product-family/candidate-b-docs-led.html)

The root URL belongs to Folio Docs. The current hero and build story remain dominant. A strong family band introduces Folio for Agents as an independently installed companion product, then returns to Docs proof.

Choose this when the current site remains the product site for `folio-docs` and Folio for Agents will get its own durable destination.

Strengths:

- The approved hero, primary audience, and conversion path remain coherent.
- The site can ship before a complete Agents marketing/documentation surface exists.
- Ownership is simple: Folio Docs generates and owns this site.

Cost:

- Folio for Agents remains secondary even though the repository README presents two independent products.
- The shared Folio family lacks a true home until another surface is created.

## Decision

| Question | Candidate A | Candidate B |
| --- | --- | --- |
| Root site represents | Folio family | Folio Docs |
| Product weight | Equal | Docs primary |
| Hero | Approved copy + family map | Approved copy + Docs artifact |
| Agents destination required now | Yes | Not beyond one proof/quickstart route |
| Best fit with independent packages | Strongest | Transitional |

Recommendation: **Candidate A**, if the package split is the confirmed product direction. It gives the repository README, installs, releases, navigation, and landing one model. Candidate B is the safer transition if Folio for Agents does not yet have a public quickstart and stable routes.

## Stage 2 integration shape

After the owner confirms A or B:

1. Rebase `feat/landing-refresh` onto the completed product-split branch.
2. Resolve the `PRODUCT.md` package-model conflict deliberately before changing landing copy.
3. Keep the approved hero component and evolve the existing `harness` section rather than adding an overlapping section type. Add only the data needed for independent commands, links, and proof labels.
4. Update Folio's `docs.yaml` composition and landing navigation. Keep generic landing-plugin defaults product-neutral.
5. Keep Docs navigation and roadmap on the Docs release cycle; link the Agents product without embedding its board state.
6. Pin the public behavior in the existing landing config/site-builder tests, then update the landing guide if the public section contract changes.
7. Validate the complete page at desktop and mobile widths, in light and dark themes, by keyboard, with reduced motion, and through a clean static export.

## Validation state

- Source, product, active split, landing config, component catalog, and board cards audited on 2026-08-30.
- Both candidates are standalone and leave product files unchanged.
- Candidate A, Candidate B, the direction brief, and the filtered board URL return HTTP 200 from the local Folio development site.
- Board page generation and internal link validation pass. The full static export is blocked by an unrelated existing `RoadmapPhase`/`milestone` type mismatch on the board branch.
- Interactive browser review is pending because no in-app browser backend was connected in this session.
