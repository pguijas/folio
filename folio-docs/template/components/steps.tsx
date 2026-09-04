"use client"

import { cn } from "@/lib/utils"

export function Steps({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "relative ml-4 pl-8 my-8",
        "[counter-reset:step]",
        "[&>div]:relative [&>div]:mb-10 [&>div:last-child]:mb-0"
      )}
    >
      <div className="absolute left-0 top-4 bottom-4 w-px bg-border" />
      {children}
    </div>
  )
}

export function Step({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="[counter-increment:step]">
      <div
        className={cn(
          "absolute -left-[41px] flex h-7 w-7 items-center justify-center rounded-full",
          "bg-primary text-primary-foreground text-xs font-semibold",
          "ring-4 ring-background",
          "before:content-[counter(step)]"
        )}
      />
      <h3 className="font-semibold text-base mb-1.5 text-foreground leading-7">
        {title}
      </h3>
      <div className="text-sm text-muted-foreground [&>p:first-child]:mt-0 [&>p:last-child]:mb-0">
        {children}
      </div>
    </div>
  )
}

Step.displayName = "Step"
