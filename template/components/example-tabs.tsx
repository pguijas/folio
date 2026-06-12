"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface Example {
  label: string
  code: string
  language?: string
}

interface ExampleTabsProps {
  examples: Example[]
}

export function ExampleTabs({ examples }: ExampleTabsProps) {
  if (examples.length === 0) return null

  return (
    <Tabs defaultValue={examples[0].label} className="my-4">
      <TabsList>
        {examples.map((ex) => (
          <TabsTrigger key={ex.label} value={ex.label}>
            {ex.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {examples.map((ex) => (
        <TabsContent key={ex.label} value={ex.label}>
          <pre className="rounded-lg bg-muted p-4 overflow-x-auto">
            <code className={`language-${ex.language ?? "python"}`}>
              {ex.code}
            </code>
          </pre>
        </TabsContent>
      ))}
    </Tabs>
  )
}
