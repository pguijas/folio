# Accordion

Collapsible content sections for organizing information into expandable panels. Use Accordion for FAQs, grouped content, or any situation where you want to reduce page clutter while keeping information accessible. Unlike [MethodAccordion](/docs/components/method-accordion), which is structured for API methods, Accordion supports any content.

## API

### Accordion

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | One or more `<AccordionItem>` elements. |

### AccordionItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | — | The heading shown in the collapsed state. |
| `defaultOpen` | `boolean` | `false` | Whether the item starts expanded. |
| `children` | `ReactNode` | — | Content revealed when expanded. |

## Example

````mdx
<Accordion>
  <AccordionItem title="What is Folioh?">
    Folioh is a documentation engine with a native Rust core that
    uses Nextra and shadcn/ui to produce structured,
    interactive documentation sites.
  </AccordionItem>
  <AccordionItem title="How does it compare to Sphinx?">
    Folioh generates a modern React-based site with live
    search, dark mode, and responsive design out of the box.
  </AccordionItem>
  <AccordionItem title="Can I migrate from Sphinx?" defaultOpen>
    Yes. Folioh includes a migration guide for moving existing
    pages and Sphinx conventions to Markdown.
  </AccordionItem>
</Accordion>
````

### What is Folioh?

    Folioh is a documentation engine with a native Rust core that uses Nextra and shadcn/ui to produce structured, interactive documentation sites.

### How does it compare to Sphinx?

    Folioh generates a modern React-based site with live search, dark mode, and responsive design out of the box. It parses the same Google/NumPy docstrings as Sphinx.

### Can I migrate from Sphinx?

    Yes. Folioh includes a migration guide for moving existing pages and Sphinx conventions to Markdown.

## Markdown details

For a single section, a plain `<details>` element with a `<summary>` collapses too, with no import.

````mdx
<details>
  <summary>Do I need to import anything?</summary>

  No. `<details>` and `<summary>` are HTML elements, and Folioh
  renders them as a collapsible section.
</details>
````

<details>
  <summary>Do I need to import anything?</summary>

  No. `<details>` and `<summary>` are HTML elements, and Folioh renders them as a collapsible section.
</details>
