"use client"

import { useState } from "react"

export interface BenchmarkRow {
  label: string
  medianMs: number
  minMs: number
  maxMs: number
}

export interface BenchmarkChartProps {
  rows: BenchmarkRow[]
  caption?: string
}

type AxisMode = "median" | "range"

function formatMilliseconds(value: number): string {
  return `${value.toLocaleString("en-US", { maximumFractionDigits: 2 })} ms`
}

function percent(value: number, maximum: number): number {
  if (!Number.isFinite(value) || maximum <= 0) return 0
  return Math.min(100, Math.max(0, (value / maximum) * 100))
}

export function BenchmarkChart({
  rows,
  caption = "Observed Python timings",
}: BenchmarkChartProps) {
  const [axisMode, setAxisMode] = useState<AxisMode>("median")

  if (rows.length === 0) {
    return (
      <figure className="not-prose my-6 overflow-hidden rounded-lg border border-border bg-card">
        <figcaption className="border-b border-border px-4 py-3 text-sm font-semibold text-foreground">
          {caption}
        </figcaption>
        <p className="m-0 px-4 py-8 text-center text-sm text-muted-foreground">
          No measurements recorded yet.
        </p>
      </figure>
    )
  }

  const medianMaximum = Math.max(0, ...rows.map((row) => row.medianMs))
  const rangeMaximum = Math.max(0, ...rows.map((row) => row.maxMs))
  const axisMaximum = axisMode === "median" ? medianMaximum : rangeMaximum
  const plotMaximum = axisMaximum || 1

  return (
    <figure className="not-prose my-6 overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex flex-col gap-3 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <figcaption className="text-sm font-semibold text-foreground">
          {caption}
        </figcaption>
        <div
          className="inline-flex w-fit rounded-md border border-border bg-muted/35 p-0.5"
          role="group"
          aria-label="Benchmark chart axis"
        >
          {(["median", "range"] as const).map((mode) => {
            const selected = axisMode === mode
            const label = mode === "median" ? "Median axis" : "Range axis"
            return (
              <button
                key={mode}
                type="button"
                aria-pressed={selected}
                onClick={() => setAxisMode(mode)}
                className={`rounded px-2.5 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card ${
                  selected
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="border-b border-border/70 bg-muted/20 px-4 py-2.5">
        <p className="m-0 text-xs leading-5 text-muted-foreground" aria-live="polite">
          {axisMode === "median"
            ? `Bars end at the median. Linear scale: 0–${formatMilliseconds(axisMaximum)}.`
            : `Lines span the observed minimum–maximum range; dots mark medians. Linear scale: 0–${formatMilliseconds(axisMaximum)}.`}
        </p>
      </div>

      <ol className="m-0 list-none divide-y divide-border/70 p-0">
        {rows.map((row) => {
          const low = Math.min(row.minMs, row.maxMs)
          const high = Math.max(row.minMs, row.maxMs)
          const medianPosition = percent(row.medianMs, plotMaximum)
          const lowPosition = percent(low, plotMaximum)
          const highPosition = percent(high, plotMaximum)

          return (
            <li key={row.label} className="px-4 py-4">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
                <p className="m-0 min-w-0 text-sm font-medium text-foreground">
                  {row.label}
                </p>
                <p className="m-0 shrink-0 text-xs leading-5 text-muted-foreground tabular-nums sm:text-right">
                  <span className="font-medium text-foreground">
                    {formatMilliseconds(row.medianMs)} median
                  </span>
                  <span aria-hidden="true"> · </span>
                  <span>
                    {formatMilliseconds(row.minMs)}–{formatMilliseconds(row.maxMs)} range
                  </span>
                </p>
              </div>

              <div
                className="relative mt-3 h-5 overflow-hidden rounded-sm bg-muted/60"
                aria-hidden="true"
              >
                {axisMode === "median" ? (
                  <>
                    <span
                      className="absolute inset-y-0 left-0 rounded-sm bg-primary/25"
                      style={{ width: `${medianPosition}%` }}
                    />
                    <span
                      className="absolute inset-y-0 w-0.5 bg-primary"
                      style={{ left: `${medianPosition}%` }}
                    />
                  </>
                ) : (
                  <>
                    <span
                      className="absolute top-1/2 h-1 -translate-y-1/2 rounded-full bg-primary/35"
                      style={{
                        left: `${lowPosition}%`,
                        width: `${Math.max(0, highPosition - lowPosition)}%`,
                      }}
                    />
                    <span
                      className="absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-card bg-primary shadow-sm"
                      style={{ left: `${medianPosition}%` }}
                    />
                  </>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </figure>
  )
}
