// FOLIO_OVERLAY_SENTINEL — this file is contributed by the custom-template
// example's overlay/ and overrides ONLY the bundled Callout component. It is a
// deliberately minimal, dependency-free replacement so the example stays cheap
// to build; every other template file is inherited from the bundled template.
import { cn } from "@/lib/utils"

type CalloutType = "note" | "warning" | "info" | "tip" | "check" | "danger"

const calloutStyles: Record<CalloutType, string> = {
  note: "border-primary/20 bg-primary/5",
  warning: "border-amber-500/30 bg-amber-500/10",
  info: "border-border bg-muted",
  tip: "border-primary/20 bg-primary/5",
  check: "border-primary/20 bg-primary/5",
  danger: "border-destructive/20 bg-destructive/5",
}

export function Callout({
  type = "note",
  title,
  children,
}: {
  type?: CalloutType
  title?: string
  children?: React.ReactNode
}) {
  return (
    <div className={cn("my-4 rounded-lg border px-4 py-3", calloutStyles[type])}>
      {title ? <p className="mb-1 font-semibold">{title}</p> : null}
      <div className="text-sm">{children}</div>
    </div>
  )
}

export default Callout
