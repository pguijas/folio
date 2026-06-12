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
4. Run tests and lint (`uv run pytest tests/ -v` and `uv run ruff check .` — CI enforces both)
5. Commit with a clear message
6. Open a pull request

## What to Work On

- Check [open issues](https://github.com/pguijas/folio/issues) for bugs and feature requests
- Look for issues labeled `good first issue` for beginner-friendly tasks

## Code Style

- Python: follow existing patterns in the codebase
- TypeScript/React: follow the template conventions
- Tests: add tests for new functionality

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version, Node.js version, OS

## License

By contributing, you agree that your contributions will be licensed under AGPL-3.0-only.
