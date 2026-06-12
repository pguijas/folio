---
title: Theming
description: Customize Folio documentation colors, typography, dark mode, layout, and theme presets to match your project brand.
---

# Theming

*Customize colors, fonts, and layout to match your project's brand.*

## Dark mode

Dark mode is enabled by default. The site uses `next-themes` with the ThemeProvider
component, which supports three modes:

- **System** (default) -- follows the user's OS preference
- **Light** -- always light
- **Dark** -- always dark

Users can toggle between light and dark mode by pressing the **D** key on their
keyboard. This hotkey works anywhere on the page except when the focus is on an input
field, textarea, or content-editable element.

To disable dark mode in your project, set `dark_mode: false` in your `docs.yaml`:

```yaml
theme:
  dark_mode: false
```

## Theme configurator

Every generated site includes a built-in theme configurator accessible from the paint
board icon in the navigation bar. It opens a preset drawer with a grouped preset
library (Organic Editorial is the default, alongside presets such as Workshop,
Canopy, Beacon, Aperture, Ledger, and Atlas) plus fine-grained controls for surface
color, shell spacing, reading rhythm, borders, code blocks, typography, accent color,
and corner radius.

Preferences are saved to `localStorage` under the key `folio-theme`, so choices
persist across page reloads and sessions. See the
[Theme Configurator component page](./components/theme-configurator) for the full
preset catalog and each control's options.

## How CSS variables work

The theme system uses **oklch** colors defined as CSS custom properties. oklch is a
perceptual color space that produces more uniform and vibrant colors than HSL. Each
color variable uses the format:

```css
--primary: oklch(0.51 0.14 170);
```

The three values are:
- **Lightness** (0-1) -- how bright or dark the color is
- **Chroma** (0-0.4) -- how saturated/vivid the color is
- **Hue** (0-360) -- the color angle on the color wheel

Both light and dark modes define their own set of variables. Here are the key color
variables and their roles:

```css
:root {
  /* Page background and text */
  --background: oklch(0.995 0 0);
  --foreground: oklch(0.145 0.005 285);

  /* Primary accent (links, active states) */
  --primary: oklch(0.51 0.14 170);
  --primary-foreground: oklch(0.99 0 0);

  /* Muted/secondary backgrounds */
  --muted: oklch(0.96 0.003 264);
  --muted-foreground: oklch(0.50 0.015 264);

  /* Cards and popovers */
  --card: oklch(0.995 0 0);
  --card-foreground: oklch(0.145 0.005 285);

  /* Borders and inputs */
  --border: oklch(0.91 0.004 264);
  --input: oklch(0.91 0.004 264);

  /* Focus rings */
  --ring: oklch(0.51 0.14 170);

  /* Global border radius */
  --radius: 0.5rem;
}
```

The dark mode overrides these same variables with darker values:

```css
.dark {
  --background: oklch(0.14 0.004 285);
  --foreground: oklch(0.92 0.004 264);
  --primary: oklch(0.72 0.17 170);
  --border: oklch(1 0 0 / 8%);
  /* ... */
}
```

## Customizing colors

To permanently change the site's color scheme, edit the template `globals.css` in
this project or ship a plugin/component that owns the custom UI. The easiest approach
is to change the `--primary` and `--ring` variables, since they control the dominant
accent color.

For example, to use a deep blue accent:

```css
:root {
  --primary: oklch(0.49 0.15 255);
  --ring: oklch(0.49 0.15 255);
  --sidebar-primary: oklch(0.49 0.15 255);
  --sidebar-ring: oklch(0.49 0.15 255);
}

.dark {
  --primary: oklch(0.65 0.18 255);
  --ring: oklch(0.65 0.18 255);
  --sidebar-primary: oklch(0.65 0.18 255);
  --sidebar-ring: oklch(0.65 0.18 255);
}
```

Sidebar-specific variables control the left navigation panel independently from the
main content area:

| Variable | Purpose |
|----------|---------|
| `--sidebar` | Sidebar background |
| `--sidebar-foreground` | Sidebar text color |
| `--sidebar-primary` | Sidebar active item color |
| `--sidebar-accent` | Sidebar hover/focus background |
| `--sidebar-border` | Sidebar border color |

## Custom fonts

The default site uses **Sora** for body text and **JetBrains Mono** for code blocks,
loaded via `next/font/google` for optimal performance (self-hosted, no external
requests).

To change fonts, modify the font imports in `layout.tsx` using any font from
Google Fonts:

```tsx
import { Fira_Sans, Fira_Code } from "next/font/google"

const firaSans = Fira_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
})

const firaCode = Fira_Code({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
})
```

The CSS variable names matter: `--font-sans` controls body text and `--font-mono`
controls code blocks. These are referenced in `globals.css`:

```css
body {
  font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif;
}
code, kbd, pre {
  font-family: var(--font-mono), ui-monospace, SFMono-Regular, monospace;
}
```

## The shadcn component system

folio uses [shadcn/ui](https://ui.shadcn.com) for its component library. These
are not installed as a dependency -- they are copied directly into the template as
source code under `components/ui/`. This means you can freely modify them.

Key components used in the generated site:

| Component | Usage |
|-----------|-------|
| `Popover` | Theme configurator dropdown |
| `Sidebar` | Navigation sidebar |
| `Collapsible` | Expandable sections |
| `Badge` | Method kind labels (property, static, etc.) |

Since shadcn components are source files in the bundled template, project-level
changes should happen in the template or through named components until override
emission is implemented.

## Custom pages alongside API docs

folio generates API reference pages automatically from your Python source code,
but you can also add hand-written documentation pages. Place Markdown files in a
directory listed under `source.docs`:

```yaml
source:
  docs:
    - "docs/"
```

Any `.md` file in this directory becomes a page in the generated site. The
directory structure determines the URL structure:

```
docs/
  guide/
    index.md             -> /guide
    installation.md      -> /guide/installation
    configuration.md     -> /guide/configuration
  tutorials/
    getting-started.md   -> /tutorials/getting-started
```

Hand-written pages and auto-generated API pages coexist in the same site. Use the
`nav` key in `docs.yaml` to control the top-level navigation order:

```yaml
nav:
  - "Guide"
  - "Tutorials"
  - "API Reference"
```

## Project branding

### Logo

Add a logo image to your docs by specifying the path in `docs.yaml`:

```yaml
theme:
  logo: "docs/assets/logo.png"
```

The logo is displayed in the navigation bar alongside the project name. The image file
is automatically copied to the built site's `public/` directory.

### Favicon

Set a custom favicon:

```yaml
theme:
  favicon: "docs/assets/favicon.ico"
```

## Putting it together

Here is a complete `docs.yaml` with full theme customization:

```yaml
project:
  name: "My Library"
  version: "2.0.0"
  repo: "https://github.com/org/my-library"

source:
  python:
    paths:
      - "src/my_library/"
  docs:
    - "docs/"

theme:
  dark_mode: true
  logo: "docs/assets/logo.png"
  favicon: "docs/assets/favicon.ico"

nav:
  - "Guide"
  - "API Reference"
```

With project files arranged like this:

```
docs/
  assets/
    logo.png
    favicon.ico
```
