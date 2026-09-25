# CommandGrid

A compact command overview for CLI-heavy pages. Use `CommandGrid` with one or more `CommandCard` children.

## API

### CommandGrid

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | `CommandCard` elements. |

### CommandCard

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `command` | `string` | — | CLI command shown in monospace. |
| `title` | `string` | — | Human-readable command name. |
| `description` | `string` | — | Short task description. |
| `href` | `string` | — | Optional link target. |
| `flags` | `string[]` | `[]` | Common flags shown as badges. |

## Example

<PreviewCode>

```mdx
<CommandGrid>
  <CommandCard command="folio init" title="Initialize" description="Create docs.yaml." />
  <CommandCard command="folio build" title="Build" description="Generate the static site." flags={["--clean", "--verbose"]} />
</CommandGrid>
```

<CommandGrid>
  <CommandCard command="folio init" title="Initialize" description="Create docs.yaml from project metadata." />
  <CommandCard command="folio build" title="Build" description="Generate MDX, search, and static output." flags={["--clean", "--verbose"]} />
</CommandGrid>

</PreviewCode>
