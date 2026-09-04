# Changelog

All notable user-facing changes are recorded here. Folio follows semantic
versioning while the public CLI, configuration, and plugin contracts stabilize.

## 0.3.0 — Unreleased

### Added

- A released plugin platform with shared loading, custom components, generated
  pages, CLI extensions, and an authoring contract.
- Folio for Agents outputs: `llms.txt`, `llms-full.txt`, per-page Markdown
  mirrors, an authoring contract, and a git-backed cardfile board with
  published artifacts.
- Landing, roadmap, kanban, and OpenAPI plugins; OpenAPI remains opt-in.
- Custom templates, theme overlays, project themes, search, branch previews,
  and richer MDX components.

### Changed

- Folio is presented as a product family: Folio Docs is the docs
  generator; Folio for Agents is the meta-harness, a harness over harnesses.
- `folio serve` now exposes the same LLM text files as a static build.
- Markdown mirrors preserve Mermaid source, component children, and useful
  labels without emitting broken MDX fragments.
- Malformed core configuration sections and list fields fail with focused
  errors instead of internal exceptions or character-by-character paths.
- The `nav` list now orders real top-level entries and ignores unknown labels
  instead of silently doing nothing.

### Removed

- The unused project overview-video plugin and media copied into every build.
- `OrganicEditorialImagePrompt`, a campaign-specific component outside the
  Folio Docs and Folio for Agents product contract.

### Security

- Updated the bundled frontend and Python locks to versions without known
  production advisories at release preparation time.
- Pinned every third-party action in the PyPI publishing workflow to a full
  commit SHA.

### Not in 0.3

Browser or remote board writes, sync backends, agent orchestration, MCP, public
IR export, multi-language parsing, i18n, and versioned builds remain disabled
or future work. Their unfinished surfaces are not part of the 0.3 promise.
