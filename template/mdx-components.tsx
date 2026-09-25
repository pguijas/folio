import type { ReactNode } from "react"
import { useMDXComponents as getThemeComponents } from "nextra-theme-docs"
import { ParamTable } from "@/components/param-table"
import { ClassOverview } from "@/components/class-overview"
import { TypeBadge } from "@/components/type-badge"
import { MethodAccordion } from "@/components/method-accordion"
import { ExampleTabs } from "@/components/example-tabs"
import { DeprecationNotice } from "@/components/deprecation-notice"
import { Callout } from "@/components/callout"
import { CodeGroup } from "@/components/code-group"
import { SourceLink } from "@/components/source-link"
import { Steps, Step } from "@/components/steps"
import { Mermaid } from "@/components/mermaid"
import { FileTree } from "@/components/file-tree"
import { FeatureCard } from "@/components/feature-card"
import { CardGrid } from "@/components/card-grid"
import { Tabs, TabItem } from "@/components/tabs"
import { Accordion, AccordionItem } from "@/components/accordion"
import { Timeline, TimelineItem } from "@/components/timeline"
import { TerminalSession } from "@/components/terminal-session"
import { ConfigPanel } from "@/components/config-panel"
import { BuildArtifact } from "@/components/build-artifact"
import { DocPreview } from "@/components/doc-preview"
import { PreviewCode } from "@/components/preview-code"
import { CommandGrid, CommandCard } from "@/components/command-grid"
import { BeforeAfter } from "@/components/before-after"
import { Checklist } from "@/components/checklist"
import { CompareMatrix } from "@/components/compare-matrix"
import { PullQuote } from "@/components/pull-quote"
import { StatStrip } from "@/components/stat-strip"
import { Swot } from "@/components/swot"
import { HookMap } from "@/components/hook-map"
import { ComponentIndex } from "@/components/component-index"
import { ApiReferenceIndex } from "@/components/api-reference-index"
import { ComparisonMatrix } from "@/components/comparison-matrix"
import { UnavailableFeature } from "@/components/unavailable-feature"
import { BrowserFrame } from "@/components/browser-frame"
// __FOLIO_COMPONENT_IMPORTS__

const themeComponents = getThemeComponents()

type TocItem = { value?: unknown } & Record<string, unknown>

type MdxWrapperProps = {
  children?: ReactNode
  toc?: unknown
  [key: string]: unknown
}

const navigationEmojiPattern =
  /[\u200d\u2300-\u23ff\u2600-\u27bf\ufe0e-\ufe0f\u{1f000}-\u{1faff}]+/gu

const ThemeWrapper = themeComponents.wrapper as
  | React.ComponentType<MdxWrapperProps>
  | undefined

function sanitizeNavigationLabel(value: unknown): unknown {
  if (typeof value !== "string") {
    return value
  }

  const cleaned = value
    .replace(navigationEmojiPattern, "")
    .replace(/\s+/g, " ")
    .trim()
  return cleaned || value
}

function sanitizeToc(toc: unknown): unknown {
  if (!Array.isArray(toc)) {
    return toc
  }

  return toc.map((item) => {
    if (!item || typeof item !== "object" || !("value" in item)) {
      return item
    }

    return {
      ...(item as TocItem),
      value: sanitizeNavigationLabel((item as TocItem).value),
    }
  })
}

function WrapperWithSanitizedToc(props: MdxWrapperProps) {
  if (!ThemeWrapper) {
    return <>{props.children}</>
  }

  return <ThemeWrapper {...props} toc={sanitizeToc(props.toc)} />
}

export function useMDXComponents(components?: Record<string, React.ComponentType>) {
  return {
    ...themeComponents,
    wrapper: WrapperWithSanitizedToc,
    ParamTable,
    ClassOverview,
    TypeBadge,
    MethodAccordion,
    ExampleTabs,
    DeprecationNotice,
    Callout,
    CodeGroup,
    SourceLink,
    Steps,
    Step,
    Mermaid,
    FileTree,
    FeatureCard,
    CardGrid,
    Tabs,
    TabItem,
    Accordion,
    AccordionItem,
    Timeline,
    TimelineItem,
    TerminalSession,
    ConfigPanel,
    BuildArtifact,
    DocPreview,
    PreviewCode,
    CommandGrid,
    CommandCard,
    BeforeAfter,
    Swot,
    CompareMatrix,
    PullQuote,
    StatStrip,
    Checklist,
    HookMap,
    ComponentIndex,
    ApiReferenceIndex,
    ComparisonMatrix,
    UnavailableFeature,
    BrowserFrame,
    // __FOLIO_COMPONENT_ENTRIES__
    ...components,
  }
}
