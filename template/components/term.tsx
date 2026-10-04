"use client"

import {
  useId,
  useRef,
  useState,
  type MouseEvent,
  type PointerEvent,
  type ReactNode,
  type TouchEvent,
} from "react"
import { HoverCard } from "radix-ui"

interface TermProps {
  def: string
  href?: string
  children: ReactNode
}

// A pointer shows the definition after a short hover, focus shows it the same
// way, and Escape hides it. A tap has no hover, so it toggles the definition
// instead, or follows `href` when the term has one. Screen readers get the
// definition as the trigger's description, so the floating copy is hidden
// from them.
export function Term({ def, href, children }: TermProps) {
  const [open, setOpen] = useState(false)
  const pointerType = useRef("")
  const trigger = useRef<HTMLElement | null>(null)
  const id = useId()

  const setTrigger = (node: HTMLElement | null) => {
    trigger.current = node
  }
  const onPointerDown = (event: PointerEvent) => {
    pointerType.current = event.pointerType
  }
  const onClick = (event: MouseEvent) => {
    const tapOrKey = pointerType.current === "touch" || event.detail === 0
    pointerType.current = ""
    setOpen((current) => (tapOrKey ? !current : true))
  }
  // The trigger cancels touchstart, but React listens to touch passively, so
  // the cancel only logs an error. Marking the event skips it.
  const onTouchStart = (event: TouchEvent) => {
    event.defaultPrevented = true
  }

  return (
    <HoverCard.Root open={open} onOpenChange={setOpen} openDelay={300} closeDelay={150}>
      <HoverCard.Trigger asChild onTouchStart={onTouchStart}>
        {href ? (
          <a ref={setTrigger} href={href} data-slot="term" aria-describedby={id}>
            {children}
          </a>
        ) : (
          <button
            ref={setTrigger}
            type="button"
            data-slot="term"
            aria-describedby={id}
            onPointerDown={onPointerDown}
            onMouseDown={(event) => event.preventDefault()}
            onClick={onClick}
          >
            {children}
          </button>
        )}
      </HoverCard.Trigger>
      <span id={id} hidden>
        {def}
      </span>
      <HoverCard.Portal>
        <HoverCard.Content
          data-slot="term-card"
          aria-hidden="true"
          side="top"
          sideOffset={8}
          collisionPadding={12}
          onPointerDownOutside={(event) => {
            if (trigger.current?.contains(event.target as Node)) event.preventDefault()
          }}
        >
          {def}
        </HoverCard.Content>
      </HoverCard.Portal>
    </HoverCard.Root>
  )
}
