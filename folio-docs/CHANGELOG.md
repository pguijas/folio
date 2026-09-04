# Changelog

All notable user-facing changes are recorded here. Folio follows semantic
versioning while the public CLI, configuration, and plugin contracts stabilize.

## 0.3.0 — Unreleased

### Added

- A released plugin platform with shared loading, custom components, generated
  pages, CLI extensions, and an authoring contract.
- Agent-readable documentation output: `llms.txt`, `llms-full.txt`, per-page
  Markdown mirrors, and an authoring contract.
- Landing, roadmap, and OpenAPI plugins; OpenAPI remains opt-in.
- Custom templates, theme overlays, project themes, search, branch previews,
  and richer MDX components.

### Changed

- Folio Docs now ships as the independent `folio-docs` distribution and
  `folio_docs` import package. It owns the shared `folio` executable, which
  installed products extend through CLI entry points.
- `folio serve` now exposes the same LLM text files as a static build.
- Markdown mirrors preserve Mermaid source, component children, and useful
  labels without emitting broken MDX fragments.
- Malformed core configuration sections and list fields fail with focused
  errors instead of internal exceptions or character-by-character paths.
- The `nav` list now orders real top-level entries and ignores unknown labels
  instead of silently doing nothing.
- MDX contract 1.1 corrects prop declarations that 1.0 published but the
  bundled components never accepted, and adds the ones they do accept:
  `Tabs.defaultValue`, `TabItem.value` and `TimelineItem.description` are gone,
  `TimelineItem` takes `children`, `FeatureCard` takes `icon`, `BrowserFrame`
  takes `footer`, `AccordionItem` takes `defaultOpen`, and the
  `ApiReferenceIndex` module fields are the ones the component reads. No
  component behaviour changed; the contract now describes what always shipped.
- `output:` is rejected when it names, or contains, a configured source
  directory or the repository's `.git`. The build removes the output directory
  before writing to it, so `output: docs` alongside the documented
  `source.docs: ["docs/"]` default used to delete the sources it had just read.

### Fixed

- MDX escaping no longer leaks into code. Braces and angle brackets inside
  inline code spans and fenced blocks are left alone in both docstrings and
  authored Markdown, so `` `/{repo}` `` renders as written instead of
  `/\{repo\}`. A fence indented under a list item or blockquote, a fence nested
  inside a longer one, and `~~~` fences are all recognized.
- Markdown mirrors keep JSX-looking content inside indented and nested fences
  instead of deleting through the next `>`.
- `llms-full.txt` parameter tables escape pipes in the Type and Default cells,
  so a PEP 604 union such as `str | None` no longer splits its own row.
- Landing `actions` are normalized for every section type. An action without a
  title or a usable href drops with a warning instead of reaching the template,
  where a missing href aborted the prerender.

### Removed

- The unused project overview-video plugin and media copied into every build.
- `OrganicEditorialImagePrompt`, a campaign-specific component outside the
  Folio Docs and Folio for Agents product contract.

### Security

- Updated the bundled frontend and Python locks to versions without known
  production advisories at release preparation time.
- Pinned every third-party action in the PyPI publishing workflow to a full
  commit SHA.
- `folio init` quotes detected project metadata into the generated `docs.yaml`.
  The project name and version read from a repository's `pyproject.toml`, and
  the git remote, were interpolated raw, so a cloned repository could close the
  quote and append top-level keys — `plugins:` among them — to the config Folio
  then trusts. The next `folio` command in that directory, `folio --help`
  included, executed the listed module. This is the case `SECURITY.md` names as
  in scope: Folio loading a plugin nobody listed.

### Not in 0.3

MCP, public IR export, multi-language parsing, i18n, and versioned builds remain
disabled or future work. Their unfinished surfaces are not part of the 0.3 promise.
