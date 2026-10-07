import { HugeiconsIcon } from "@hugeicons/react"
import {
  NoteIcon,
  AlertCircleIcon,
  InformationCircleIcon,
  BulbIcon,
  CheckListIcon,
  AlertDiamondIcon,
} from "@hugeicons/core-free-icons"

type CalloutType = "note" | "warning" | "info" | "tip" | "check" | "danger"

// Each type's colours come from its --folioh-tone-* tokens, applied in
// app/styles/callout.css through data-variant.
const calloutIcons: Record<CalloutType, typeof NoteIcon> = {
  note: NoteIcon,
  warning: AlertCircleIcon,
  info: InformationCircleIcon,
  tip: BulbIcon,
  check: CheckListIcon,
  danger: AlertDiamondIcon,
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
  return (
    <div
      data-slot="callout"
      data-variant={type}
      className="my-5 rounded-lg border px-4 py-3.5 transition-colors duration-150"
    >
      <div className="flex gap-3">
        <div data-slot="callout-icon" className="mt-0.5 shrink-0">
          <HugeiconsIcon icon={calloutIcons[type]} size={18} strokeWidth={2} />
        </div>
        <div className="min-w-0 flex-1">
          {title && (
            <p data-slot="callout-title" className="mb-1 text-sm font-semibold">
              {title}
            </p>
          )}
          <div data-slot="callout-body" className="text-sm [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
