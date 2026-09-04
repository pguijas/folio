# MethodAccordion

Expandable accordion panels for documenting class methods. Each method shows its name and signature in the header, with the full description revealed on click. Async methods display an "async" badge. This component is typically auto-generated for classes with public methods.

## API

### MethodAccordion

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `methods` | `Method[]` | — | Array of method objects. |

### Method object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `string` | — | Method name. |
| `signature` | `string` | — | Parameter signature (e.g. `(self, x: int) -> bool`). |
| `description` | `string` | — | Description of what the method does. |
| `isAsync` | `boolean` | `false` | If true, displays an "async" badge next to the name. |
| `children` | `ReactNode` | — | Additional content (parameter tables, examples, etc.) rendered inside the accordion. |

## Example

<PreviewCode>

```mdx
<MethodAccordion methods={[
  {
    name: "connect",
    signature: "(self, address: str, timeout: float = 30.0) -> None",
    description: "Establish a connection to a remote node.",
    isAsync: true
  },
  {
    name: "disconnect",
    signature: "(self) -> None",
    description: "Close the current connection and release resources."
  },
  {
    name: "send",
    signature: "(self, data: bytes, compress: bool = True) -> int",
    description: "Send data to the connected node. Returns bytes sent.",
    isAsync: true
  }
]} />
```

<MethodAccordion methods={[
  {
    name: "connect",
    signature: "(self, address: str, timeout: float = 30.0) -> None",
    description: "Establish a connection to a remote node.",
    isAsync: true
  },
  {
    name: "disconnect",
    signature: "(self) -> None",
    description: "Close the current connection and release resources."
  },
  {
    name: "send",
    signature: "(self, data: bytes, compress: bool = True) -> int",
    description: "Send data to the connected node. Returns bytes sent.",
    isAsync: true
  }
]} />

</PreviewCode>
