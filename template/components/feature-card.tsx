import { cn } from "@/lib/utils"
import { HugeiconsIcon, type IconSvgElement } from "@hugeicons/react"
import {
  AiNetworkIcon,
  AlertCircleIcon,
  Analytics01Icon,
  BookOpenTextIcon,
  BrainCogIcon,
  ChartEvaluationIcon,
  CodeIcon,
  DashboardSquare01Icon,
  DatabaseSyncIcon,
  GitBranchIcon,
  HelpCircleIcon,
  PackageIcon,
  PlayCircleIcon,
  RocketIcon,
  Route03Icon,
  ServerStack01Icon,
  Settings02Icon,
  Share05Icon,
  SourceCodeIcon,
  TerminalIcon,
  UserGroupIcon,
  WorkflowSquare06Icon,
} from "@hugeicons/core-free-icons"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"

interface FeatureCardProps {
  title: string
  description: string
  icon?: string
  href?: string
}

const FEATURE_ICONS: Record<string, IconSvgElement> = {
  ai: BrainCogIcon,
  analytics: Analytics01Icon,
  architecture: WorkflowSquare06Icon,
  api: SourceCodeIcon,
  book: BookOpenTextIcon,
  code: CodeIcon,
  community: UserGroupIcon,
  dashboard: DashboardSquare01Icon,
  data: DatabaseSyncIcon,
  diagnose: HelpCircleIcon,
  experiment: ChartEvaluationIcon,
  git: GitBranchIcon,
  install: PackageIcon,
  monitor: DashboardSquare01Icon,
  network: AiNetworkIcon,
  quickstart: RocketIcon,
  run: PlayCircleIcon,
  server: ServerStack01Icon,
  settings: Settings02Icon,
  terminal: TerminalIcon,
  topology: Route03Icon,
  warning: AlertCircleIcon,
  workflow: WorkflowSquare06Icon,
  share: Share05Icon,
}

function FeatureIcon({ icon }: { icon?: string }) {
  if (!icon) {
    return null
  }

  const iconElement = FEATURE_ICONS[icon.toLowerCase()]

  if (!iconElement) {
    return (
      <div
        className="mb-2 text-2xl leading-none"
        aria-hidden="true"
        data-feature-card-icon={icon}
      >
        {icon}
      </div>
    )
  }

  return (
    <div
      className="mb-3 inline-flex size-9 items-center justify-center rounded-lg border border-primary/20 bg-primary/10 text-primary"
      aria-hidden="true"
      data-feature-card-icon={icon}
    >
      <HugeiconsIcon icon={iconElement} size={19} strokeWidth={1.9} />
    </div>
  )
}

export function FeatureCard({ title, description, icon, href }: FeatureCardProps) {
  const content = (
    <Card
      className={cn(
        "h-full transition-all duration-200",
        href && "cursor-pointer hover:ring-2 hover:ring-primary/30 hover:shadow-md"
      )}
    >
      <CardHeader className="gap-2">
        <FeatureIcon icon={icon} />
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
    </Card>
  )

  if (href) {
    return (
      <a href={href} className="no-underline text-inherit">
        {content}
      </a>
    )
  }

  return content
}
