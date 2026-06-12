#!/bin/sh
set -eu

FOLIO_PACKAGE=${FOLIO_PACKAGE:-folio-docs}
FOLIO_VERSION=${FOLIO_VERSION:-}
FOLIO_INSTALL_SPEC=${FOLIO_INSTALL_SPEC:-}
FOLIO_UV_INSTALL_URL=${FOLIO_UV_INSTALL_URL:-https://astral.sh/uv/install.sh}
FOLIO_BOOTSTRAP_UV=${FOLIO_BOOTSTRAP_UV:-0}
FOLIO_SKIP_PNPM_SETUP=${FOLIO_SKIP_PNPM_SETUP:-0}

say() {
  printf '%s\n' "$*"
}

warn() {
  printf 'warning: %s\n' "$*" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

have() {
  command -v "$1" >/dev/null 2>&1
}

prepend_common_bin_dirs() {
  for dir in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
    case ":$PATH:" in
      *":$dir:"*) ;;
      *) PATH="$dir:$PATH" ;;
    esac
  done
  export PATH
}

download_uv_installer() {
  if have curl; then
    curl -LsSf "$FOLIO_UV_INSTALL_URL" | sh
  elif have wget; then
    wget -qO- "$FOLIO_UV_INSTALL_URL" | sh
  else
    die "curl or wget is required to install uv automatically"
  fi
}

ensure_uv() {
  prepend_common_bin_dirs
  if have uv; then
    say "Found $(uv --version 2>/dev/null || printf 'uv')"
    return
  fi

  if [ "$FOLIO_BOOTSTRAP_UV" != "1" ]; then
    die "uv is required. Install it first from https://docs.astral.sh/uv/getting-started/installation/ or rerun with FOLIO_BOOTSTRAP_UV=1 after inspecting this script."
  fi

  say "Installing uv..."
  download_uv_installer
  prepend_common_bin_dirs

  if ! have uv; then
    die "uv was installed, but it is not available on PATH. Restart your shell or run: uv tool update-shell"
  fi
}

folio_install_spec() {
  if [ -n "$FOLIO_INSTALL_SPEC" ]; then
    printf '%s\n' "$FOLIO_INSTALL_SPEC"
  elif [ -n "$FOLIO_VERSION" ]; then
    printf '%s==%s\n' "$FOLIO_PACKAGE" "$FOLIO_VERSION"
  else
    printf '%s\n' "$FOLIO_PACKAGE"
  fi
}

node_is_supported() {
  if ! have node; then
    warn "Node.js 20.19+ is required for folio build and serve"
    return 1
  fi

  node_version=$(node -v 2>/dev/null | sed 's/^v//')
  major=$(printf '%s' "$node_version" | cut -d. -f1)
  minor=$(printf '%s' "$node_version" | cut -d. -f2)

  case "$major" in
    ''|*[!0-9]*)
      warn "Could not parse Node.js version: $node_version"
      return 1
      ;;
  esac
  case "$minor" in
    ''|*[!0-9]*) minor=0 ;;
  esac

  if [ "$major" -lt 20 ] || { [ "$major" -eq 20 ] && [ "$minor" -lt 19 ]; }; then
    warn "Node.js $node_version found, but Folio expects Node.js 20.19+"
    return 1
  fi

  return 0
}

pnpm_major_version() {
  pnpm_version=$(pnpm --version 2>/dev/null || true)
  major=$(printf '%s' "$pnpm_version" | cut -d. -f1)
  case "$major" in
    ''|*[!0-9]*) return 1 ;;
  esac
  printf '%s\n' "$major"
}

pnpm_is_supported() {
  major=$(pnpm_major_version) || return 1
  [ "$major" -ge 10 ]
}

ensure_pnpm() {
  if [ "$FOLIO_SKIP_PNPM_SETUP" = "1" ]; then
    warn "Skipping pnpm setup because FOLIO_SKIP_PNPM_SETUP=1 was set"
    return
  fi

  node_is_supported || {
    warn "Install Node.js 20.19+ and pnpm 10 before running folio build or serve"
    return
  }

  if have pnpm && pnpm_is_supported; then
    say "Found pnpm $(pnpm --version 2>/dev/null || true)"
    return
  fi

  if have pnpm; then
    warn "Found pnpm $(pnpm --version 2>/dev/null || true), but Folio expects pnpm 10"
  fi

  if have corepack; then
    say "Installing pnpm with Corepack..."
    corepack enable >/dev/null 2>&1 || warn "corepack enable failed"
    corepack prepare pnpm@10 --activate || warn "corepack could not activate pnpm"
  fi

  if have pnpm && pnpm_is_supported; then
    say "Found pnpm $(pnpm --version 2>/dev/null || true)"
  else
    warn "pnpm 10 was not found. Install it with: corepack prepare pnpm@10 --activate"
  fi
}

print_dependency_summary() {
  say "Dependencies:"
  say "  - uv: required; install from https://docs.astral.sh/uv/getting-started/installation/"
  say "  - Python 3.10+: used by Folio through uv"
  say "  - Node.js 20.19+: required for build/serve; checked by this script"
  say "  - pnpm 10: activated with Corepack when possible"
}

main() {
  print_dependency_summary
  ensure_uv

  install_spec=$(folio_install_spec)
  say "Installing Folio with uv: $install_spec"
  uv tool install --force "$install_spec"
  prepend_common_bin_dirs

  ensure_pnpm

  if have folio; then
    say "Installed $(folio --version 2>/dev/null || printf 'folio')"
  else
    warn "Folio installed, but the folio command is not on PATH yet. Restart your shell or run: uv tool update-shell"
  fi

  say "Next: folio init && folio serve"
}

main "$@"
