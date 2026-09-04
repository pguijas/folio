# Tabs

Generic tabbed content panels for organizing alternative content views. Unlike [CodeGroup](/docs/components/code-group) (which is code-only), Tabs supports any content including text, tables, images, and nested components.

## API

### Tabs

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | One or more `<TabItem>` elements. |

### TabItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | — | The tab label shown in the tab bar. |
| `children` | `ReactNode` | — | Content displayed when this tab is active. |

## Example

<PreviewCode>

````mdx
<Tabs>
  <TabItem label="Python">
    Install with pip: `pip install my-library`

    ```python
    import my_library
    client = my_library.Client()
    ```
  </TabItem>
  <TabItem label="Node.js">
    Install with npm: `npm install my-library`

    ```javascript
    import { Client } from "my-library";
    const client = new Client();
    ```
  </TabItem>
  <TabItem label="Go">
    Install with go get: `go get github.com/example/my-library`
  </TabItem>
</Tabs>
````

<Tabs>
  <TabItem label="Python">
    Install with pip: `pip install my-library`
  </TabItem>
  <TabItem label="Node.js">
    Install with npm: `npm install my-library`
  </TabItem>
  <TabItem label="Go">
    Install with go get: `go get github.com/example/my-library`
  </TabItem>
</Tabs>

</PreviewCode>
