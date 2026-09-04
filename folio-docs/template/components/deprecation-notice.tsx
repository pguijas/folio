import { Badge } from "@/components/ui/badge"

interface DeprecationNoticeProps {
  since?: string
  alternative?: string
  message?: string
}

export function DeprecationNotice({ since, alternative, message }: DeprecationNoticeProps) {
  return (
    <div className="my-4 rounded-lg border border-destructive/50 bg-destructive/5 p-4">
      <div className="flex items-center gap-2 mb-1">
        <Badge variant="destructive" className="text-xs">Deprecated</Badge>
        {since && (
          <span className="text-xs text-muted-foreground">since {since}</span>
        )}
      </div>
      {message && <p className="text-sm mt-1">{message}</p>}
      {alternative && (
        <p className="text-sm mt-1 text-muted-foreground">
          Use <code className="font-mono text-foreground">{alternative}</code> instead.
        </p>
      )}
    </div>
  )
}
