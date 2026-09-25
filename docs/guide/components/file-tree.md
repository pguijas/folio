# FileTree

A visual file and folder tree for showing project structures, directory layouts, and file hierarchies. Parses an indented text string into a tree with folder/file icons, connectors, and proper nesting.

## API

### FileTree

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `tree` | `string` | — | An indented text string representing the file tree. Lines ending with `/` are rendered as folders; all others are rendered as files. Nesting is determined by indentation (spaces). |

Formatting rules:
- Lines ending with `/` are rendered as **folders** (accent-colored icon)
- All other lines are rendered as **files** (muted icon)
- Nesting is determined by indentation level
- Multiple root entries are supported at the top level

## Example

<PreviewCode>

```mdx
<FileTree tree={`
my-project/
  pyproject.toml
  README.md
  docs/
    index.md
    guide/
      installation.md
      quickstart.md
  src/
    my_lib/
      __init__.py
      core.py
      utils.py
  tests/
    test_core.py
    test_utils.py
`} />
```

<FileTree tree={`
my-project/
  pyproject.toml
  README.md
  src/
    my_lib/
      __init__.py
      core.py
  tests/
    test_core.py
  docs/
    index.md
    guide/
      installation.md
`} />

</PreviewCode>
