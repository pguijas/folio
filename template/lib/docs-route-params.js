const DISABLED_DOC_STATIC_PATHS = [
  ["i18n"],
  ["landing"],
  ["plugins"],
  ["roadmap"],
  ["versioning"],
  ["api-reference", "folio", "extensions"],
  ["api-reference", "folio", "generator", "extension_emitter"],
  ["api-reference", "folio", "plugin"],
  ["api-reference", "folio", "plugins"],
  ["api-reference", "folio", "plugins", "roadmap"],
]

const DISABLED_DOC_STATIC_PATH_KEYS = new Set(
  DISABLED_DOC_STATIC_PATHS.map((path) => path.join("/"))
)

export function normalizeMdxPath(mdxPath) {
  if (!Array.isArray(mdxPath)) {
    return []
  }

  if (mdxPath.length === 1 && mdxPath[0] === "") {
    return []
  }

  if (mdxPath.at(-1) === "index.html") {
    return mdxPath.slice(0, -1)
  }

  return mdxPath
}

export function isDisabledMdxPath(mdxPath) {
  return DISABLED_DOC_STATIC_PATH_KEYS.has(normalizeMdxPath(mdxPath).join("/"))
}

export function normalizeStaticParam(param) {
  return { ...param, mdxPath: normalizeMdxPath(param.mdxPath) }
}

function staticParamKey(param) {
  return JSON.stringify(
    Object.keys(param)
      .sort()
      .map((key) => [key, param[key]])
  )
}

export function expandStaticParams(params, options = {}) {
  const includeIndexHtmlAliases =
    options.includeIndexHtmlAliases ?? process.env.NODE_ENV === "development"
  const includeDisabledParams =
    options.includeDisabledParams ?? process.env.NODE_ENV === "development"
  const expanded = []
  const seen = new Set()

  function push(param) {
    const key = staticParamKey(param)
    if (seen.has(key)) {
      return
    }
    seen.add(key)
    expanded.push(param)
  }

  for (const param of params) {
    const normalized = normalizeStaticParam(param)
    push(normalized)

    if (includeIndexHtmlAliases) {
      push({
        ...normalized,
        mdxPath: [...normalized.mdxPath, "index.html"],
      })
    }
  }

  if (includeDisabledParams) {
    for (const mdxPath of DISABLED_DOC_STATIC_PATHS) {
      push({ mdxPath })

      if (includeIndexHtmlAliases) {
        push({ mdxPath: [...mdxPath, "index.html"] })
      }
    }
  }

  return expanded
}
