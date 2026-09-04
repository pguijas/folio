type ComparisonStatus = "YES" | "PARTIAL" | "NO"

/* One configured cell: `true` yes, `false` no, `"~"` partial. */
type ComparisonValue = boolean | string

/* One configured row: a feature, one value per tool, an optional gloss. */
export type ComparisonRow = {
  feature: string
  values: ComparisonValue[]
  note?: string
}

const comparisonFrameworks = [
  { key: "folio", label: "Folio" },
  { key: "pdoc", label: "pdoc" },
  { key: "sphinx", label: "Sphinx" },
  { key: "mkdocs", label: "MkDocs" },
  { key: "mintlify", label: "Mintlify" },
  { key: "gitbook", label: "GitBook" },
] as const

type ComparisonFrameworkKey = (typeof comparisonFrameworks)[number]["key"]
type ComparisonScores = Record<ComparisonFrameworkKey, ComparisonStatus>

const comparisonFeatureRows: {
  feature: string
  scores: ComparisonScores
}[] = [
  {
    feature: "Python API",
    scores: {
      folio: "YES",
      pdoc: "YES",
      sphinx: "YES",
      mkdocs: "PARTIAL",
      mintlify: "NO",
      gitbook: "NO",
    },
  },
  {
    feature: "Guides",
    scores: {
      folio: "YES",
      pdoc: "PARTIAL",
      sphinx: "YES",
      mkdocs: "YES",
      mintlify: "YES",
      gitbook: "YES",
    },
  },
  {
    feature: "Static export",
    scores: {
      folio: "YES",
      pdoc: "YES",
      sphinx: "YES",
      mkdocs: "YES",
      mintlify: "NO",
      gitbook: "NO",
    },
  },
  {
    feature: "LLM friendly",
    scores: {
      folio: "YES",
      pdoc: "NO",
      sphinx: "NO",
      mkdocs: "NO",
      mintlify: "YES",
      gitbook: "YES",
    },
  },
  {
    feature: "Extensibility",
    scores: {
      folio: "YES",
      pdoc: "PARTIAL",
      sphinx: "YES",
      mkdocs: "YES",
      mintlify: "PARTIAL",
      gitbook: "PARTIAL",
    },
  },
  {
    feature: "Open source",
    scores: {
      folio: "YES",
      pdoc: "YES",
      sphinx: "YES",
      mkdocs: "YES",
      mintlify: "NO",
      gitbook: "NO",
    },
  },
  {
    feature: "Git + CI",
    scores: {
      folio: "YES",
      pdoc: "PARTIAL",
      sphinx: "YES",
      mkdocs: "YES",
      mintlify: "PARTIAL",
      gitbook: "PARTIAL",
    },
  },
]

function classNames(values: Array<string | false | undefined>) {
  return values.filter(Boolean).join(" ")
}

function ComparisonCell({
  value,
}: {
  value: ComparisonStatus
}) {
  const labels: Record<ComparisonStatus, string> = {
    YES: "Yes",
    PARTIAL: "Some",
    NO: "No",
  }
  const statusClasses: Record<ComparisonStatus, string> = {
    YES: "comparison-matrix-cell-yes",
    PARTIAL: "comparison-matrix-cell-partial",
    NO: "comparison-matrix-cell-no",
  }

  return (
    <span
      className={["comparison-matrix-cell", statusClasses[value]].join(" ")}
      aria-label={labels[value]}
      title={labels[value]}
    >
      <span className="comparison-matrix-value">{labels[value]}</span>
    </span>
  )
}

/**
 * A comparison table.
 *
 * Pass `tools` and `rows` to render the table the site configured (the
 * `landing.comparison` mapping in docs.yaml, or the props of an MDX page).
 * Without them the component falls back to Folio's own bundled matrix, which
 * is deprecated: it names Folio's own set of documentation tools, so it only
 * belongs on Folio's own pages.
 */
export function ComparisonMatrix({
  className,
  includeSurface = true,
  caption,
  tools,
  rows,
}: {
  className?: string
  includeSurface?: boolean
  caption?: string
  tools?: string[]
  rows?: ComparisonRow[]
}) {
  const configuredTools = tools ?? []
  const configuredRows = rows ?? []
  const isConfigured = configuredTools.length > 0 && configuredRows.length > 0

  return (
    <div
      className={
        classNames([includeSurface && "comparison-evidence", className]) ||
        undefined
      }
    >
      <div className="comparison-table-shell mx-auto w-fit max-w-full overflow-x-auto bg-card">
        {isConfigured ? (
          <ConfiguredMatrix
            caption={caption}
            tools={configuredTools}
            rows={configuredRows}
          />
        ) : (
          <BundledMatrix />
        )}
      </div>
    </div>
  )
}

function comparisonStatus(value: ComparisonValue): ComparisonStatus {
  if (value === true) {
    return "YES"
  }
  if (value === false) {
    return "NO"
  }
  return "PARTIAL"
}

/* Features down the rows, tools across the columns: the orientation the
 * `{tools, rows}` config shape spells out. */
function ConfiguredMatrix({
  caption,
  tools,
  rows,
}: {
  caption?: string
  tools: string[]
  rows: ComparisonRow[]
}) {
  return (
    <table className="w-full min-w-[36rem] table-fixed border-collapse text-left">
      <thead>
        <tr className="border-b border-border bg-muted/60">
          <th
            scope="col"
            className="comparison-tool-heading sticky left-0 z-20 px-4 py-2 text-xs font-semibold text-foreground"
          >
            {caption ?? ""}
          </th>
          {tools.map((tool) => (
            <th
              key={tool}
              scope="col"
              className="px-2 py-2 text-center text-xs leading-tight font-semibold text-foreground"
            >
              <span className="block">{tool}</span>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr
            key={row.feature}
            className="comparison-table-row border-b border-border last:border-b-0"
          >
            <th
              scope="row"
              className="comparison-tool-cell sticky left-0 z-10 px-4 py-2 text-sm text-foreground"
            >
              <span className="block font-semibold">{row.feature}</span>
              {row.note ? (
                <span className="block text-xs font-normal text-muted-foreground">
                  {row.note}
                </span>
              ) : null}
            </th>
            {row.values.map((value, index) => (
              <td
                key={`${row.feature}-${tools[index] ?? index}`}
                className="comparison-score-cell px-2 py-2 text-center"
                data-comparison-cell-status={comparisonStatus(
                  value
                ).toLowerCase()}
              >
                <ComparisonCell value={comparisonStatus(value)} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/* Deprecated: Folio's own scorecard, kept for the legacy `comparison: true`
 * config and for Folio's own docs pages. */
function BundledMatrix() {
  return (
    <table className="w-full min-w-[720px] table-fixed border-collapse text-left">
      <caption className="sr-only">
        Feature matrix comparing Folio with pdoc, Sphinx, MkDocs, Mintlify, and
        GitBook.
      </caption>
      <thead>
        <tr className="border-b border-border bg-muted/60">
          <th
            scope="col"
            className="comparison-tool-heading sticky left-0 z-20 px-4 py-2 text-xs font-semibold text-foreground"
          >
            Tool
          </th>
          {comparisonFeatureRows.map((feature) => (
            <th
              key={feature.feature}
              scope="col"
              className="comparison-framework-heading px-2 py-2 text-center text-xs leading-tight font-semibold text-foreground"
            >
              <span className="block">{feature.feature}</span>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {comparisonFrameworks.map((framework) => (
          <tr
            key={framework.key}
            className="comparison-table-row border-b border-border last:border-b-0"
            data-comparison-framework={framework.key}
          >
            <th
              scope="row"
              className="comparison-tool-cell sticky left-0 z-10 max-w-[8rem] px-4 py-2 text-sm text-foreground"
            >
              <span className="block font-semibold">{framework.label}</span>
            </th>
            {comparisonFeatureRows.map((feature) => (
              <td
                key={feature.feature}
                className="comparison-score-cell px-2 py-2 text-center"
                data-comparison-framework={framework.key}
                data-comparison-cell-status={feature.scores[
                  framework.key
                ].toLowerCase()}
              >
                <ComparisonCell value={feature.scores[framework.key]} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
