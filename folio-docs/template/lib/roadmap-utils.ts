import type { RoadmapPhase, RoadmapStatus } from "@/lib/roadmap-data"

/**
 * Shared roadmap arithmetic: ordering and grouping.
 *
 * Pure functions only — no JSX and no React — because the shipped roadmap
 * (`components/roadmap.tsx`) and the design studies beside it all need the
 * same answers, and the shipped one must stay out of the hydration bundle.
 */

/** Presentation for one project key, from `roadmap.projects` in docs.yaml. */
export interface RoadmapProject {
  label?: string
  description?: string
}

/** A phase that names no project still belongs to one. Matches the plugin's
 * own DEFAULT_PROJECT so the key a build groups on is the key it configures. */
export const DEFAULT_PROJECT_KEY = "shared"

export const statusLabels: Record<RoadmapStatus, string> = {
  shipped: "Shipped",
  active: "In progress",
  next: "Up next",
  later: "Later",
}

export function projectKeyOf(phase: RoadmapPhase): string {
  return phase.project || DEFAULT_PROJECT_KEY
}

/** The display name for a project key, falling back to the key itself.
 *
 * A framework component never names one project's products, so there is no
 * table of known keys here: an unlabelled project renders as whatever the
 * site called it in docs.yaml. */
export function projectLabel(
  key: string,
  projects?: Record<string, RoadmapProject>
): string {
  return projects?.[key]?.label || key
}

/**
 * Order two version strings numerically, segment by segment.
 *
 * String comparison puts 0.10 before 0.2 and a naive two-segment split drops
 * a third; both are wrong on a real release list, so every dot-separated
 * segment is compared as a number and a missing segment counts as zero
 * (1.2 sorts before 1.2.1). A leading "v" is tolerated because authors write
 * both forms. Non-numeric segments compare as zero rather than as NaN, which
 * would make the comparator inconsistent and the sort unstable.
 */
export function compareVersions(a: string, b: string): number {
  const left = segments(a)
  const right = segments(b)
  const depth = Math.max(left.length, right.length)
  for (let i = 0; i < depth; i++) {
    const delta = (left[i] ?? 0) - (right[i] ?? 0)
    if (delta !== 0) return delta
  }
  return 0
}

function segments(version: string): number[] {
  return version
    .trim()
    .replace(/^v/i, "")
    .split(".")
    .map((part) => {
      const value = Number.parseInt(part, 10)
      return Number.isNaN(value) ? 0 : value
    })
}

/**
 * Releases in version order, ascending, always.
 *
 * Status is a property of a release, never its position: this project has
 * 0.6 marked `later` and 0.7 marked `next`, so sorting on status prints
 * 0.5, 0.7, 0.6 and the numerals count backwards. Non-mutating, and stable
 * for equal versions because equal versions compare 0 and Array#sort has
 * been stable since ES2019.
 */
export function sortByVersion(phases: RoadmapPhase[]): RoadmapPhase[] {
  return [...phases].sort((a, b) => compareVersions(a.version, b.version))
}

/** One project's releases, with the presentation the site configured for it. */
export interface RoadmapGroup {
  key: string
  label: string
  description?: string
  phases: RoadmapPhase[]
}

/**
 * Phases split by project, each group version-sorted.
 *
 * `projects` is docs.yaml's `roadmap.projects`, and its key order is the
 * authority: project order is addressable state here, deciding which column a
 * rail draws first and which segment a switch opens on. A project the site did
 * not configure still gets a group, ordered by where its first phase appeared,
 * so an unconfigured project is never dropped and never silently reordered.
 */
export function groupPhasesByProject(
  phases: RoadmapPhase[],
  projects?: Record<string, RoadmapProject>
): RoadmapGroup[] {
  const buckets = new Map<string, RoadmapPhase[]>()
  for (const phase of phases) {
    const key = projectKeyOf(phase)
    const bucket = buckets.get(key)
    if (bucket) bucket.push(phase)
    else buckets.set(key, [phase])
  }

  const appearance = [...buckets.keys()]
  const declared = projects ? Object.keys(projects) : []
  const keys = [
    ...declared.filter((key) => buckets.has(key)),
    ...appearance.filter((key) => !declared.includes(key)),
  ]

  return keys.map((key) => ({
    key,
    label: projectLabel(key, projects),
    description: projects?.[key]?.description,
    phases: sortByVersion(buckets.get(key) as RoadmapPhase[]),
  }))
}
