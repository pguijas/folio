# Contributing to Folio

Thanks for your interest in contributing. Every contribution matters — from bug reports to documentation fixes to new features.

## Getting Started

Folio is one Rust workspace: eleven crates under `crates/` carrying the documentation engine, the CLI host and the plugin interfaces, with `folio-cli` building the `folio` binary. Install a Rust toolchain through [rustup](https://rustup.rs/) — `rust-toolchain.toml` selects the stable channel and the components the checks need, and `rust-version` in the workspace manifest records the 1.85 floor — plus Node.js 20.19+ and pnpm 10 for `folio build`, `folio serve`, and template work. The [Developer Guide](docs/guide/developing.md) covers the repository layout, the tests, and the template in depth; the short version is:

```bash
git clone https://github.com/pguijas/folio.git
cd folio
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo build --release   # target/release/folio
```

For template/UI work:

```bash
cd template && pnpm install && pnpm run dev
```

Unit tests live in separate files beside the module they test, loaded with `#[cfg(test)] #[path = "sidebar_tests.rs"] mod tests;` (`src/sidebar.rs` loads `src/sidebar_tests.rs`; `mod.rs` and `lib.rs` load an adjacent `tests.rs`). Crate integration tests live under each crate's `tests/` directory. The seven docs CLI suites live in `crates/folio-cli/tests/`, the package that builds the binary, so they keep testing the real executable; the release surface checks, workspace boundaries and the shared support those suites load sit beside them. `cargo test -p folio-cli` runs all of these targets; `cargo test --workspace` runs every crate's tests.

## Development Workflow

1. Fork the repository
2. Create a branch from `develop` (`git checkout -b feature/my-feature develop`)
3. Make your changes
4. Run the narrowest useful test while iterating (`cargo test -p <crate>`), then the four cargo commands above once before opening the PR
5. Commit with a clear message
6. Open a pull request against `develop`

## What to Work On

- Check [open issues](https://github.com/pguijas/folio/issues) for bugs and feature requests
- Look for issues labeled `good first issue` for beginner-friendly tasks

## Code Style

- Rust: `cargo fmt` formats and `cargo clippy -- -D warnings` lints; follow existing patterns in the crate you touch
- TypeScript/React: follow the template conventions
- Tests: add tests for new functionality

### Tests that earn their cost

Every test should protect a distinct public behavior or failure boundary. When
new inputs exercise the same code through the same setup, add them to the
existing table-driven test instead of cloning the scenario. Batch cases that
cross an expensive boundary such as a subprocess, Git repository, or site
build, while keeping an assertion that identifies each case. Integration tests
own wiring between units; they do not need to repeat every edge case already
covered by a focused unit test.

During development, run the narrowest useful selection:

```bash
cargo test -p folio-config
cargo test -p folio-cli --test release_surface
```

Run `cargo test --workspace` once after the implementation is complete. This
keeps feedback fast without weakening the final regression gate.

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Folio version (`folio --version`), Node.js version, OS

## Releases

Folio cuts a release branch from reviewed work, updates the version in
`Cargo.toml` and `docs.yaml` (a test keeps the two in agreement) and the
changelog, then runs lint, the full test suite, and a clean site build. After
the release branch lands on `main`, an owner creates the matching `vX.Y.Z` tag;
its GitHub Release carries one archive per platform, the files `install.sh`
downloads.

Patch releases contain compatible fixes. Minor releases collect new public
CLI, configuration, plugin, and template behavior. Unfinished features stay
disabled and out of public navigation until a later release.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
