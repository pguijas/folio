# Security Policy

## Supported Versions

Security fixes target the latest released version of Folio.

## Reporting a Vulnerability

Please do not open a public issue for suspected vulnerabilities. Report them privately through GitHub Security Advisories, or contact the repository owner if advisories are unavailable.

Include:

- A short description of the issue.
- Steps to reproduce or a minimal proof of concept.
- Affected versions, if known.
- Any practical impact you have observed.

Maintainers will acknowledge valid reports when possible and coordinate a fix before public disclosure.

## Plugins

A Folio plugin is a Python module that Folio imports and executes inside your build, in the same interpreter process as Folio itself, with your environment and filesystem. Listing a plugin is the same trust decision as installing any other dependency and importing it. Folio applies no sandbox, no permission model, and no vetting.

Two behaviors to know before reporting:

- Plugins listed under `plugins:` in a project's `docs.yaml` load when the CLI starts, so running any `folio` command from that directory (`folio --help` included) executes their module-level code.
- Entry-point plugins are opt-in. Installing a distribution that declares a `folio` entry point never activates it; only a name listed in `plugins:` is loaded.

In scope: Folio loading a plugin nobody listed, or a file-path plugin resolving outside the project directory. Out of scope: a plugin you listed reading files, reaching the network, or running arbitrary code. That is documented behavior, not a vulnerability.

Full details: https://pguijas.github.io/folio/docs/plugins/trust
