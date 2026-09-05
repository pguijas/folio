# ConfigPanel

Pair a YAML example with short field notes. Use it when a configuration snippet needs explanation but a full reference table would interrupt the guide.

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | Section title. |
| `description` | `string` | — | Short explanation below the title. |
| `fields` | `ConfigField[]` | `[]` | Field notes shown below the example. |
| `children` | `ReactNode` | — | Usually a fenced YAML block. |

`ConfigField` supports `name`, `type`, `default`, and `description`.

## Example

````mdx
<ConfigPanel
  title="source.python"
  description="Tell Folio where your package code lives."
  fields={[
    { name: "paths", type: "list[string]", description: "Python source directories to scan." },
    { name: "docstring_style", type: "string", default: "auto", description: "Parser for Google or NumPy style docstrings." },
  ]}
>
```yaml
source:
  python:
    paths:
      - "src/mymath"
```
</ConfigPanel>
````

```yaml
source:
  python:
    paths:
      - "src/mymath"
    docstring_style: "google"
```
