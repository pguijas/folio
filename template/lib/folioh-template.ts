// Development fallback. Folioh replaces this module with project data when it
// prepares a generated workspace.
export const foliohProject = {
  name: "Folioh",
  version: "0.0.0",
  repo: "",
  repoRef: "main",
  url: "",
} as const

export const foliohTemplateParams = {} as const

export const foliohDocs = {
  routeBase: "/docs",
  mdxContractVersion: "1.0",
} as const

export const foliohTemplateContext = {
  project: foliohProject,
  docs: foliohDocs,
  template: {
    params: foliohTemplateParams,
    docsRouteBase: foliohDocs.routeBase,
    mdxContractVersion: foliohDocs.mdxContractVersion,
  },
} as const
