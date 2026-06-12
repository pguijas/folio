# TerminalSession

Render a command with prompt context, optional output, and a compact status marker. Most guide command snippets should use plain fenced `bash` blocks. Reserve `TerminalSession` for cases where prompt context, exact output, or status state matters to the reader.

Avoid invented success logs in guide pages. Use `output` only for exact text the reader should recognize, such as a version check, error message, or URL printed by a command. For setup commands, omit output so the command stays easy to copy.

The header copy button copies only the `command` value, not the prompt, output, or notes.

## API

| Prop       | Type                                | Default      | Description                                         |
| ---------- | ----------------------------------- | ------------ | --------------------------------------------------- |
| `command`  | `string`                            | —            | Command shown after the prompt.                     |
| `output`   | `string \| string[]`                | —            | Terminal output shown below the command.            |
| `cwd`      | `string`                            | —            | Optional working directory label.                   |
| `title`    | `string`                            | `"Terminal"` | Header label.                                       |
| `prompt`   | `string`                            | `"$"`        | Prompt marker before the command.                   |
| `status`   | `"neutral" \| "success" \| "error"` | `"neutral"`  | Header status color.                                |
| `children` | `ReactNode`                         | —            | Optional explanatory note below the terminal block. |

## Example

<PreviewCode>

```mdx
<TerminalSession
  title="Check version"
  command="folio --version"
  status="success"
  output="folio 0.2.1"
/>
```

<TerminalSession
  title="Check version"
  command="folio --version"
  status="success"
  output="folio 0.2.1"
/>

</PreviewCode>
