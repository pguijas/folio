import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

type BaseEntry = string | { name: string; href?: string }

interface ClassOverviewProps {
  name: string
  bases?: BaseEntry[]
  decorators?: string[]
  description?: string
}

function renderBase(base: BaseEntry, index: number, total: number) {
  const name = typeof base === "string" ? base : base.name
  const href = typeof base === "string" ? undefined : base.href
  const separator = index < total - 1 ? ", " : ""

  if (href) {
    return (
      <span key={name}>
        <a href={href} className="underline decoration-dotted underline-offset-2 hover:decoration-solid">
          {name}
        </a>
        {separator}
      </span>
    )
  }
  return (
    <span key={name}>
      {name}
      {separator}
    </span>
  )
}

export function ClassOverview({ name, bases = [], decorators = [], description }: ClassOverviewProps) {
  return (
    <Card className="my-4">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {decorators.map((dec) => (
            <Badge key={dec} variant="outline" className="font-mono text-xs">
              @{dec}
            </Badge>
          ))}
        </div>
        <CardTitle className="font-mono text-lg">
          class {name}
          {bases.length > 0 && (
            <span className="text-muted-foreground font-normal">
              ({bases.map((b, i) => renderBase(b, i, bases.length))})
            </span>
          )}
        </CardTitle>
      </CardHeader>
      {description && (
        <CardContent>
          <p className="text-sm text-muted-foreground">{description}</p>
        </CardContent>
      )}
    </Card>
  )
}
