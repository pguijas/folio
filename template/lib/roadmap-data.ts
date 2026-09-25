export type RoadmapStatus = "shipped" | "active" | "next" | "later"

export type RoadmapFeature = string | { text: string; done?: boolean }

export interface RoadmapPhase {
  id: string
  version: string
  project?: string
  title: string
  status: RoadmapStatus
  layer: string
  summary: string
  command?: string
  features: RoadmapFeature[]
}

export const roadmapPhases: RoadmapPhase[] = []
