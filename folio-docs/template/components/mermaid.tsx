"use client"

import { useEffect, useRef, useState } from "react"
import { useTheme } from "next-themes"

interface MermaidProps {
  chart: string
}

const LIGHT_FALLBACK = {
  background: "#f4f2ee",
  foreground: "#1f1e1c",
  card: "#f8f6f1",
  muted: "#e8e6e1",
  mutedForeground: "#686662",
  accent: "#dde5c9",
  accentForeground: "#1f1e1c",
  border: "#b8b5af",
}

const DARK_FALLBACK = {
  background: "#171615",
  foreground: "#e5e2dc",
  card: "#1f1e1c",
  muted: "#2c2a27",
  mutedForeground: "#98958f",
  accent: "#363d2b",
  accentForeground: "#e5e2dc",
  border: "#4d4a45",
}

function cssVar(styles: CSSStyleDeclaration, name: string, fallback: string) {
  return styles.getPropertyValue(name).trim() || fallback
}

function clamp01(value: number) {
  return Math.min(1, Math.max(0, value))
}

function toSrgbChannel(value: number) {
  const channel = value <= 0.0031308
    ? value * 12.92
    : 1.055 * Math.pow(value, 1 / 2.4) - 0.055
  return Math.round(clamp01(channel) * 255)
}

function toHex(value: number) {
  return value.toString(16).padStart(2, "0")
}

function parseOklchChannel(value: string) {
  return value.endsWith("%") ? Number.parseFloat(value) / 100 : Number.parseFloat(value)
}

function oklchToHex(color: string) {
  const match = color.match(/^oklch\((.+)\)$/i)
  if (!match) return null

  const parts = match[1].replace(/\s*\/\s*/, " / ").trim().split(/\s+/)
  if (parts.length < 3) return null

  const lightness = parseOklchChannel(parts[0])
  const chroma = Number.parseFloat(parts[1])
  const hue = Number.parseFloat(parts[2]) * (Math.PI / 180)

  if (![lightness, chroma, hue].every(Number.isFinite)) return null

  const a = chroma * Math.cos(hue)
  const b = chroma * Math.sin(hue)
  const lPrime = lightness + 0.3963377774 * a + 0.2158037573 * b
  const mPrime = lightness - 0.1055613458 * a - 0.0638541728 * b
  const sPrime = lightness - 0.0894841775 * a - 1.2914855480 * b
  const l = lPrime ** 3
  const m = mPrime ** 3
  const s = sPrime ** 3

  const red = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
  const green = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
  const blue = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

  return `#${toHex(toSrgbChannel(red))}${toHex(toSrgbChannel(green))}${toHex(toSrgbChannel(blue))}`
}

function mermaidColor(styles: CSSStyleDeclaration, name: string, fallback: string) {
  const value = cssVar(styles, name, fallback)
  return oklchToHex(value) ?? value
}

function unescapeHtml(s: string) {
  return s
    .replace(/&gt;/g, ">")
    .replace(/&lt;/g, "<")
    .replace(/&amp;/g, "&")
    .replace(/&#123;/g, "{")
    .replace(/&#125;/g, "}")
    .replace(/&quot;/g, '"')
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
}

export function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState("")
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    let cancelled = false
    const cleanChart = unescapeHtml(chart)

    const render = async () => {
      try {
        const mermaid = (await import("mermaid")).default
        const rootStyles = getComputedStyle(document.documentElement)
        const bodyStyles = getComputedStyle(document.body)
        const fallback = resolvedTheme === "dark" ? DARK_FALLBACK : LIGHT_FALLBACK
        const background = mermaidColor(rootStyles, "--background", fallback.background)
        const foreground = mermaidColor(rootStyles, "--foreground", fallback.foreground)
        const card = mermaidColor(rootStyles, "--card", fallback.card)
        const muted = mermaidColor(rootStyles, "--muted", fallback.muted)
        const mutedForeground = mermaidColor(rootStyles, "--muted-foreground", fallback.mutedForeground)
        const accent = mermaidColor(rootStyles, "--accent", fallback.accent)
        const accentForeground = mermaidColor(rootStyles, "--accent-foreground", fallback.accentForeground)
        const border = mermaidColor(rootStyles, "--border", fallback.border)
        const fontFamily = bodyStyles.fontFamily || "ui-sans-serif, system-ui, sans-serif"

        mermaid.initialize({
          startOnLoad: false,
          theme: "base",
          darkMode: resolvedTheme === "dark",
          flowchart: {
            curve: "basis",
            htmlLabels: true,
          },
          themeVariables: {
            background,
            fontFamily,
            fontSize: "14px",
            primaryColor: card,
            primaryTextColor: foreground,
            primaryBorderColor: border,
            secondaryColor: muted,
            secondaryTextColor: foreground,
            secondaryBorderColor: border,
            tertiaryColor: accent,
            tertiaryTextColor: accentForeground,
            tertiaryBorderColor: border,
            mainBkg: card,
            secondBkg: muted,
            nodeBorder: border,
            lineColor: mutedForeground,
            textColor: foreground,
            titleColor: foreground,
            edgeLabelBackground: background,
            clusterBkg: background,
            clusterBorder: border,
            noteBkgColor: accent,
            noteTextColor: accentForeground,
            noteBorderColor: border,
            actorBkg: card,
            actorBorder: border,
            actorTextColor: foreground,
            actorLineColor: border,
            signalColor: foreground,
            signalTextColor: foreground,
            labelBoxBkgColor: card,
            labelBoxBorderColor: border,
            labelTextColor: foreground,
            loopTextColor: foreground,
            activationBkgColor: muted,
            activationBorderColor: border,
          },
        })
        const id = `mermaid-${Math.random().toString(36).slice(2)}`
        const { svg: rendered } = await mermaid.render(id, cleanChart)
        if (!cancelled) setSvg(rendered)
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Unknown Mermaid error"
          setSvg(
            `<pre style="color: var(--destructive); white-space: pre-wrap;">${escapeHtml(`Failed to render Mermaid diagram:\n${message}\n\n${cleanChart}`)}</pre>`
          )
        }
      }
    }
    render()

    return () => { cancelled = true }
  }, [chart, resolvedTheme])

  if (!svg) {
    return (
      <div className="folio-mermaid">
        <pre className="text-sm text-muted-foreground">{chart}</pre>
      </div>
    )
  }

  return (
    <div
      ref={ref}
      className="folio-mermaid"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}
