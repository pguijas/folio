# OpenAPI

*Turn an OpenAPI spec into an endpoint index page in your docs.*

The OpenAPI integration is compiled into `folio`: nothing to install, nothing
to list. It stays inert until an `openapi:` section appears in `docs.yaml`.

```yaml
openapi:
  sources:
    - path: "specs/petstore.yaml"
      title: "Petstore"
      route: "api-reference/petstore"
```

## What it builds

For each source the integration writes one docs page, `/docs/<route>/`, with
an `OpenApiReference` block and an entry in the sidebar. The page shows the
spec's title, description and version, the number of operations and schemas,
the schema names, and one row per operation with its:

- method and path,
- summary and description,
- `operationId`,
- tags.

Operations are listed path by path, in the order the spec declares the paths,
and in `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `trace`
order within a path.

The same data is written to `lib/openapi-data.ts` as `openApiSources`, so a
page or a theme can read it too.

**Not available in this release**

  The page is an index of the endpoints, not a full reference. Parameters,
  request bodies, responses, schema fields and "try it" requests are not
  rendered.

## Sources

`openapi.sources` is a list of sources, or a single mapping for one source.
Each source takes:

| Key | Description |
|-----|-------------|
| `path` | The spec file, YAML or JSON. A relative path resolves against the project directory. The path must stay inside the project directory; one that resolves outside it stops the build. |
| `content` | The spec inline, as a mapping or as YAML/JSON text, instead of `path`. `spec` is accepted as another name for it. |
| `title` | The page title. Defaults to the spec's `info.title`, then to `OpenAPI`. |
| `description` | The text under the title. Defaults to the spec's `info.description`. |
| `route` | Where the page goes under `/docs/`. Defaults to `api-reference/<slug of the title>`. |

A configured `route` is cleaned up one segment at a time: each segment is
lowercased and slugged (`HTTP v1.2` becomes `http-v1-2`) and empty segments
are dropped; a route with no segment left (`/`) takes the default. A `.` or
`..` segment stops the build, so a route cannot climb out of the docs.

## Errors

- A `path` that does not exist, or a spec that is not valid YAML or JSON,
  stops the build with an error that names the source.
- A spec that parses to something other than a mapping is skipped with a
  warning.

## Editing a spec during `folio serve`

`folio serve` reads the specs when it starts. After you edit a spec, restart
`folio serve` to see the change.
