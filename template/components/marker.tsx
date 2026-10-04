import type { ReactNode } from "react"

interface MarkerProps {
  tone?: "ok" | "danger"
  children: ReactNode
}

export function Marker({ tone, children }: MarkerProps) {
  return (
    <div data-slot="marker" data-tone={tone} className="not-prose">
      {children}
    </div>
  )
}
