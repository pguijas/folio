# ParamTable

A structured table for displaying function or method parameters with name, type, default value, and description columns. Every Python and JavaScript function with parameters on a generated API page gets one, filled from its signature and its docstring or JSDoc; Rust functions show their signature instead. You can also use it by hand for documentation you write yourself.

## API

### ParamTable

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `args` | `Param[]` | — | Array of parameter objects. |

### Param object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `string` | — | Parameter name. |
| `type` | `string` | — | Type annotation string. |
| `default` | `string` | `"-"` | Default value. Shown as `-` if omitted. |
| `description` | `string` | — | Description of the parameter. |
| `href` | `string` | — | Optional URL to link the type badge to its documentation. |

## Example

```mdx
<ParamTable args={[
  { name: "host", type: "str", default: '"localhost"', description: "Server hostname." },
  { name: "port", type: "int", default: "8080", description: "Server port number." },
  { name: "debug", type: "bool", default: "False", description: "Enable debug mode." },
  { name: "workers", type: "int", description: "Number of worker processes. Required." }
]} />
```
