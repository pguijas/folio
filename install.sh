#!/bin/sh
# Installs the folio binary from GitHub Releases.
#
#   curl -LsSf https://pguijas.github.io/folio/install.sh | sh
#
# Knobs (all optional):
#   FOLIO_VERSION       release to install, e.g. 0.3.0-a1 (default: latest)
#   FOLIO_INSTALL_DIR   where the binary goes (default: ~/.local/bin)
#   FOLIO_REPO          GitHub repository to fetch from (default: pguijas/folio)
#   FOLIO_DOWNLOAD_URL  full URL of the release archive, for mirrors and air-gapped installs
set -eu

FOLIO_VERSION=${FOLIO_VERSION:-latest}
FOLIO_INSTALL_DIR=${FOLIO_INSTALL_DIR:-$HOME/.local/bin}
FOLIO_REPO=${FOLIO_REPO:-pguijas/folio}
FOLIO_DOWNLOAD_URL=${FOLIO_DOWNLOAD_URL:-}

say() { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

fetch() {
  if have curl; then curl -LsSf "$1" -o "$2"
  elif have wget; then wget -q "$1" -O "$2"
  else die "curl or wget is required"
  fi
}

target() {
  os=$(uname -s)
  arch=$(uname -m)
  case "$arch" in
    x86_64 | amd64) arch=x86_64 ;;
    arm64 | aarch64) arch=aarch64 ;;
    *) die "unsupported architecture: $arch" ;;
  esac
  case "$os" in
    Linux) say "$arch-unknown-linux-gnu" ;;
    Darwin) say "$arch-apple-darwin" ;;
    *) die "unsupported OS: $os. On Windows, download folio-x86_64-pc-windows-msvc.zip from https://github.com/$FOLIO_REPO/releases" ;;
  esac
}

# Check the archive against the SHA256SUMS the release publishes beside it.
# A mirror or an air-gapped copy without one warns instead of failing.
verify() {
  dir=$1 file=$2 sums_url=$3
  if ! fetch "$sums_url" "$dir/SHA256SUMS"; then
    warn "no SHA256SUMS at $sums_url; the archive was not verified"
    return 0
  fi
  expected=$(awk -v a="$file" '$2 == a || $2 == "*"a { print $1 }' "$dir/SHA256SUMS" | head -n1)
  [ -n "$expected" ] || die "SHA256SUMS has no entry for $file"
  if have sha256sum; then actual=$(sha256sum "$dir/$file" | cut -d' ' -f1)
  elif have shasum; then actual=$(shasum -a 256 "$dir/$file" | cut -d' ' -f1)
  else warn "neither sha256sum nor shasum is installed; the archive was not verified"; return 0
  fi
  [ "$expected" = "$actual" ] || die "checksum mismatch for $file: expected $expected, got $actual"
  say "checksum verified"
}

# `folio build` and `folio serve` shell out to Node and pnpm; nothing else does.
check_node() {
  if have node; then
    node_version=$(node -v 2>/dev/null | sed 's/^v//')
    case "$node_version" in
      [0-9]*.[0-9]*)
        node_major=${node_version%%.*}
        node_rest=${node_version#*.}
        node_minor=${node_rest%%.*}
        if [ "$node_major" -lt 20 ] || { [ "$node_major" -eq 20 ] && [ "$node_minor" -lt 19 ]; }; then
          warn "Node.js $node_version is below the 20.19 'folio build' and 'folio serve' need"
        fi
        ;;
      *) warn "could not read a version from 'node -v'; 'folio build' and 'folio serve' need Node.js 20.19+" ;;
    esac
  else
    warn "Node.js 20.19+ is needed for 'folio build' and 'folio serve'"
  fi
  have pnpm || warn "pnpm 10 is needed for 'folio build' and 'folio serve'"
}

main() {
  triple=$(target)
  asset="folio-$triple.tar.gz"
  if [ -n "$FOLIO_DOWNLOAD_URL" ]; then
    url=$FOLIO_DOWNLOAD_URL
  elif [ "$FOLIO_VERSION" = latest ]; then
    url="https://github.com/$FOLIO_REPO/releases/latest/download/$asset"
  else
    url="https://github.com/$FOLIO_REPO/releases/download/v${FOLIO_VERSION#v}/$asset"
  fi

  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  say "downloading $url"
  fetch "$url" "$tmp/$asset" || die "no release archive at $url"
  verify "$tmp" "$asset" "${url%/*}/SHA256SUMS"
  tar -xzf "$tmp/$asset" -C "$tmp"
  [ -f "$tmp/folio" ] || die "archive did not contain a folio binary"

  mkdir -p "$FOLIO_INSTALL_DIR"
  install -m 755 "$tmp/folio" "$FOLIO_INSTALL_DIR/folio"
  version=$("$FOLIO_INSTALL_DIR/folio" --version) || die "the installed binary does not run on this machine"
  say "installed $version to $FOLIO_INSTALL_DIR/folio"

  case ":$PATH:" in
    *":$FOLIO_INSTALL_DIR:"*) ;;
    *) warn "$FOLIO_INSTALL_DIR is not on your PATH" ;;
  esac
  check_node
}

main
