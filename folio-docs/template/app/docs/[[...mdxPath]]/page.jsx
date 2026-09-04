import { existsSync } from "fs"
import { join } from "path"
import { generateStaticParamsFor, importPage } from "nextra/pages"
import { notFound } from "next/navigation"
import {
  expandStaticParams,
  isDisabledMdxPath,
  normalizeMdxPath,
} from "@/lib/docs-route-params"
import { useMDXComponents as getMDXComponents } from "@/mdx-components"
import { PageActionsButton } from "@/components/page-actions-button"

const _nextraParams = generateStaticParamsFor("mdxPath")
const configuredSiteUrl = "__SITE_URL__"
const siteUrl = configuredSiteUrl.startsWith("http")
  ? configuredSiteUrl.replace(/\/$/, "")
  : ""
const projectName = "__PROJECT_NAME__"
const projectDescription = "__PROJECT_DESCRIPTION__"
const docsOgImageUrl = siteUrl
  ? `${siteUrl}/docs/opengraph-image`
  : "/docs/opengraph-image"
const docsIndexCanonicalPath = "__DOCS_INDEX_CANONICAL_PATH__"
const folioBasePath = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\/+$/, "") ?? ""
const markdownMirrorDir = join(process.cwd(), "public", "_folio", "markdown")

function docsRouteForMdxPath(mdxPath) {
  if (!mdxPath.length) {
    return docsIndexCanonicalPath === "/" ? "/" : "/docs/"
  }
  return `/docs/${mdxPath.join("/")}/`
}

function absoluteDocsUrl(mdxPath) {
  return siteUrl ? `${siteUrl}${docsRouteForMdxPath(mdxPath)}` : ""
}

// The build writes a Markdown mirror of every page into
// public/_folio/markdown, named after the content file rather than the docs
// route: content/plugins/index.mdx mirrors to plugins/index.md, not
// plugins.md. Probe both shapes on disk and link nothing when neither is
// there, so the head never points at a file the build did not write.
function markdownMirrorPath(mdxPath) {
  const route = mdxPath.length ? mdxPath.join("/") : "index"
  for (const candidate of [`${route}.md`, `${route}/index.md`]) {
    if (existsSync(join(markdownMirrorDir, candidate))) {
      return `/_folio/markdown/${candidate}`
    }
  }
  return ""
}

function markdownMirrorUrl(mdxPath) {
  const mirrorPath = markdownMirrorPath(mdxPath)
  if (!mirrorPath) {
    return ""
  }
  // A configured site URL already carries the deploy base path (it is what
  // canonical links are built from); without one, fall back to the base path
  // Next was configured with.
  return siteUrl ? `${siteUrl}${mirrorPath}` : `${folioBasePath}${mirrorPath}`
}

function pageAlternates(metadata, canonical, markdownUrl) {
  if (!canonical && !markdownUrl) {
    return null
  }

  return {
    ...metadata.alternates,
    ...(canonical ? { canonical } : {}),
    ...(markdownUrl
      ? {
          types: {
            ...metadata.alternates?.types,
            "text/markdown": markdownUrl,
          },
        }
      : {}),
  }
}

function pageMetadata(metadata, mdxPath) {
  const canonical = absoluteDocsUrl(mdxPath)
  const alternates = pageAlternates(
    metadata,
    canonical,
    markdownMirrorUrl(mdxPath)
  )
  if (!canonical) {
    return alternates ? { ...metadata, alternates } : metadata
  }

  const title = metadata.title ?? `${projectName} documentation`
  const description = metadata.description ?? projectDescription

  return {
    ...metadata,
    alternates,
    openGraph: {
      ...metadata.openGraph,
      title: metadata.openGraph?.title ?? title,
      description: metadata.openGraph?.description ?? description,
      url: canonical,
      images: metadata.openGraph?.images ?? [
        {
          url: docsOgImageUrl,
          width: 1200,
          height: 630,
          alt: `${title} - ${projectName}`,
        },
      ],
    },
    twitter: {
      ...metadata.twitter,
      card: metadata.twitter?.card ?? "summary_large_image",
      title: metadata.twitter?.title ?? title,
      description: metadata.twitter?.description ?? description,
      images: metadata.twitter?.images ?? [docsOgImageUrl],
    },
  }
}

export async function generateStaticParams() {
  const params = await _nextraParams()
  return expandStaticParams(params)
}

export async function generateMetadata(props) {
  const params = await props.params
  const mdxPath = normalizeMdxPath(params.mdxPath)
  if (isDisabledMdxPath(mdxPath)) {
    return {
      robots: {
        index: false,
        follow: false,
      },
    }
  }
  const { metadata } = await importPage(mdxPath)
  return pageMetadata(metadata, mdxPath)
}

const Wrapper = getMDXComponents().wrapper

export default async function Page(props) {
  const params = await props.params
  const mdxPath = normalizeMdxPath(params.mdxPath)
  if (isDisabledMdxPath(mdxPath)) {
    notFound()
  }
  const normalizedParams = { ...params, mdxPath }
  const { default: MDXContent, toc, metadata } = await importPage(mdxPath)
  return (
    <Wrapper toc={toc} metadata={metadata}>
      <div className="mb-2 flex justify-end">
        <PageActionsButton />
      </div>
      <MDXContent {...props} params={normalizedParams} />
    </Wrapper>
  )
}
