# Product

## Users

Folio is for Python maintainers, library authors, internal platform teams, and developer tooling teams who need a polished documentation site without adopting a large Sphinx setup. They are usually working inside an existing codebase and want the docs to stay close to source, config, tests, and release automation.

Primary visitor contexts:

- A maintainer evaluating whether Folio can replace Sphinx for a Python package.
- A contributor opening the generated docs to understand the project structure.
- A developer reading API reference, guides, migration notes, or LLM-friendly output.

## Product Purpose

Folio turns Python source code and Markdown guides into a static Nextra documentation site with API reference pages, search, dark mode, rich MDX components, and optional `llms.txt` files.

Success means the generated site feels complete from the first build: clear navigation, trustworthy API pages, minimal setup, and fast feedback.

## Brand Personality

Precise, spare, engineering-native.

Folio should feel like a serious developer tool that respects maintainers' time. It should communicate confidence through clean structure, exact copy, and working code examples, not through decorative claims.

## Anti-references

- Generic SaaS landing pages with oversized icon grids, vague feature cards, and decorative gradients.
- Documentation sites that require extensive theme hunting before they look acceptable.
- Heavy process artifacts in the repository that age faster than code and documentation.
- Decorative icon packs when a video thumbnail, real UI, terminal command, or generated docs preview carries the message better.
- In-app copy that explains obvious UI mechanics instead of letting the interface work.

## Design Principles

1. Show the artifact. Prefer real generated docs, command output, API pages, and the demo video over decorative abstractions.
2. Keep the promise small and provable. Three commands, one config file, generated docs from source.
3. Make minimal feel deliberate. Fewer links, fewer cards, fewer icons, stronger hierarchy.
4. Treat documentation as product quality. Code, docs, and configuration must agree.
5. Keep customization structured. Plugins, named components, presets, and config should be explicit and testable.

## Accessibility & Inclusion

Target WCAG AA for generated sites. Preserve keyboard navigation, visible focus, skip links, reduced-motion behavior, readable contrast in light and dark modes, and responsive layouts that do not require horizontal scrolling for normal prose.

Motion should clarify build or state transitions, and must be disabled by `prefers-reduced-motion`.
