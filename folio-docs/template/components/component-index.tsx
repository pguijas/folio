import type { CSSProperties } from "react"

type ComponentEntry = {
  title: string
  description: string
  href: string
  role: string
}

type ComponentGroup = {
  title: string
  summary: string
  accent: string
  entries: ComponentEntry[]
}

const componentGroups: ComponentGroup[] = [
  {
    title: "Workflow Components",
    summary:
      "Build setup guides, CLI references, migration notes, and plugin docs that stay easy to scan.",
    accent: "oklch(0.58 0.075 150)",
    entries: [
      {
        title: "TerminalSession",
        description:
          "Command and output blocks with prompt, status, and working directory context.",
        href: "/docs/components/terminal-session",
        role: "Commands",
      },
      {
        title: "ConfigPanel",
        description:
          "Annotated configuration snippets for docs.yaml examples.",
        href: "/docs/components/config-panel",
        role: "Config",
      },
      {
        title: "BuildArtifact",
        description:
          "Compact summaries of generated files, folders, and routes.",
        href: "/docs/components/build-artifact",
        role: "Output",
      },
      {
        title: "CommandGrid",
        description: "Scannable CLI command cards with common flags.",
        href: "/docs/components/command-grid",
        role: "CLI",
      },
      {
        title: "BeforeAfter",
        description:
          "Side-by-side migration, config, and output comparisons.",
        href: "/docs/components/before-after",
        role: "Compare",
      },
      {
        title: "Checklist",
        description:
          "Readiness and deployment checklists with explicit states.",
        href: "/docs/components/checklist",
        role: "State",
      },
      {
        title: "HookMap",
        description:
          "Plugin lifecycle stages with hook names and descriptions.",
        href: "/docs/components/hook-map",
        role: "Plugins",
      },
    ],
  },
  {
    title: "Interactive Components",
    summary:
      "Add controlled disclosure, alternate examples, and sequence structure without custom page logic.",
    accent: "oklch(0.56 0.078 248)",
    entries: [
      {
        title: "Accordion",
        description:
          "Collapsible content sections for FAQs and grouped information.",
        href: "/docs/components/accordion",
        role: "Reveal",
      },
      {
        title: "Tabs",
        description: "Tabbed panels for organizing alternative content views.",
        href: "/docs/components/tabs",
        role: "Views",
      },
      {
        title: "Steps",
        description:
          "Numbered step-by-step instructions with a vertical timeline.",
        href: "/docs/components/steps",
        role: "Sequence",
      },
      {
        title: "Timeline",
        description: "Vertical timeline for changelogs and version history.",
        href: "/docs/components/timeline",
        role: "History",
      },
      {
        title: "CodeGroup",
        description:
          "Tabbed code blocks for multi-language or multi-variant examples.",
        href: "/docs/components/code-group",
        role: "Code",
      },
      {
        title: "PreviewCode",
        description:
          "Paired rendered previews and source snippets for component examples.",
        href: "/docs/components/preview-code",
        role: "Examples",
      },
      {
        title: "ExampleTabs",
        description:
          "Tabbed code panels for basic vs. advanced usage patterns.",
        href: "/docs/components/example-tabs",
        role: "Examples",
      },
    ],
  },
  {
    title: "Display Components",
    summary:
      "Present diagrams, file structures, notes, feature summaries, and rendered technical notation.",
    accent: "oklch(0.61 0.09 42)",
    entries: [
      {
        title: "Callout",
        description:
          "Highlighted message blocks for notes, warnings, tips, and alerts.",
        href: "/docs/components/callout",
        role: "Message",
      },
      {
        title: "FeatureCards",
        description:
          "Cards for feature overviews, landing pages, and link grids.",
        href: "/docs/components/feature-cards",
        role: "Summary",
      },
      {
        title: "FileTree",
        description: "Visual file and folder tree for project structures.",
        href: "/docs/components/file-tree",
        role: "Files",
      },
      {
        title: "DocPreview",
        description:
          "Responsive iframe frames for showing generated docs pages inside a guide.",
        href: "/docs/components/doc-preview",
        role: "Preview",
      },
      {
        title: "BrowserFrame",
        description:
          "Browser window chrome with a mono URL bar for framing embedded examples.",
        href: "/docs/components/browser-frame",
        role: "Frame",
      },
      {
        title: "Mermaid",
        description: "Diagrams rendered as SVG for flows and sequences.",
        href: "/docs/components/mermaid",
        role: "Diagram",
      },
      {
        title: "Math",
        description: "LaTeX math rendering with KaTeX.",
        href: "/docs/components/math",
        role: "Formula",
      },
      {
        title: "Code Blocks",
        description:
          "Syntax highlighting, line numbers, filenames, and word highlighting.",
        href: "/docs/components/code-blocks",
        role: "Code",
      },
    ],
  },
  {
    title: "API Reference Components",
    summary:
      "These appear automatically when Folio turns Python source into reference pages.",
    accent: "oklch(0.52 0.07 305)",
    entries: [
      {
        title: "ClassOverview",
        description:
          "Card displaying a Python class with bases, decorators, and description.",
        href: "/docs/components/class-overview",
        role: "Class",
      },
      {
        title: "MethodAccordion",
        description:
          "Expandable panels for documenting class methods and signatures.",
        href: "/docs/components/method-accordion",
        role: "Method",
      },
      {
        title: "ParamTable",
        description: "Structured table for function or method parameters.",
        href: "/docs/components/param-table",
        role: "Params",
      },
      {
        title: "TypeBadge",
        description:
          "Inline badge for displaying type annotations with optional links.",
        href: "/docs/components/type-badge",
        role: "Types",
      },
      {
        title: "DeprecationNotice",
        description:
          "Banner indicating deprecated classes, functions, or modules.",
        href: "/docs/components/deprecation-notice",
        role: "Lifecycle",
      },
    ],
  },
  {
    title: "Theme Components",
    summary:
      "Small pieces of site chrome used by the generated Nextra theme.",
    accent: "oklch(0.49 0.035 82)",
    entries: [
      {
        title: "ThemeConfigurator",
        description:
          "Popover widget for customizing accent color and border radius.",
        href: "/docs/components/theme-configurator",
        role: "Theme",
      },
      {
        title: "Page Actions",
        description:
          "Header controls for copying a page or opening it with AI context.",
        href: "/docs/components/copy-page-button",
        role: "Actions",
      },
      {
        title: "PageFeedback",
        description:
          "Was this page helpful? widget with thumbs up/down.",
        href: "/docs/components/page-feedback",
        role: "Feedback",
      },
    ],
  },
]

const fastPaths = [
  {
    task: "Write a setup guide",
    components: ["TerminalSession", "Steps", "Checklist"],
  },
  {
    task: "Explain generated output",
    components: ["FileTree", "BuildArtifact", "ConfigPanel"],
  },
  {
    task: "Document Python APIs",
    components: ["ClassOverview", "ParamTable", "TypeBadge"],
  },
]

const componentCount = componentGroups.reduce(
  (total, group) => total + group.entries.length,
  0
)

function groupStyle(accent: string) {
  return { "--folio-component-group-accent": accent } as CSSProperties
}

export function ComponentIndex() {
  return (
    <div className="component-index">
      <section className="component-index-hero" aria-labelledby="component-index-title">
        <div className="component-index-hero-copy">
          <p className="component-index-kicker">Component catalog</p>
          <h2 id="component-index-title">
            Pick the right primitive before writing another docs section.
          </h2>
          <p>
            Folio ships {componentCount} documentation components across{" "}
            {componentGroups.length} families. Use this page as a routing layer:
            find the job, open the component, then copy the pattern into a real
            guide or generated API page.
          </p>
        </div>
        <div className="component-index-panel" aria-label="Catalog summary">
          <span>{componentCount} entries</span>
          <span>{componentGroups.length} families</span>
          <span>MDX ready</span>
        </div>
      </section>

      <section className="component-index-fast-paths" aria-labelledby="fast-path-title">
        <div>
          <p className="component-index-kicker">Fast paths</p>
          <h3 id="fast-path-title">Start from the shape of the page.</h3>
        </div>
        <div className="component-index-path-list">
          {fastPaths.map((path) => (
            <div className="component-index-path" key={path.task}>
              <span>{path.task}</span>
              <p>{path.components.join(" + ")}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="component-index-groups">
        {componentGroups.map((group) => (
          <section
            className="component-index-group"
            key={group.title}
            style={groupStyle(group.accent)}
            aria-labelledby={`${group.title.replaceAll(" ", "-")}-title`}
          >
            <div className="component-index-group-heading">
              <span className="component-index-swatch" aria-hidden="true" />
              <h3 id={`${group.title.replaceAll(" ", "-")}-title`}>
                {group.title}
              </h3>
              <p>{group.summary}</p>
            </div>
            <div className="component-index-links">
              {group.entries.map((entry) => (
                <a className="component-index-link" href={entry.href} key={entry.href}>
                  <span className="component-index-link-meta">{entry.role}</span>
                  <strong>{entry.title}</strong>
                  <span>{entry.description}</span>
                  <em>Open</em>
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
