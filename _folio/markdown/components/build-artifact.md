# BuildArtifact

Summarize the files, directories, and generated routes produced by a Folio command.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | `"Build artifacts"` | Panel title. |
| `description` | `string` | — | Optional summary. |
| `items` | `BuildArtifactItem[]` | — | Artifact rows. |

`BuildArtifactItem` supports `path`, `kind`, and `description`.

## Example

```mdx
<BuildArtifact
  title="Generated output"
  items={[
    { path: ".build/", kind: "workspace", description: "Intermediate Nextra project." },
    { path: "_site/", kind: "static", description: "Deployable static output." },
  ]}
/>
```
