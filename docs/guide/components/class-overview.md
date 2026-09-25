# ClassOverview

A card displaying a class with its name, base classes, decorators, and description. Every Python and JavaScript class on a generated API page opens with one, and the page writes the class docstring below the card rather than in `description`. You can also use it by hand for class documentation you write yourself.

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

<PreviewCode>

```mdx
<ClassOverview
  name="FederatedLearner"
  bases={["BaseNode", "Serializable"]}
  decorators={["dataclass"]}
  description="A node that participates in federated learning rounds."
/>
```

<ClassOverview
  name="FederatedLearner"
  bases={["BaseNode", "Serializable"]}
  decorators={["dataclass"]}
  description="A node that participates in federated learning rounds."
/>

</PreviewCode>

With linked base classes:

<PreviewCode>

```mdx
<ClassOverview
  name="FederatedLearner"
  bases={[
    { name: "BaseNode", href: "/docs/api-reference" },
    "Serializable"
  ]}
  decorators={["dataclass", "deprecated"]}
  description="A node that participates in federated learning rounds."
/>
```

<ClassOverview
  name="FederatedLearner"
  bases={[
    { name: "BaseNode", href: "/docs/api-reference" },
    "Serializable"
  ]}
  decorators={["dataclass", "deprecated"]}
  description="A node that participates in federated learning rounds."
/>

</PreviewCode>
