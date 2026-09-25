declare const __LANDING_FEATURES__: Array<{
  title: string
  description: string
  wide?: boolean
}>

declare const __LANDING_INSTALL_COMMANDS__: string[]
declare const __LANDING_SECTIONS__: Array<Record<string, unknown>>

declare const __VERSIONS__: Array<{
  label: string
  path: string
  defaultPath?: string
}>

declare const __PROJECT_NAME_JSON__: string
declare const __PROJECT_MONOGRAM_JSON__: string
declare const __PROJECT_VERSION_JSON__: string
declare const __LANDING_TAGLINE_JSON__: string
declare const __LANDING_NOTICE_TEXT_JSON__: string
declare const __LANDING_NOTICE_LINK_JSON__: string
declare const __LANDING_HEADLINE_JSON__: string
declare const __LANDING_DESCRIPTION_JSON__: string
declare const __LANDING_CTA_PRIMARY_TEXT_JSON__: string
declare const __LANDING_CTA_PRIMARY_LINK_JSON__: string
declare const __LANDING_CTA_SECONDARY_TEXT_JSON__: string
declare const __LANDING_CTA_SECONDARY_LINK_JSON__: string | null
declare const __LANDING_HERO_VARIANT_JSON__:
  | "docs-map"
  | "source-pipeline"
  | "build-pipeline"
  | "heartbeat"
declare const __CURRENT_VERSION_PATH__: string
