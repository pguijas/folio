# Installation

*Install Folioh and start the CLI.*

## Install Folioh

Folioh is one native binary. Install it with the standalone installer:

```bash
curl -LsSf https://folioh.site/install.sh | sh
```

The script detects your operating system and architecture, downloads the
matching release archive from GitHub Releases, installs the `folioh` binary into
`~/.local/bin`, and prints `folioh --version`. It warns when that directory is
not on your `PATH` and when Node.js is missing. Your project does not need
Python or any package manager.

Inspect the script before running it:

```bash
curl -LsSf https://folioh.site/install.sh | less
```

The installer reads four optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FOLIOH_VERSION` | `latest` | Release to install, for example `0.3.1`. |
| `FOLIOH_INSTALL_DIR` | `~/.local/bin` | Directory that receives the `folioh` binary. |
| `FOLIOH_REPO` | `pguijas/folioh` | GitHub repository the release archive is fetched from. |
| `FOLIOH_DOWNLOAD_URL` | unset | Full URL of the release archive, for mirrors and air-gapped installs. |

Set them on the `sh` side of the pipe:

```bash
curl -LsSf https://folioh.site/install.sh | FOLIOH_VERSION=0.3.1 sh
```

## Verify

```bash
folioh --version
```

## Upgrade from Folio

The command is `folioh` from 0.3.1 onward. Run the installation command above
and use `folioh` in scripts and CI. The installer leaves an existing `folio`
binary in place. Rename `FOLIO_*` settings to `FOLIOH_*` for the new command.
Older binaries expect the previous archive names; install the new release
with the installer instead of using the old binary's self-update command.

If your project names a preset with the old `folio` prefix, use its `folioh` name.
Update custom template imports, CSS variables and data attributes to the new
namespace as well: for example, `--folio-*` becomes `--folioh-*`. The bundled
template already uses the new names.

## Update

```bash
folioh --update
```

The binary updates itself. It resolves the latest release of `pguijas/folioh`
and, when that release is newer than the installed version, downloads the
archive for your platform and the release's `SHA256SUMS`, verifies the
archive, unpacks it with `tar` beside the binary, swaps it into place and
prints the new version. A binary that is up to date, or ahead of the latest
release, says so and changes nothing; a checksum mismatch, a missing checksum
file, an archive without the binary or a binary that does not start abort
before the installed one is touched. `SHA256SUMS` comes from the same release
as the archive, so it guards against a corrupted or truncated download, not
against a compromised release or mirror. Like the installer it needs `curl`
and `tar`, plus write access to the directory that holds `folioh`. On Windows
the release is a `.zip`, which `tar` also unpacks, and the previous binary
stays beside the new one as `folioh.exe.old`.

`--update` reads two optional environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FOLIOH_REPO` | `pguijas/folioh` | GitHub repository whose releases are checked; the installer reads the same variable. |
| `FOLIOH_RELEASES_URL` | `https://github.com/<FOLIOH_REPO>/releases` | Base URL of the releases, for mirrors: `<base>/latest` must redirect to `<base>/tag/<version>`, and `<base>/download/<tag>/` must serve the archive and `SHA256SUMS`. |

Re-running the installer installs the latest release as well.

## Node.js and pnpm

`folioh build` and `folioh serve` render the site through the bundled Next.js
template and need `Node.js 20.19+` and `pnpm 10`. Enable pnpm through
Corepack and activate pnpm 10, or install it with npm:

```bash
corepack enable pnpm && corepack prepare pnpm@10 --activate
# or
npm install -g pnpm@10
```

## Bundled Template

The Next.js template ships inside the binary. The first `folioh build` or
`folioh serve` materialises it once under the user cache directory,
`$XDG_CACHE_HOME/folioh/template/<version>-<hash>` or the platform equivalent
(`%LOCALAPPDATA%` on Windows, `~/.cache` when neither variable is set), and
every build copies it from there into `.build/`. Set `FOLIOH_TEMPLATE_DIR` to a
template checkout to build from it instead.

## Manual Install

Every release on the [Releases page](https://github.com/pguijas/folioh/releases)
ships one archive per target:

| Target | Archive |
|--------|---------|
| `x86_64-unknown-linux-gnu` | `folioh-x86_64-unknown-linux-gnu.tar.gz` |
| `aarch64-unknown-linux-gnu` | `folioh-aarch64-unknown-linux-gnu.tar.gz` |
| `x86_64-apple-darwin` | `folioh-x86_64-apple-darwin.tar.gz` |
| `aarch64-apple-darwin` | `folioh-aarch64-apple-darwin.tar.gz` |
| `x86_64-pc-windows-msvc` | `folioh-x86_64-pc-windows-msvc.zip` |

Extract the archive and put the `folioh` binary on your `PATH`. The installer
script does not run on Windows; download the `.zip` from the Releases page.

## Build from Source

With a Rust toolchain installed, build the release binary from a checkout:

```bash
git clone https://github.com/pguijas/folioh
cd folioh
cargo build --release
```

The binary is written to `target/release/folioh`.

## Contributing to Folioh

Repository setup and the checks are covered in the
[Developer Guide](/docs/developing).

## Next Steps

Once Folioh is installed, head to the [Quick Start](/docs/quickstart) guide to build your first documentation site.
