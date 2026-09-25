# Plugin Catalog

*Every integration in the Folio binary, in one place.*

Every integration below is **built in**: compiled into `folio`, present in
every build, and inert until its section appears in `docs.yaml`. Add the
section and the integration builds its pages. Remove it and the integration
goes inert again. A clean build clears any route it had already written.

## Built-in integrations

- **[Roadmap](/docs/plugins/roadmap)**: Product phases from docs.yaml rendered as a release timeline, with an optional standalone /roadmap page and a CLI table. Activated by the roadmap: key.

- **[Landing Page](/docs/plugins/landing)**: A public homepage in front of your docs: hero variants, CTAs, install commands, and a section catalog. Activated by the landing: key.

- **[OpenAPI](/docs/plugins/openapi)**: Point openapi.sources at a spec file and get an endpoint index page (method, path, summary, operationId, tags) wired into the sidebar and search. Activated by the openapi: key.

## Activation

```yaml
# docs.yaml — each section is its integration's switch
roadmap:
  phases: [...]
landing:
  hero: {...}
openapi:
  sources: [...]
```

## Static files

Files the site serves from its root without a plugin, such as an installer
script, go under the `public:` key in `docs.yaml`. Folio's own site serves
`install.sh` that way. See [public](/docs/configuration#public).

## Project plugins

Not available in this release. Plugins loaded from your own repository return
with the sidecar protocol; the hooks they will implement are documented in
[Writing Plugins](/docs/plugins/authoring), and the built-ins above are their reference
implementations.
