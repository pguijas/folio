// JS-side mirror of the Python feature gates: doc-route entries must match
// MVP_DISABLED_DOC_ROUTES and api-reference entries MVP_DISABLED_API_MODULES
// in folio/features.py (parity is enforced by
// tests/test_site_builder.py::test_docs_route_disabled_paths_match_python_feature_gates).
const DISABLED_DOC_STATIC_PATHS = [["i18n"], ["versioning"]]

const DISABLED_DOC_STATIC_PATH_KEYS = new Set(
  DISABLED_DOC_STATIC_PATHS.map((path) => path.join("/"))
)

const API_REFERENCE_SEGMENT = "api-reference"

function isApiReferencePath(mdxPath) {
  return mdxPath[0] === API_REFERENCE_SEGMENT
}

function normalizeDocsPathSegments(mdxPath) {
  if (isApiReferencePath(mdxPath)) {
    return mdxPath
  }
  return mdxPath.map((segment) =>
    typeof segment === "string" ? segment.replaceAll("_", "-") : segment
  )
}

function underscoreDocsPathAlias(mdxPath) {
  if (isApiReferencePath(mdxPath)) {
    return null
  }

  const alias = mdxPath.map((segment) =>
    typeof segment === "string" ? segment.replaceAll("-", "_") : segment
  )
  return alias.join("/") === mdxPath.join("/") ? null : alias
}

export function normalizeMdxPath(mdxPath) {
  if (!Array.isArray(mdxPath)) {
    return []
  }

  if (mdxPath.length === 1 && mdxPath[0] === "") {
    return []
  }

  let normalized = mdxPath
  if (mdxPath.at(-1) === "index.html") {
    normalized = mdxPath.slice(0, -1)
  }

  return normalizeDocsPathSegments(normalized)
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

    const underscoreAlias = underscoreDocsPathAlias(normalized.mdxPath)
    const aliasParam = underscoreAlias
      ? { ...normalized, mdxPath: underscoreAlias }
      : null
    if (aliasParam) {
      push(aliasParam)
    }

    if (includeIndexHtmlAliases) {
      push({
        ...normalized,
        mdxPath: [...normalized.mdxPath, "index.html"],
      })
      if (aliasParam) {
        push({
          ...aliasParam,
          mdxPath: [...aliasParam.mdxPath, "index.html"],
        })
      }
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
