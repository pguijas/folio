# Developer Guide

*How to build, test, and run everything in the repository from a checkout.*

Folio ships as one native Rust binary: `folio`.
The repository is one Cargo workspace plus the site template the binary renders
through. This guide covers building the binary, running the tests, and working
on the template.

## Prerequisites

| Tool | Needed for | Notes |
|------|------------|-------|
| Rust toolchain | The workspace | Install via [rustup](https://rustup.rs/). `rust-toolchain.toml` pins the stable channel with `clippy` and `rustfmt`; rustup picks it up automatically. |
| Node.js 20.19+ and pnpm 10 | `folio build`, `folio serve`, and template work | The generated site renders through the bundled Nextra/Next.js template. Not needed to build the binary or run `cargo test`. Get pnpm with `corepack enable pnpm && corepack prepare pnpm@10 --activate`, or `npm install -g pnpm@10`. |

## Get the source

```bash
git clone https://github.com/pguijas/folio
cd folio
```

## Repository layout

The root `Cargo.toml` coordinates the packages in one virtual workspace.

- `crates/*` contains the eleven engine crates: the CLI host (`folio-cli`),
  configuration, parsers, page generation, plugin interfaces, site builder and
  watcher. `folio-cli` is both the library and the package that builds the
  released `folio` binary, from `src/bin/folio.rs`.

Beside the crates:

- `docs/examples/` — the small example projects the guides build and the tests
  read. What a build must produce from them is checked in as a golden beside
  the crate that produces it, under `crates/<crate>/tests/fixtures/`.
- `template/` — the Nextra/Next.js site template, built with pnpm.
- `docs/` — the guides on this site. The root `docs.yaml` is the
  config of Folio's own site and `theme/folio-site` its theme.
- `install.sh` — the installer behind the install one-liner.

## Build and verify

Run these from the repository root. The first three are the Rust checks CI
runs (CI adds `--locked`); [What CI runs](#what-ci-runs) lists the rest.

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo build --release
```

- `cargo fmt --all --check` verifies formatting without rewriting files; drop
  `--check` to apply it.
- `cargo clippy --workspace --all-targets -- -D warnings` lints every crate and
  target. CI treats warnings as errors with `-D warnings`; match it locally to
  avoid surprises.
- `cargo test --workspace` runs the tests across all crates.
- `cargo build --release` produces `target/release/folio` using the thin-LTO,
  stripped release profile.

### Installing the binary you built

The release build is a single self-contained executable. Copy
`target/release/folio` to a directory on your `PATH` (for example
`~/.local/bin/`) and run `folio --version` to confirm the shell picks up your
build rather than an installed release. To run a command without installing,
`cargo run --release -p folio-cli -- build --clean` builds and runs the same
binary.

## Tests

`cargo test --workspace` runs every crate's tests. Unit tests live in a
separate file beside the module they test: `src/sidebar.rs` declares
`#[cfg(test)] #[path = "sidebar_tests.rs"] mod tests;` and loads
`src/sidebar_tests.rs`. Tests for `lib.rs`, `main.rs`, or `mod.rs` use a
`tests.rs` file in the same directory. This keeps access to private helpers
without mixing the test bodies into implementation files, and a directory
under `src/` only ever holds submodules. Shared test-only helpers use
separate child modules the same way.

Crate integration tests live under each crate's `tests/` directory. The CLI
suites live in `crates/folio-cli/tests/`, including the documentation
checks in `docs_surface.rs`: that is the package that builds the binary, so
they keep testing the actual executable.

The same directory holds the release surface checks (`release_surface.rs`),
workspace layout rules (`workspace_boundaries.rs`), and the shared support the
CLI suites load with `mod common;` (`common/`).
`cargo test -p folio-cli` runs all of these targets.

Narrow the run while iterating:

```bash
cargo test -p folio-config                      # one crate
cargo test -p folio-cli --test release_surface  # one integration test file
cargo test -p folio-cli the_one_liner           # tests whose name contains a string
```

A new behaviour lands with its test: a unit test when it is local to one
function, an integration test under the crate's `tests/` when it crosses crates
or touches the filesystem, and a black-box run of the binary when it is what a
user sees. The CLI tests in `crates/folio-cli/tests/` run the built binary
through `env!("CARGO_BIN_EXE_folio")` against a project from `docs/examples/`
and check the result against the checked-in golden. The fixtures and the tests
are the definition of correct output.

Each crate keeps the fixtures its own tests read under
`crates/<crate>/tests/fixtures/`: the config that must load without a warning
(`folio-config`), the sources each reader must parse with the IR they must
parse to (`golden_ir.json` in `folio-lang-javascript` and `folio-lang-rust`;
`rich_package_ir.json` and `example_package_ir.json` in `folio-lang-python`,
the second for the example package under `docs/examples/generated-site/`), the
MDX contract baseline (`folio-plugins`) and the pages, `llms.txt` and
`llms-full.txt` a build must write (`folio-docs`, compared again through the
CLI by `folio-cli`). `FOLIO_UPDATE_GOLDEN=1` rewrites the goldens of these
tests:

```bash
FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-lang-python --test golden
FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-lang-javascript --test golden
FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-lang-rust --test golden
FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-docs --test example_site
FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-plugins --test template_pins
```

The diff is the point: a golden regenerated without reading it turns a
regression into the contract.

### Benchmarks

`crates/folio-lang-python/benches/parse.rs` is a criterion
parse-throughput benchmark over the `*.py` files under `$FOLIO_BENCH_CORPUS`.
The crate declares it as a `[[bench]]` target with `harness = false` and keeps
`criterion` as a dev-dependency, so `cargo bench -p folio-lang-python` runs it.

## The template

Everything `folio build` renders comes from `template/`, a
Next.js/Nextra workspace. Work on it directly with pnpm:

```bash
cd template
pnpm install
pnpm run dev
```

`pnpm run lint` and `pnpm run typecheck` are the template's own checks.

## What CI runs

One workflow gates changes: `rust` (`.github/workflows/rust.yml`). It runs on
pushes and pull requests to `main` and `develop` and on `v*` tags, and the
release workflow calls it before building. Its jobs install the stable
toolchain and cache the build:

- `lint` (Linux) runs `cargo fmt --all --check` and
  `cargo clippy --workspace --all-targets --locked -- -D warnings`, then the
  template's `pnpm install --frozen-lockfile`, `pnpm lint` and
  `pnpm typecheck` on Node 22 and pnpm 10.
- `test` (Linux and macOS) runs `cargo test --workspace --locked` on Node 22.
- `windows` runs `cargo test -p folio-cli --test cli_surface --locked`.
- `real-export` (Linux) runs the two suites ignored by default because they
  run a real pnpm install and Next export:
  `cargo test -p folio-site --test e2e_export --locked -- --ignored` and
  `cargo test -p folio-cli --test build_pipeline --locked -- --ignored`.

CI does not run `cargo build --release`; the release workflow does.

## Releasing

A release is a tag. Bump `version` in the root `Cargo.toml` and `project.version`
in `docs.yaml` to the same string, spelled the Cargo way (`0.3.0-a1`; the tests
check they agree), record the changes in `CHANGELOG.md` under a
`## <version> — <date>` heading, merge, then tag `v<version>` and push the
tag:

```bash
git tag v0.3.0-a1
git push origin v0.3.0-a1
```

`.github/workflows/release.yml` fails before building if the tag does not match
the workspace version. It then builds one archive per target on five
targets (Linux and macOS on x86_64 and aarch64 as `.tar.gz` with the `folio`
binary at the archive root, which `install.sh` installs, and Windows x86_64 as
a `.zip` to download by hand), runs
`install.sh` against the two archives the runners execute natively (x86_64
Linux, arm64 macOS), and publishes a GitHub Release with the archives, a
`SHA256SUMS` file and the version's `CHANGELOG.md` entry as its notes; a
version with no entry fails the release. `install.sh` downloads from
`releases/latest`, so releases are published as regular releases, not
prereleases, while the version string carries the alpha.

Pushing a tag is the publication decision; only the repository owner tags.
Pull requests that touch the workflow or the installer run the build matrix
without publishing, so the release path is proven before a tag exists.

## Next steps

- [Architecture](/docs/architecture) — How the CLI, parser, generator, and export pipeline fit together
- [CLI Reference](/docs/cli) — Every command, flag, and option
- [Writing Doc Comments](/docs/docstrings) — How Folio reads Python docstrings, JSDoc and Rust doc comments
