# Timeline

Vertical timeline for changelogs, version history, or sequential events. Each item shows a date, title, optional badge, and description. Badges like `"new"` and `"breaking"` have special styling.

## API

### Timeline

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | One or more `<TimelineItem>` elements. |

### TimelineItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `date` | `string` | — | Date or version label. |
| `title` | `string` | — | Event or release title. |
| `badge` | `string` | — | Optional badge text. `"new"` and `"breaking"` have special styling; any other string displays as a neutral badge. |
| `children` | `ReactNode` | — | Description or details. |

## Example

<PreviewCode>

````mdx
<Timeline>
  <TimelineItem date="v2.0.0" title="Major release" badge="breaking">
    Dropped Python 3.8 support. Migrated to Pydantic v2. New plugin API.
  </TimelineItem>
  <TimelineItem date="v1.5.0" title="Mermaid diagrams" badge="new">
    Added Mermaid diagram rendering support.
  </TimelineItem>
  <TimelineItem date="v1.4.2" title="Bug fixes">
    Fixed sidebar ordering and improved build performance.
  </TimelineItem>
</Timeline>
````

<Timeline>
  <TimelineItem date="v2.0.0" title="Major release" badge="breaking">
    Dropped Python 3.8 support. Migrated to Pydantic v2. New plugin API.
  </TimelineItem>
  <TimelineItem date="v1.5.0" title="Mermaid diagrams" badge="new">
    Added support for Mermaid diagram rendering in documentation pages.
  </TimelineItem>
  <TimelineItem date="v1.4.2" title="Bug fixes">
    Fixed sidebar ordering issue with nested modules. Improved build performance.
  </TimelineItem>
  <TimelineItem date="v1.4.0" title="Search customization" badge="new">
    Added configurable search placeholder and the ability to disable search.
  </TimelineItem>
</Timeline>

</PreviewCode>
