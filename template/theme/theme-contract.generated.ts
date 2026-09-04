// GENERATED FILE - DO NOT EDIT
// Source: folio/schemas/theme_contract.py

export interface ThemeStyle {
  "--folio-heading-font-family"?: string
  "--folio-body-font-family"?: string
  "--folio-code-font-family"?: string
  "--folio-heading-letter-spacing"?: string
  "--folio-heading-weight"?: string
  "--folio-body-line-height"?: string
  "--folio-font-size-base"?: string
  "--folio-card-shadow"?: string
  "--folio-card-border-width"?: string
  "--folio-card-padding"?: string
  "--folio-card-hover-shadow"?: string
  "--folio-card-backdrop"?: string
  "--folio-card-opacity"?: string
  "--folio-code-border-radius"?: string
  "--folio-code-border"?: string
  "--folio-code-bg"?: string
  "--folio-code-foreground"?: string
  "--folio-code-shadow"?: string
  "--folio-h2-border"?: string
  "--folio-h2-transform"?: string
  "--folio-h2-letter-spacing"?: string
  "--folio-h2-weight"?: string
  "--folio-h2-padding-left"?: string
  "--folio-h2-border-left"?: string
  "--folio-link-decoration"?: string
  "--folio-section-gap"?: string
  "--folio-content-max-width"?: string
  "--folio-workspace-shell-padding"?: string
  "--folio-workspace-shell-border"?: string
  "--folio-workspace-shell-shadow"?: string
  "--folio-workspace-shell-background"?: string
  "--folio-workspace-shell-surface"?: string
  "--folio-workspace-shell-topbar"?: string
  "--folio-workspace-shell-topbar-blur"?: string
  "--folio-workspace-shell-topbar-border"?: string
}

export type ThemeTuneKey =
  | "borderId"
  | "codeTreatmentId"
  | "colorId"
  | "contentWidthId"
  | "fontId"
  | "rhythmId"
  | "shellPaddingId"
  | "surfaceColorId"

export type ThemeVars = Record<string, string>

export const themeRadiusScale = ["0", "0.3rem", "0.5rem", "0.75rem", "1rem"] as const
