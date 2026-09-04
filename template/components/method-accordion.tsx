"use client"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"

interface Method {
  name: string
  signature: string
  description: string
  isAsync?: boolean
  children?: React.ReactNode
}

interface MethodAccordionProps {
  methods: Method[]
}

export function MethodAccordion({ methods }: MethodAccordionProps) {
  return (
    <Accordion type="multiple" className="my-4">
      {methods.map((method) => (
        <AccordionItem key={method.name} value={method.name}>
          <AccordionTrigger className="font-mono text-sm hover:no-underline">
            <div className="flex items-center gap-2 min-w-0">
              {method.isAsync && (
                <Badge variant="outline" className="shrink-0 text-xs">async</Badge>
              )}
              <span className="shrink-0">{method.name}</span>
              <span className="truncate text-muted-foreground font-normal">{method.signature}</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <p className="text-sm mb-2">{method.description}</p>
            {method.children}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
