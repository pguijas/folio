// Development fallback. Folio replaces this module with project data when it
// prepares a generated workspace.
export const folioProject = {
  name: "Folio",
  version: "0.0.0",
  repo: "",
  repoRef: "main",
  url: "",
} as const

export const folioTemplateParams = {} as const

export const folioDocs = {
  routeBase: "/docs",
  mdxContractVersion: "1.0",
} as const

export const folioTemplateContext = {
  project: folioProject,
  docs: folioDocs,
  template: {
    params: folioTemplateParams,
    docsRouteBase: folioDocs.routeBase,
    mdxContractVersion: folioDocs.mdxContractVersion,
  },
} as const
