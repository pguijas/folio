import { cn } from "@/lib/utils"

type CellValue = boolean | string

interface CompareRow {
  feature: string
  values: CellValue[]
  note?: string
}

interface CompareMatrixProps {
  tools: string[]
  rows: CompareRow[]
  caption?: string
  highlight?: number
}

function Cell({ value }: { value: CellValue }) {
  if (value === true) {
    return (
      <span
        aria-label="yes"
        className="inline-flex size-5 items-center justify-center rounded-full bg-primary/15 text-primary"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="size-3"
          aria-hidden="true"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </span>
    )
  }
  if (value === false) {
    return (
      <span aria-label="no" className="text-muted-foreground/40">
        —
      </span>
    )
  }
  if (value === "~") {
    return (
      <span
        aria-label="partial"
        title="Partial"
        className="font-mono text-xs font-semibold text-warning"
      >
        ~
      </span>
    )
  }
  return <span className="text-xs text-muted-foreground">{value}</span>
}

export function CompareMatrix({
  tools,
  rows,
  caption,
  highlight = 0,
}: CompareMatrixProps) {
  return (
    <figure className="not-prose my-6 overflow-x-auto rounded-lg border border-border bg-card">
      <table className="m-0 w-full table-fixed border-collapse text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="w-[34%] px-3 py-2.5 text-left font-mono text-[10px] tracking-[0.14em] text-muted-foreground uppercase">
              {caption ?? ""}
            </th>
            {tools.map((tool, index) => (
              <th
                key={tool}
                className={cn(
                  "px-2 py-2.5 text-center text-xs font-semibold",
                  index === highlight
                    ? "bg-primary/[0.06] text-primary"
                    : "text-foreground"
                )}
              >
                {tool}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.feature}
              className="border-b border-border/60 last:border-b-0"
            >
              <td className="px-3 py-2.5 text-[13px] leading-5 text-foreground/85">
                {row.feature}
                {row.note ? (
                  <span className="block text-xs text-muted-foreground">
                    {row.note}
                  </span>
                ) : null}
              </td>
              {row.values.map((value, index) => (
                <td
                  key={`${row.feature}-${tools[index] ?? index}`}
                  className={cn(
                    "px-2 py-2.5 text-center",
                    index === highlight && "bg-primary/[0.06]"
                  )}
                >
                  <Cell value={value} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
