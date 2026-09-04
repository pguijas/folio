---
title: init writes only the sources that exist
status: released
tags: [cli, bug]
type: bug
created: '2026-08-26'
---

Owner report from pguijas/kanban: every serve prints "Python source path
not found: .../src" on a repository that has no Python. `folio init -y`
writes `source.python.paths: ["src/"]` and a nav entry "API Reference"
unconditionally (folio/cli.py, _generate_docs_yaml region ~900-968), so a
board-only project's config claims sources that do not exist and the build
warns about its own scaffolding forever.

Fix direction: init detects. Write the python block only when a Python
source layout exists (src/ or a top-level package); otherwise write it
commented out, so the config documents how to enable it without claiming
it. Same rule for the "API Reference" nav entry. The kanban front-page
guard already treats configured-but-missing paths as not publishing; this
fix removes the state at its origin.

## Acceptance criteria
- [x] folio init -y on a repo with no Python writes a commented python block and no API Reference nav entry
- [x] folio init -y on a repo with src/ (or a detectable package) keeps today's output
- [x] A board-only init produces a build with zero source warnings

## Comments
- 2026-08-27 @claude: Criterion 3 (board-only build, zero source warnings) is verified by mechanism, not by a build-running test: folio/build.py:613 only warns about configured paths and a no-Python init writes the block commented. No E2E test runs an actual build asserting zero warnings; acceptable for a bug card, but noted.

## Trail
- 2026-08-26 @pguijas (4b065c3bf): detection cascade keeps its four candidates and stops inventing src/; commented block + conditional nav; E2E quickstart builds with zero source warnings
- 2026-08-27 @claude: audit: detection cascade at folio/cli.py:877-889, commented block at :951-956, conditional nav at :973-974; test_init_without_python_sources_writes_a_commented_block and test_init_with_src_keeps_the_python_block pass; the sole warning emitter (folio/build.py:613) cannot fire on a board-only config
