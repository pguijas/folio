import { Badge } from "@/components/ui/badge"

interface TypeBadgeProps {
  type: string
  href?: string
}

export function TypeBadge({ type, href }: TypeBadgeProps) {
  if (href) {
    return (
      <a href={href} className="no-underline">
        <Badge data-slot="type-badge" variant="secondary" className="font-mono text-xs">
          {type}
        </Badge>
      </a>
    )
  }
  return (
    <Badge data-slot="type-badge" variant="secondary" className="font-mono text-xs">
      {type}
    </Badge>
  )
}
