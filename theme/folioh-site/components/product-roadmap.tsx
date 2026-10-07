"use client"

import { roadmapPhases } from "@/lib/roadmap-data"
import { roadmapProjects } from "@/lib/roadmap-projects"
import { RoadmapProjectCard } from "@/components/roadmap-project-card"
import {
  groupPhasesByProject,
  type RoadmapProject,
} from "@/lib/roadmap-utils"

/* The release plan, on the landing.
 *
 * The card is the plugin's own `RoadmapProjectCard`, not a copy of it. The
 * phases come from the generated `lib/roadmap-data.ts` and the project's
 * label and description from the generated `lib/roadmap-projects.ts`, so both
 * follow `roadmap.phases` and `roadmap.projects` in docs.yaml. The plugin
 * writes both modules whether or not `routes.public` turns the `/roadmap/`
 * route on.
 */
export function ProductRoadmap({
  project,
}: {
  /** The `project` key its phases carry in docs.yaml. */
  project: string
}) {
  const projects: Record<string, RoadmapProject> = {
    [project]: roadmapProjects[project] ?? {},
  }
  const group = groupPhasesByProject(roadmapPhases, projects).find(
    (candidate) => candidate.key === project
  )

  /* A project with no phases gets no card rather than an empty one, so a
     site that configured a project it never shipped draws no heading over
     nothing. */
  if (!group || group.phases.length === 0) {
    return null
  }

  return <RoadmapProjectCard group={group} />
}
