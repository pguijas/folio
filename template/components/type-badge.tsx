import { Badge } from "@/components/ui/badge"

interface TypeBadgeProps {
  type: string
  href?: string
}

export function TypeBadge({ type, href }: TypeBadgeProps) {
  if (href) {
    return (
      <a href={href} className="no-underline">
        <Badge variant="secondary" className="font-mono text-xs">
          {type}
        </Badge>
      </a>
    )
  }
  return (
    <Badge variant="secondary" className="font-mono text-xs">
      {type}
    </Badge>
  )
}
