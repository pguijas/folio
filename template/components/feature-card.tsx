import { cn } from "@/lib/utils"
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

export function FeatureCard({ title, description, icon, href }: FeatureCardProps) {
  const content = (
    <Card
      className={cn(
        "h-full transition-all duration-200",
        href && "cursor-pointer hover:ring-2 hover:ring-primary/30 hover:shadow-md"
      )}
    >
      <CardHeader>
        {icon && (
          <div className="text-2xl mb-1 leading-none" aria-hidden="true">
            {icon}
          </div>
        )}
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
