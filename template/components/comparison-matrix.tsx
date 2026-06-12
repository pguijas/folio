type ComparisonStatus = "YES" | "PARTIAL" | "NO"

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

export function ComparisonMatrix({
  className,
  includeSurface = true,
}: {
  className?: string
  includeSurface?: boolean
}) {
  return (
    <div
      className={
        classNames([includeSurface && "comparison-evidence", className]) ||
        undefined
      }
    >
      <div className="comparison-table-shell mx-auto w-fit max-w-full overflow-x-auto bg-card">
        <table className="w-full min-w-[720px] table-fixed border-collapse text-left">
          <caption className="sr-only">
            Feature matrix comparing Folio with pdoc, Sphinx, MkDocs, Mintlify,
            and GitBook.
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
                  <span className="block font-semibold">
                    {framework.label}
                  </span>
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
      </div>
    </div>
  )
}
