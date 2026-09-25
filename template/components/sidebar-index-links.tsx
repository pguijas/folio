"use client"

import { useEffect } from "react"

const FOLIO_BASE_PATH =
  process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\/+$/, "") ?? ""

function targetButton(target: EventTarget | null) {
  if (!(target instanceof Element)) return null
  return target.closest<HTMLButtonElement>("button[data-href]")
}

function withFolioBasePath(path: string) {
  if (/^[a-z][a-z\d+.-]*:/i.test(path)) return path
  if (!path.startsWith("/")) return path
  if (!FOLIO_BASE_PATH || FOLIO_BASE_PATH === "/") return path
  if (path === FOLIO_BASE_PATH || path.startsWith(`${FOLIO_BASE_PATH}/`)) {
    return path
  }

  return `${FOLIO_BASE_PATH}${path}`
}

function withTrailingSlash(href: string) {
  const hashIndex = href.indexOf("#")
  const beforeHash = hashIndex >= 0 ? href.slice(0, hashIndex) : href
  const hash = hashIndex >= 0 ? href.slice(hashIndex) : ""
  const queryIndex = beforeHash.indexOf("?")
  const pathname = queryIndex >= 0 ? beforeHash.slice(0, queryIndex) : beforeHash
  const query = queryIndex >= 0 ? beforeHash.slice(queryIndex) : ""
  const normalizedPathname = pathname.endsWith("/") ? pathname : `${pathname}/`

  return `${normalizedPathname}${query}${hash}`
}

function buttonHref(button: HTMLButtonElement) {
  const href = button.dataset.href
  if (!href) return null
  return withTrailingSlash(withFolioBasePath(href))
}

export function SidebarIndexLinks() {
  useEffect(() => {
    function handleClick(event: MouseEvent) {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      ) {
        return
      }

      const target = event.target
      if (target instanceof Element && target.closest("svg")) return

      const button = targetButton(target)
      if (!button) return

      const href = buttonHref(button)
      if (!href) return

      event.preventDefault()
      event.stopImmediatePropagation()
      window.location.assign(href)
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.key !== "Enter") return

      const target = event.target
      if (target instanceof Element && target.closest("svg")) return

      const button = targetButton(target)
      if (!button) return

      const href = buttonHref(button)
      if (!href) return

      event.preventDefault()
      event.stopImmediatePropagation()
      window.location.assign(href)
    }

    document.addEventListener("click", handleClick, true)
    document.addEventListener("keydown", handleKeyDown, true)

    return () => {
      document.removeEventListener("click", handleClick, true)
      document.removeEventListener("keydown", handleKeyDown, true)
    }
  }, [])

  return null
}
