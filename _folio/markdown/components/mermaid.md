# Mermaid

Renders [Mermaid](https://mermaid.js.org/) diagrams as SVG directly in the browser. Supports flowcharts, sequence diagrams, class diagrams, state diagrams, ER diagrams, Gantt charts, and all other Mermaid diagram types. Automatically switches between light and dark themes to match the site.

## API

### Mermaid (JSX component)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `chart` | `string` | — | The Mermaid diagram definition string. |

### Fenced code block (recommended)

You can also use standard Mermaid fenced code blocks. Folio automatically converts these into `<Mermaid>` components during the build:

````md
```mermaid
graph TD
    A --> B
```
````

## Example

### Fenced code block syntax

````md
```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[OK]
    B -->|No| D[Cancel]
```
````

```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[OK]
    B -->|No| D[Cancel]
```

### JSX component syntax

```mdx
<Mermaid chart="graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[OK]
    B -->|No| D[Cancel]" />
```

### Sequence diagram

````md
```mermaid
sequenceDiagram
    Client->>Server: POST /train
    Server->>Worker: dispatch(job)
    Worker-->>Server: result
    Server-->>Client: 200 OK
```
````

```mermaid
sequenceDiagram
    Client->>Server: POST /train
    Server->>Worker: dispatch(job)
    Worker-->>Server: result
    Server-->>Client: 200 OK
```

### Class diagram

````md
```mermaid
classDiagram
    class Node {
        +str address
        +connect()
        +disconnect()
    }
    class FederatedNode {
        +train()
        +aggregate()
    }
    Node <|-- FederatedNode
```
````

```mermaid
classDiagram
    class Node {
        +str address
        +connect()
        +disconnect()
    }
    class FederatedNode {
        +train()
        +aggregate()
    }
    Node <|-- FederatedNode
```
