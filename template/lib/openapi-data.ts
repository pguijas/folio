export interface OpenApiOperation {
  method: string
  path: string
  summary: string
  description: string
  operationId: string
  tags: string[]
}

export interface OpenApiSource {
  title: string
  version: string
  description: string
  route: string
  servers: string[]
  operations: OpenApiOperation[]
  schemas: string[]
}

export const openApiSources: OpenApiSource[] = []
