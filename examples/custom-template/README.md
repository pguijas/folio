# Custom template example (one-file overlay)

This example is the smallest possible **valid custom template**. Rather than
vendoring a full Next/Nextra template, it uses the opt-in
`template.overlay_path` key to layer a single overridden file
(`overlay/components/callout.tsx`) on top of the bundled Folio template.

Everything the overlay does not provide falls back to the bundled template, so
the Folio marker and MDX contracts are satisfied entirely by the bundled
fallbacks — you only own the file you actually want to change.

## Layout

```
custom-template/
  docs.yaml                       # template.overlay_path: "overlay"
  docs/index.md                   # a tiny source page so the build has content
  overlay/
    components/callout.tsx        # the ONE file overridden atop the bundle
```

## Build it

```bash
uv run folio build
```

The build copies the bundled template into `.build/`, overlays
`components/callout.tsx`, injects project metadata, and renders `docs/`.

## Why it exists

It is a regression guard. `tests/test_examples.py` runs the workspace
preparation for this exact project (with the Next/pnpm steps mocked) and asserts
the prepared `.build/` tree is coherent — overlay file overridden, bundled
fallbacks present, no residual injection markers. CI additionally performs a
real build so a broken custom-template contract is caught end to end.
