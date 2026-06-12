import type { CSSProperties } from "react"

type ApiModule = {
  name: string
  description: string
  href: string
  classCount: number
  functionCount: number
}

type ApiModuleGroup = {
  title: string
  modules: ApiModule[]
}

const groupAccents = [
  "oklch(0.58 0.075 150)",
  "oklch(0.56 0.078 248)",
  "oklch(0.61 0.09 42)",
  "oklch(0.52 0.07 305)",
]

function pluralize(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`
}

function groupModules(modules: ApiModule[]): ApiModuleGroup[] {
  const groups = new Map<string, ApiModule[]>()

  modules.forEach((module) => {
    const [scope] = module.name.split(".")
    const title = scope ? `${scope} package` : "Modules"
    const entries = groups.get(title) ?? []
    entries.push(module)
    groups.set(title, entries)
  })

  return Array.from(groups, ([title, entries]) => ({
    title,
    modules: entries,
  }))
}

function groupStyle(index: number) {
  return {
    "--api-reference-index-accent": groupAccents[index % groupAccents.length],
  } as CSSProperties
}

export function ApiReferenceIndex({ modules }: { modules: ApiModule[] }) {
  const moduleCount = modules.length
  const classCount = modules.reduce(
    (total, module) => total + module.classCount,
    0
  )
  const functionCount = modules.reduce(
    (total, module) => total + module.functionCount,
    0
  )
  const groups = groupModules(modules)
  const modulesWithClasses = modules.filter((module) => module.classCount > 0)
  const modulesWithFunctions = modules.filter(
    (module) => module.functionCount > 0
  )
  const primaryModule = modules[0]

  const fastPaths = [
    {
      label: "Start at the root",
      value: primaryModule?.name ?? "No modules",
      href: primaryModule?.href,
    },
    {
      label: "Inspect classes",
      value: pluralize(classCount, "class", "classes"),
      href: modulesWithClasses[0]?.href,
    },
    {
      label: "Find functions",
      value: pluralize(functionCount, "function"),
      href: modulesWithFunctions[0]?.href,
    },
  ]

  return (
    <div className="api-reference-index">
      <section
        className="api-reference-index-hero"
        aria-labelledby="api-reference-index-title"
      >
        <div className="api-reference-index-hero-copy">
          <p className="api-reference-index-kicker">Python API catalog</p>
          <h2 id="api-reference-index-title">
            Open the right module before reading every symbol.
          </h2>
          <p>
            This reference covers {pluralize(moduleCount, "module")} across{" "}
            {pluralize(groups.length, "package")} with{" "}
            {pluralize(classCount, "class", "classes")} and{" "}
            {pluralize(functionCount, "function")}. Use this page as a routing
            layer: scan the surface, open the module, then jump into classes,
            functions, parameters, and source links.
          </p>
        </div>
        <div className="api-reference-index-panel" aria-label="API summary">
          <span>{pluralize(moduleCount, "module")}</span>
          <span>{pluralize(classCount, "class", "classes")}</span>
          <span>{pluralize(functionCount, "function")}</span>
        </div>
      </section>

      <section
        className="api-reference-index-fast-paths"
        aria-labelledby="api-fast-path-title"
      >
        <div>
          <p className="api-reference-index-kicker">Fast paths</p>
          <h3 id="api-fast-path-title">Start from the question in front of you.</h3>
        </div>
        <div className="api-reference-index-path-list">
          {fastPaths.map((path) => {
            const content = (
              <>
                <span>{path.label}</span>
                <p>{path.value}</p>
              </>
            )

            if (path.href) {
              return (
                <a
                  className="api-reference-index-path"
                  href={path.href}
                  key={path.label}
                >
                  {content}
                </a>
              )
            }

            return (
              <div className="api-reference-index-path" key={path.label}>
                {content}
              </div>
            )
          })}
        </div>
      </section>

      <div className="api-reference-index-groups">
        {groups.map((group, index) => (
          <section
            className="api-reference-index-group"
            key={group.title}
            style={groupStyle(index)}
            aria-labelledby={`${group.title.replaceAll(" ", "-")}-title`}
          >
            <div className="api-reference-index-group-heading">
              <span className="api-reference-index-swatch" aria-hidden="true" />
              <h3 id={`${group.title.replaceAll(" ", "-")}-title`}>
                {group.title}
              </h3>
              <p>
                {pluralize(group.modules.length, "module")} in this namespace.
              </p>
            </div>
            <div className="api-reference-index-links">
              {group.modules.map((module) => (
                <a
                  className="api-reference-index-link"
                  href={module.href}
                  key={module.name}
                >
                  <span className="api-reference-index-link-meta">
                    {pluralize(module.classCount, "class", "classes")} /{" "}
                    {pluralize(module.functionCount, "function")}
                  </span>
                  <strong>{module.name}</strong>
                  <span>{module.description}</span>
                  <em>Open module</em>
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
