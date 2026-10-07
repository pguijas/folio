# Steps

Numbered step-by-step instructions with a vertical timeline. Steps are numbered automatically using CSS counters — you do not provide numbers manually. Use Steps for tutorials, setup guides, and any sequential process.

## API

### Steps

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | One or more `<Step>` elements. |

### Step

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | The step heading. |
| `children` | `ReactNode` | — | The step content (text, code, components, etc.). |

## Example

```mdx
<Steps>
  <Step title="Install the package">
    Run `uv add my-lib` or `pip install my-lib` to install.
  </Step>

  <Step title="Create a config file">
    Run `my-lib init` to generate a default configuration.
  </Step>

  <Step title="Start the server">
    Run `my-lib serve` to start the development server on port 3000.
  </Step>
</Steps>
```

### Install the package

    Run `uv add my-lib` to install.

### Create a config file

    Run `my-lib init` to generate a default configuration.

### Start the server

    Run `my-lib serve` to start the development server.
