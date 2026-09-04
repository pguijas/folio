# Contributing to Folio

Thanks for your interest in contributing! Every contribution matters — from bug reports to documentation fixes to new features.

## Getting Started

Install Python 3.10+, [uv](https://docs.astral.sh/uv/), Node.js 20.19+, and pnpm 10. Folio is a Python CLI, but builds and previews use the bundled Nextra/Next.js template through pnpm.

```bash
git clone https://github.com/pguijas/folio.git
cd folio
uv sync
uv run pytest tests/ -v
uv run ruff check .
uv run folio build --clean
```

For template/UI work:

```bash
cd template && pnpm install && pnpm run dev
```

## Development Workflow

1. Fork the repository
2. Create a branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the smallest relevant test file while iterating, then run the full suite and lint once before opening the PR (`uv run pytest tests/ -q` and `uv run ruff check .`)
5. Commit with a clear message
6. Open a pull request

## What to Work On

- Check [open issues](https://github.com/pguijas/folio/issues) for bugs and feature requests
- Look for issues labeled `good first issue` for beginner-friendly tasks

## Code Style

- Python: follow existing patterns in the codebase
- TypeScript/React: follow the template conventions
- Tests: add tests for new functionality

### Tests that earn their cost

Every test should protect a distinct public behavior or failure boundary. When
new inputs exercise the same code through the same setup, add them to the
existing parameterized or table-driven test instead of cloning the scenario.
Batch cases that cross an expensive boundary such as a subprocess, Git
repository, or site build, while keeping an assertion that identifies each
case. Integration tests own wiring between units; they do not need to repeat
every edge case already covered by a focused unit test.

During development, run the narrowest useful selection:

```bash
uv run pytest tests/test_config.py -q
uv run pytest tests/test_config.py::test_load_config -q
```

Run `uv run pytest tests/ -q` once after the implementation is complete. This
keeps feedback fast without weakening the final regression gate.

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version, Node.js version, OS

## Releases

Folio cuts a release branch from reviewed work, updates the version and
changelog, then runs lint, the full test suite, a clean site build, page smoke
checks, and a clean-wheel install. After the release branch lands on `main`, an
owner creates the matching `vX.Y.Z` tag or manually dispatches the release
workflow. That workflow verifies the version again before publishing to PyPI.

Patch releases contain compatible fixes. Minor releases collect new public
CLI, configuration, plugin, and template behavior. Unfinished features stay
disabled and out of public navigation until a later release.

## License

By contributing, you agree that your contributions will be licensed under AGPL-3.0-only.
