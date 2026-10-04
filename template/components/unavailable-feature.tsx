import { HugeiconsIcon } from "@hugeicons/react"
import { AlertCircleIcon } from "@hugeicons/core-free-icons"

export function UnavailableFeature({
  title,
}: {
  feature: string
  title: string
}) {
  return (
    <section data-slot="unavailable-feature" className="unavailable-feature" aria-labelledby="unavailable-feature-title">
      <div data-slot="unavailable-feature-mark" className="unavailable-feature-mark" aria-hidden="true">
        <HugeiconsIcon icon={AlertCircleIcon} size={18} strokeWidth={1.9} />
      </div>
      <div data-slot="unavailable-feature-copy" className="unavailable-feature-copy">
        <p className="unavailable-feature-kicker">Not finished</p>
        <h1 id="unavailable-feature-title">{title}</h1>
        <p>This page is not finished yet.</p>
      </div>
    </section>
  )
}
