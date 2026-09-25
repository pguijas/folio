import { HugeiconsIcon } from "@hugeicons/react"
import {
  NoteIcon,
  AlertCircleIcon,
  InformationCircleIcon,
  BulbIcon,
  CheckListIcon,
  AlertDiamondIcon,
} from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

type CalloutType = "note" | "warning" | "info" | "tip" | "check" | "danger"

const calloutConfig: Record<
  CalloutType,
  {
    icon: typeof NoteIcon
    bg: string
    border: string
    iconColor: string
  }
> = {
  note: {
    icon: NoteIcon,
    bg: "bg-primary/5",
    border: "border-primary/20",
    iconColor: "text-primary",
  },
  warning: {
    icon: AlertCircleIcon,
    bg: "bg-warning/10",
    border: "border-warning/30",
    iconColor: "text-warning",
  },
  info: {
    icon: InformationCircleIcon,
    bg: "bg-muted",
    border: "border-border",
    iconColor: "text-muted-foreground",
  },
  tip: {
    icon: BulbIcon,
    bg: "bg-primary/5",
    border: "border-primary/20",
    iconColor: "text-primary",
  },
  check: {
    icon: CheckListIcon,
    bg: "bg-primary/5",
    border: "border-primary/20",
    iconColor: "text-primary",
  },
  danger: {
    icon: AlertDiamondIcon,
    bg: "bg-destructive/5",
    border: "border-destructive/20",
    iconColor: "text-destructive",
  },
}

export function Callout({
  type = "info",
  title,
  children,
}: {
  type?: CalloutType
  title?: string
  children: React.ReactNode
}) {
  const config = calloutConfig[type]
  return (
    <div
      className={cn(
        "my-5 rounded-lg border px-4 py-3.5",
        "transition-colors duration-150",
        config.border,
        config.bg
      )}
    >
      <div className="flex gap-3">
        <div className={cn("mt-0.5 shrink-0", config.iconColor)}>
          <HugeiconsIcon icon={config.icon} size={18} strokeWidth={2} />
        </div>
        <div className="min-w-0 flex-1">
          {title && (
            <p className="mb-1 text-sm font-semibold text-foreground">
              {title}
            </p>
          )}
          <div className="text-sm text-foreground/85 [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
