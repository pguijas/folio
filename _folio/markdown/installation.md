# Installation

*Install Folio and start the CLI.*

## Install Folio

Folio is one native binary. Install it with the standalone installer:

```bash
curl -LsSf https://pguijas.github.io/folio/install.sh | sh
```

The script detects your operating system and architecture, downloads the
matching release archive from GitHub Releases, installs the `folio` binary into
`~/.local/bin`, and prints `folio --version`. It warns when that directory is
not on your `PATH` and when Node.js is missing. Your project does not need
Python or any package manager.

Inspect the script before running it:

```bash
curl -LsSf https://pguijas.github.io/folio/install.sh | less
```

The installer reads four optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FOLIO_VERSION` | `latest` | Release to install, for example `0.3.0-a1`. |
| `FOLIO_INSTALL_DIR` | `~/.local/bin` | Directory that receives the `folio` binary. |
| `FOLIO_REPO` | `pguijas/folio` | GitHub repository the release archive is fetched from. |
| `FOLIO_DOWNLOAD_URL` | unset | Full URL of the release archive, for mirrors and air-gapped installs. |

Set them on the `sh` side of the pipe:

```bash
curl -LsSf https://pguijas.github.io/folio/install.sh | FOLIO_VERSION=0.3.0-a1 sh
```

## Verify

```bash
folio --version
```

## Update

```bash
folio --update
```

The binary updates itself. It resolves the latest release of `pguijas/folio`
and, when that release is newer than the installed version, downloads the
archive for your platform and the release's `SHA256SUMS`, verifies the
archive, unpacks it with `tar` beside the binary, swaps it into place and
prints the new version. A binary that is up to date, or ahead of the latest
release, says so and changes nothing; a checksum mismatch, a missing checksum
file, an archive without the binary or a binary that does not start abort
before the installed one is touched. `SHA256SUMS` comes from the same release
as the archive, so it guards against a corrupted or truncated download, not
against a compromised release or mirror. Like the installer it needs `curl`
and `tar`, plus write access to the directory that holds `folio`. On Windows
the release is a `.zip`, which `tar` also unpacks, and the previous binary
stays beside the new one as `folio.exe.old`.

`--update` reads two optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FOLIO_REPO` | `pguijas/folio` | GitHub repository whose releases are checked; the installer reads the same variable. |
| `FOLIO_RELEASES_URL` | `https://github.com/<FOLIO_REPO>/releases` | Base URL of the releases, for mirrors: `<base>/latest` must redirect to `<base>/tag/<version>`, and `<base>/download/<tag>/` must serve the archive and `SHA256SUMS`. |

Re-running the installer installs the latest release as well.

## Node.js and pnpm

`folio build` and `folio serve` render the site through the bundled Next.js
template and need `Node.js 20.19+` and `pnpm 10`. Enable pnpm through
Corepack and activate pnpm 10, or install it with npm:

```bash
corepack enable pnpm && corepack prepare pnpm@10 --activate
# or
npm install -g pnpm@10
```

## Bundled Template

The Next.js template ships inside the binary. The first `folio build` or
`folio serve` materialises it once under the user cache directory,
`$XDG_CACHE_HOME/folio/template/<version>-<hash>` or the platform equivalent
(`%LOCALAPPDATA%` on Windows, `~/.cache` when neither variable is set), and
every build copies it from there into `.build/`. Set `FOLIO_TEMPLATE_DIR` to a
template checkout to build from it instead.

## Manual Install

Every release on the [Releases page](https://github.com/pguijas/folio/releases)
ships one archive per target:

| Target | Archive |
|--------|---------|
| `x86_64-unknown-linux-gnu` | `folio-x86_64-unknown-linux-gnu.tar.gz` |
| `aarch64-unknown-linux-gnu` | `folio-aarch64-unknown-linux-gnu.tar.gz` |
| `x86_64-apple-darwin` | `folio-x86_64-apple-darwin.tar.gz` |
| `aarch64-apple-darwin` | `folio-aarch64-apple-darwin.tar.gz` |
| `x86_64-pc-windows-msvc` | `folio-x86_64-pc-windows-msvc.zip` |

Extract the archive and put the `folio` binary on your `PATH`. The installer
script does not run on Windows; download the `.zip` from the Releases page.

## Build from Source

With a Rust toolchain installed, build the release binary from a checkout:

```bash
git clone https://github.com/pguijas/folio
cd folio
cargo build --release
```

The binary is written to `target/release/folio`.

## Contributing to Folio

Repository setup and the checks are covered in the
[Developer Guide](/docs/developing).

## Next Steps

Once Folio is installed, head to the [Quick Start](/docs/quickstart) guide to build your first documentation site.
