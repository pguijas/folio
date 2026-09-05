# ClassOverview

A card displaying a Python class with its name, base classes, decorators, and description. This component is typically auto-generated from source code during the build, but you can also use it manually to create hand-crafted class documentation.

## API

### ClassOverview

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `string` | — | The class name. |
| `bases` | `(string \| { name: string, href?: string })[]` | `[]` | List of base classes. Each entry can be a plain string or an object with `name` and optional `href` for linking to the base class docs. |
| `decorators` | `string[]` | `[]` | List of decorator names (displayed with `@` prefix). |
| `description` | `string` | — | A short description of the class. |

## Example

Basic usage with string base classes:

```mdx
<ClassOverview
  name="FederatedLearner"
  bases={["BaseNode", "Serializable"]}
  decorators={["dataclass"]}
  description="A node that participates in federated learning rounds."
/>
```

With linked base classes:

```mdx
<ClassOverview
  name="FederatedLearner"
  bases={[
    { name: "BaseNode", href: "/docs/api-reference/base-node" },
    { name: "Serializable", href: "/docs/api-reference/serializable" }
  ]}
  decorators={["dataclass", "deprecated"]}
  description="A node that participates in federated learning rounds."
/>
```
