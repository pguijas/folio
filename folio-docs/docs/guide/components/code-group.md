# CodeGroup

Tabbed code blocks for showing the same concept in multiple languages or multiple variants of a command. Tabs are automatically labeled from the language of each code block, or you can provide explicit labels.

## API

### CodeGroup

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `labels` | `string[]` | — | Optional explicit tab labels. If omitted, labels are auto-detected from each code block's language (e.g. `python`, `bash`). |
| `children` | `ReactNode` | — | Two or more fenced code blocks to display as tabs. |

Label auto-detection tries, in order: a `title` prop, a `data-language` attribute, a `language-*` CSS class, and falls back to `Tab N`.

## Example

Auto-detected labels from language:

<PreviewCode>

````mdx
<CodeGroup>
```python
import my_lib
client = my_lib.Client()
```

```javascript
import { Client } from "my-lib";
const client = new Client();
```
</CodeGroup>
````

<CodeGroup>
```python
import my_lib
client = my_lib.Client()
```

```javascript
import { Client } from "my-lib";
const client = new Client();
```
</CodeGroup>

</PreviewCode>

With explicit labels:

<PreviewCode>

````mdx
<CodeGroup labels={["pip", "uv", "conda"]}>
```bash
pip install my-lib
```

```bash
uv add my-lib
```

```bash
conda install my-lib
```
</CodeGroup>
````

<CodeGroup labels={["pip", "uv", "conda"]}>
```bash
pip install my-lib
```

```bash
uv add my-lib
```

```bash
conda install my-lib
```
</CodeGroup>

</PreviewCode>
