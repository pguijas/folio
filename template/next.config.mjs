import nextra from 'nextra'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const configuredBasePath = '' // __FOLIO_BASE_PATH__
const isDevServer = process.env.NODE_ENV === 'development'
const rawBasePath = isDevServer
  ? process.env.FOLIO_BASE_PATH?.trim() ?? ''
  : process.env.FOLIO_BASE_PATH?.trim() || configuredBasePath
const normalizedBasePath = rawBasePath.replace(/\/+$/, '')
const basePath = normalizedBasePath && normalizedBasePath !== '/'
  ? normalizedBasePath.startsWith('/')
    ? normalizedBasePath
    : `/${normalizedBasePath}`
  : undefined

const withNextra = nextra({
  contentDirBasePath: '/docs',
  latex: true,
  defaultShowCopyCode: true,
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  ...(basePath ? { basePath, assetPrefix: basePath } : {}),
  env: {
    NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? "",
  },
  images: { unoptimized: true },
  turbopack: {
    root: __dirname,
    resolveAlias: {
      'next-mdx-import-source-file': './mdx-components.tsx',
    },
  },
  __I18N_CONFIG__
}

export default withNextra(nextConfig)
