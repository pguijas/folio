# PullQuote

A high-emphasis statement block for the one sentence the page exists to deliver — verdicts, theses, the line you want quoted back.

## API

### PullQuote

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | — | The statement. |
| `kicker` | `string` | — | Small uppercase label above it. |
| `attribution` | `string` | — | Source line below it. |

## Example

**Verdict**

```mdx
<PullQuote kicker="The short version">
  Nobody remembers the third-best espresso in the district.
</PullQuote>
```

**The short version**

  Nobody remembers the third-best espresso in the district.
