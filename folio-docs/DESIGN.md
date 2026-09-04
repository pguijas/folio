# Design

## Visual Direction

Folio should read as a technical publishing system: quiet, exact, and source-driven. The landing page is brand register, but it should still borrow the discipline of product UI: compact controls, clear CTAs, visible structure, and no decorative excess.

The current visual direction is restrained monochrome with paper-like OKLCH neutrals, thin rules, source-code artifacts, and small amounts of motion. It should feel like generated documentation becoming a finished static site, not like a generic marketing template.

## Theme

Default scene: a maintainer reviews docs during implementation on a laptop or external monitor, moving between terminal output, generated pages, and source files. The interface should work in both light and dark mode because docs are read during normal daytime development and late maintenance sessions.

Use light mode as the public first impression unless the selected preset changes it. Dark mode must stay first-class for API reading and code-heavy pages.

## Color

Use OKLCH tokens only.

Core default tokens from `template/app/globals.css`:

| Role | Light | Dark |
|------|-------|------|
| Background | `oklch(0.966 0.008 82)` | `oklch(0.130 0.007 82)` |
| Foreground | `oklch(0.155 0.007 82)` | `oklch(0.920 0.007 82)` |
| Card | `oklch(0.976 0.007 82)` | `oklch(0.155 0.007 82)` |
| Muted | `oklch(0.920 0.007 82)` | `oklch(0.210 0.007 82)` |
| Accent | `oklch(0.875 0.026 110)` | `oklch(0.240 0.024 110)` |
| Border | `oklch(0.740 0.007 82)` | `oklch(0.330 0.007 82)` |

Color strategy: restrained. Use foreground and border as structure, primary as action/state, and accent only for low-volume emphasis. Avoid one-hue decorative gradients and large saturated areas unless a future preset explicitly owns that direction.

**Zero elevation.** No `box-shadow`, no `drop-shadow`, no elevation anywhere.
Depth is hairlines, value and air. A card is a border and nothing else; when a
boundary reads too weakly the answer is a stronger border or more space around
it, never a shadow. This is a constant, not a per-component judgement.

Two measured limits, in the preset this site actually ships
(`docs/theme/folio-site`, which is not the table above):

- **`bg-card` is not elevation and not a state.** `--card` and `--background`
  are within 0.001 lightness — 1.00:1 in light mode, 1.04:1 in dark. A card
  that needs to read as a card needs a border and a shadow; a selected state
  drawn with `bg-card` draws nothing at all.
- **`--border` is 1.5:1 against the page.** That is enough for a divider and
  not enough for anything carrying meaning. A status dot, a progress line or a
  checkbox that encodes state takes `border-muted-foreground` (8:1) or a
  fraction of it — never `border-border`, which fails WCAG 1.4.11's 3:1 for
  non-text contrast.

## Typography

Runtime fonts:

- Body: Sora via `next/font/google`, with system fallbacks.
- Code: JetBrains Mono via `next/font/google`, with monospace fallbacks.
- Current article heading token: Georgia stack for the default paper/manual treatment.

Rules:

- Keep documentation prose within 65 to 75 characters where practical.
- **Mono is for code, not labels.** Use JetBrains Mono for commands, file
  paths, version numerals and generated-code signals — nothing else. Eyebrows,
  status words, section labels and back-links take Sora at a small size, with
  weight, colour and letter-spacing doing the work. This rule replaces an
  earlier one that listed "labels" as a mono use; that produced pages where
  mono carried every small string, and it was rejected (owner directive).
- Letter spacing stays `0` unless a component has a narrow technical label
  where uppercase needs clarity. The uppercase `0.14em` treatment is separable
  from the face: keep the tracking, drop the mono.
- Type scale by surface: docs prose stays at body size; a plugin page or
  landing section takes `text-3xl sm:text-4xl font-bold`, and only a true hero
  goes to `text-5xl`/`text-6xl`. Never `clamp()` in a font-size, never
  `font-extrabold`.

## Layout

Landing:

- First viewport should show the project name, value proposition, one primary CTA, optional secondary source link, install command, and generated-docs artifact.
- Do not add decorative icon sets. If an asset is needed, prefer the existing video thumbnail or a real UI/generated-docs preview.
- Action grids must reduce gracefully to one primary CTA when no secondary link exists.
- Avoid nested cards. Use rules, bands, and divided rows for structure.

Documentation:

- Preserve Nextra's predictable docs layout: sidebar, content column, search, theme controls, version selector when configured.
- API pages should optimize for scanning: signatures, parameter tables, class overviews, headings, and source links.
- Long guides can use richer MDX components, but components must serve comprehension.

## Components

Component vocabulary:

- shadcn/ui source components under `template/components/ui`.
- MDX components registered through `template/mdx-components.tsx`.
- Extension components copied into `components/__folio_components`.
- ThemeConfigurator as a global floating control for preset, typography, accent, radius, and color mode.

Interactive components need visible focus, hover, disabled when applicable, and predictable keyboard behavior.

Page headers:

- A page names itself once. No header rule repeating a name the body heading
  already carries.
- A header sits on the page background, not on its own `bg-card` slab behind a
  border — that split reads as two colours stacked rather than one page.
- No decorative backdrops, and never an ornamental diagram above a real one (a
  drawn roadmap spine above the actual roadmap was the specific mistake).
- Cross-links out of the page share the radius, border and height of whatever
  control sits below them, so the header reads as one family.
- Get presence from hierarchy — dominant now, compressed past, faint future —
  not from larger type.
- No UI that narrates itself: no legends, no keyboard hints, no captions
  restating the drawing, no N-of-M ratios. Implement the keyboard, do not
  advertise it. If four states need a legend, fix the states.

## Motion

Use short entrance and state motion only:

- Landing reveals use `cubic-bezier(0.16, 1, 0.3, 1)`.
- Build-artifact motion may suggest parsing or generation, but should remain subtle.
- Do not animate layout properties.
- Respect `prefers-reduced-motion` by removing entrance, scan, pulse, and transition effects.

## Copy

Voice: direct, concrete, and code-grounded.

Preferred claims:

- "Three commands."
- "One config file."
- "Generated from Python source and Markdown."
- "Static Nextra site with search and LLM files."

Avoid:

- Vague words like magical, effortless, revolutionary, or beautiful unless the interface proves the claim.
- Process-heavy promises that are not visible in code or documentation.
- In-app instructional copy that explains obvious controls.

## Open Design Questions

- Whether the public landing should show the actual demo video thumbnail in the first viewport or keep the current generated-docs artifact as the primary visual.
- Whether the default preset should remain paper/manual styled or move closer to a neutral developer-docs style for generated third-party projects.
- Whether future landing sections should be generated from actual routes/modules instead of static feature content.
