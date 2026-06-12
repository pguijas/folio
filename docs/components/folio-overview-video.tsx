export function FolioOverviewVideo() {
  return (
    <figure className="mx-auto my-10 w-full max-w-6xl overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <video
        className="aspect-video w-full bg-black"
        autoPlay
        loop
        muted
        playsInline
        preload="metadata"
        poster="/media/folio-commercial-v2-poster.jpeg"
        aria-label="Folio overview video"
      >
        <source src="/media/folio-commercial-v2.mp4" type="video/mp4" />
      </video>
    </figure>
  )
}
