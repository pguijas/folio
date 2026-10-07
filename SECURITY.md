# Security Policy

## Supported Versions

Security fixes target the latest released version of Folioh.

## Reporting a Vulnerability

Please do not open a public issue for suspected vulnerabilities. Report them privately through [GitHub Security Advisories](https://github.com/pguijas/folioh/security/advisories/new), or contact the repository owner if advisories are unavailable.

Include:

- A short description of the issue.
- Steps to reproduce or a minimal proof of concept.
- Affected versions, if known.
- Any practical impact you have observed.

Maintainers will acknowledge valid reports when possible and coordinate a fix before public disclosure.

## What Folioh runs

Folioh reads your source code and never runs it: the Python, JavaScript and Rust readers parse files inside the `folioh` binary, with no interpreter, toolchain or package manager. Project plugins are not available in this release, and a `plugins:` key in `docs.yaml` warns and is ignored, so no configuration makes `folioh` load code into its own process.

The site build is different. `folioh build` and `folioh serve` install and build a Next.js frontend with pnpm and Node.js, and everything a project adds to that frontend runs as trusted code with your permissions: `components:` entries, a `theme.package`, a `template.path` or a `template.overlay_path`. A fetched theme package is pinned by a `sha256:` digest and verified before any build reads it. Treat a docs build of an untrusted branch exactly like running its test suite.

In scope, for example:

- Folioh executing or importing project source code.
- A path in `docs.yaml` (`output`, `public`, `components:`) reaching outside the project directory.
- A fetched theme package used although its tree does not match its digest.
- `folioh --update` or `install.sh` installing an archive that does not match the release's `SHA256SUMS`.
- The branch-preview workflow `folioh init` writes giving pull-request code the permissions of the deploy job.

Out of scope: frontend code you added to a build (a component, a theme package, a template) reading files, reaching the network or running commands. That is documented behavior, not a vulnerability.

Full details: [Trust & Safety](https://folioh.site/docs/plugins/trust), [Theme Packages](https://folioh.site/docs/theming/theme-packages) and [Custom Templates](https://folioh.site/docs/theming/custom-templates).
