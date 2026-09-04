---
title: Folio Docs distribution 0.3.0
status: in-review
priority: high
created: '2026-07-16'
tags: [release]
type: release
size: L
---

Package, tag, and publish Folio Docs independently. This card owns the
`folio-docs` 0.3 distribution and the `docs-v*` release cadence. Folio for
Agents has a separate board, distribution, tag sequence, and release gate.

## Acceptance criteria
- [x] Folio Docs 0.3.0 is consistent across package, CLI, docs, lockfiles, and version matrix
- [x] CHANGELOG and release notes describe the shipped surface and disabled features
- [ ] Folio Docs 0.3 reaches its release criteria
- [x] Distributed Python and frontend dependencies have no known production vulnerabilities
- [x] The built wheel installs and runs in a clean environment
- [x] Tests, clean build, serve, and representative page checks pass
- [x] The release cadence is documented
- [ ] Tag, push, and PyPI publication happen only after explicit owner approval

## Comments
- 2026-08-27 @claude: High priority confirmed; PyPI parity and a cadence remain required.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-29 @codex (release/0.3.0): refreshed from the live PyPI and git state; scoped to 0.3.0 preparation with publication kept behind owner approval.
- 2026-08-29 @codex (d9b829122): prepared 0.3.0; 1,236 tests, clean build, serve and route probes, audits, lint, type checks, and clean-wheel install passed.
- 2026-08-29 @codex (board): split product readiness into independent Docs 0.3 and Agents 0.1 release cards.
- 2026-08-30 @codex (board): moved into the standalone Docs board and removed every Agents release dependency.
