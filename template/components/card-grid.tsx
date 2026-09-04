import { cn } from "@/lib/utils"

interface CardGridProps {
  columns?: 2 | 3 | 4
  children: React.ReactNode
}

const columnClasses: Record<number, string> = {
  2: "lg:grid-cols-2",
  3: "lg:grid-cols-3",
  4: "lg:grid-cols-4",
}

export function CardGrid({ columns = 3, children }: CardGridProps) {
  return (
    <div
      className={cn(
        "my-6 grid grid-cols-1 gap-4 md:grid-cols-2",
        columnClasses[columns]
      )}
    >
      {children}
    </div>
  )
}
