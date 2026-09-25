"use client"

import * as React from "react"
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes"

// `theme.dark_mode: false` in docs.yaml sets this to false: the site stays
// light, and the mode controls, the toggles and the `d` shortcut go away.
const darkModeEnabled: boolean = true // __FOLIO_DARK_MODE__

function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  if (!darkModeEnabled) {
    // A storage key of its own, so a "dark" saved while dark mode was on
    // cannot leak into resolvedTheme.
    return (
      <NextThemesProvider
        attribute="class"
        disableTransitionOnChange
        {...props}
        forcedTheme="light"
        defaultTheme="light"
        enableSystem={false}
        themes={["light"]}
        storageKey="folio-theme-light"
      >
        {children}
      </NextThemesProvider>
    )
  }
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      <ThemeHotkey />
      {children}
    </NextThemesProvider>
  )
}

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  return (
    target.isContentEditable ||
    target.tagName === "INPUT" ||
    target.tagName === "TEXTAREA" ||
    target.tagName === "SELECT"
  )
}

function ThemeHotkey() {
  const { resolvedTheme, setTheme } = useTheme()

  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.repeat) {
        return
      }

      if (event.metaKey || event.ctrlKey || event.altKey) {
        return
      }

      if (event.key.toLowerCase() !== "d") {
        return
      }

      if (isTypingTarget(event.target)) {
        return
      }

      setTheme(resolvedTheme === "dark" ? "light" : "dark")
    }

    window.addEventListener("keydown", onKeyDown)

    return () => {
      window.removeEventListener("keydown", onKeyDown)
    }
  }, [resolvedTheme, setTheme])

  return null
}

export { ThemeProvider }
