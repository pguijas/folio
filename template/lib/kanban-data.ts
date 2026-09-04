export interface KanbanCard {
  title: string
  description: string
  tags: string[]
  assignee: string[]
  size: string
  source: string
  link: string
  /* Roadmap phase this card belongs to, matched against phase.version. The
   * kanban plugin always writes it; the bundled stub keeps it optional so a
   * site without the plugin still typechecks. */
  milestone?: string
}

export interface KanbanColumn {
  id: string
  title: string
  limit: number | null
  cards: KanbanCard[]
}

export const kanbanColumns: KanbanColumn[] = []
