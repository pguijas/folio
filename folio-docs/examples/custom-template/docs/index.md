# Custom Template Example

This tiny site exists to prove that a **real** custom template keeps building.

It uses `template.overlay_path` to override a single file
(`components/callout.tsx`) on top of the bundled Folio template. Everything else
— the Next/Nextra scaffolding, the MDX contract components, the injection
markers — is inherited from the bundled template, so this is the minimal valid
custom template.

If the overlay merge or the bundled marker/MDX contract ever regresses, this
example fails to build and CI catches it.
