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
import { OrganicEditorialImagePrompt } from "@/components/organic-editorial-image-prompt"
import { TerminalSession } from "@/components/terminal-session"
import { ConfigPanel } from "@/components/config-panel"
import { BuildArtifact } from "@/components/build-artifact"
import { DocPreview } from "@/components/doc-preview"
import { PreviewCode } from "@/components/preview-code"
import { CommandGrid, CommandCard } from "@/components/command-grid"
import { BeforeAfter } from "@/components/before-after"
import { Checklist } from "@/components/checklist"
import { HookMap } from "@/components/hook-map"
import { ComponentIndex } from "@/components/component-index"
import { ApiReferenceIndex } from "@/components/api-reference-index"
import { ComparisonMatrix } from "@/components/comparison-matrix"
import { UnavailableFeature } from "@/components/unavailable-feature"
// __FOLIO_COMPONENT_IMPORTS__

const themeComponents = getThemeComponents()

export function useMDXComponents(components?: Record<string, React.ComponentType>) {
  return {
    ...themeComponents,
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
    OrganicEditorialImagePrompt,
    TerminalSession,
    ConfigPanel,
    BuildArtifact,
    DocPreview,
    PreviewCode,
    CommandGrid,
    CommandCard,
    BeforeAfter,
    Checklist,
    HookMap,
    ComponentIndex,
    ApiReferenceIndex,
    ComparisonMatrix,
    UnavailableFeature,
    // __FOLIO_COMPONENT_ENTRIES__
    ...components,
  }
}
