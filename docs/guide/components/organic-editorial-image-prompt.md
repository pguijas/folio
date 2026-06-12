# OrganicEditorialImagePrompt

Displays the default Organic Editorial prompt for an image-generation model. Use it when a launch page, training program, or editorial guide needs the cobalt abstract image language without committing a bitmap asset to the template.

### OrganicEditorialImagePrompt

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | `"Organic Editorial image prompt"` | Heading shown above the prompt. |
| `prompt` | `string` | Built-in Organic Editorial prompt | Prompt text to copy into an image model. |
| `model` | `string` | `"Image model"` | Label for the intended generation target. |
| `ratio` | `string` | `"16:9"` | Intended image aspect ratio. |
| `className` | `string` | — | Optional wrapper class names. |

## Example

<PreviewCode>

```mdx
<OrganicEditorialImagePrompt />
```

<OrganicEditorialImagePrompt />

</PreviewCode>

## Custom Prompt

<PreviewCode>

```mdx
<OrganicEditorialImagePrompt
  title="Launch page opener prompt"
  model="Image model"
  ratio="4:3"
  prompt="Create an abstract editorial image for an open source documentation launch page. Use cobalt blue organic forms on a warm white photographic field, subtle analog grain, generous negative space, no typography, no logos, no UI, no people. The result should feel calm, technical, and premium."
/>
```

<OrganicEditorialImagePrompt
  title="Launch page opener prompt"
  model="Image model"
  ratio="4:3"
  prompt="Create an abstract editorial image for an open source documentation launch page. Use cobalt blue organic forms on a warm white photographic field, subtle analog grain, generous negative space, no typography, no logos, no UI, no people. The result should feel calm, technical, and premium."
/>

</PreviewCode>
