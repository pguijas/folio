export type RoadmapStatus = "shipped" | "active" | "next" | "later"

export interface RoadmapPhase {
  id: string
  version: string
  title: string
  status: RoadmapStatus
  layer: string
  summary: string
  command?: string
  features: string[]
}

export const roadmapPhases: RoadmapPhase[] = []
