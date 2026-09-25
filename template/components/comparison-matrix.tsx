import { cn } from "@/lib/utils"

import { CompareMatrix } from "@/components/compare-matrix"

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
  note?: string
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
      folio: "PARTIAL",
      pdoc: "PARTIAL",
      sphinx: "YES",
      mkdocs: "YES",
      mintlify: "PARTIAL",
      gitbook: "PARTIAL",
    },
    note: "Folio: built-in plugins only; project plugins are on the roadmap",
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

/* YES/PARTIAL/NO is how the bundled table was written; `CompareMatrix` speaks
 * true, "~" and false. */
function comparisonCell(value: ComparisonStatus): ComparisonValue {
  if (value === "YES") {
    return true
  }
  return value === "PARTIAL" ? "~" : false
}

/**
 * A comparison table.
 *
 * Pass `tools` and `rows` to render the table the site configured (the
 * `landing.comparison` mapping in docs.yaml, or the props of an MDX page).
 * Without them the component falls back to Folio's own bundled matrix, which
 * is deprecated: it names Folio's own set of documentation tools, so it only
 * belongs on Folio's own pages.
 *
 * Both render through `CompareMatrix`, so a page carrying one of each shows
 * one table twice rather than two tables that disagree about what a table
 * looks like.
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
  const configured = (tools?.length ?? 0) > 0 && (rows?.length ?? 0) > 0
  const bundledTools = comparisonFrameworks.map((framework) => framework.label)
  const bundledRows: ComparisonRow[] = comparisonFeatureRows.map((row) => ({
    feature: row.feature,
    values: comparisonFrameworks.map((framework) =>
      comparisonCell(row.scores[framework.key])
    ),
    note: row.note,
  }))

  return (
    <div className={cn(includeSurface && "comparison-evidence", className)}>
      <CompareMatrix
        caption={caption ?? (configured ? undefined : "Capability")}
        tools={configured ? tools! : bundledTools}
        rows={configured ? rows! : bundledRows}
      />
    </div>
  )
}
