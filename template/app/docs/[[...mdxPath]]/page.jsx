import { generateStaticParamsFor, importPage } from "nextra/pages"
import { notFound } from "next/navigation"
import {
  expandStaticParams,
  isDisabledMdxPath,
  normalizeMdxPath,
} from "@/lib/docs-route-params"
import { useMDXComponents as getMDXComponents } from "../../../mdx-components"
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

function docsRouteForMdxPath(mdxPath) {
  if (!mdxPath.length) {
    return docsIndexCanonicalPath === "/" ? "/" : "/docs/"
  }
  return `/docs/${mdxPath.join("/")}/`
}

function absoluteDocsUrl(mdxPath) {
  return siteUrl ? `${siteUrl}${docsRouteForMdxPath(mdxPath)}` : ""
}

function pageMetadata(metadata, mdxPath) {
  const canonical = absoluteDocsUrl(mdxPath)
  if (!canonical) {
    return metadata
  }

  const title = metadata.title ?? `${projectName} documentation`
  const description = metadata.description ?? projectDescription

  return {
    ...metadata,
    alternates: {
      ...metadata.alternates,
      canonical,
    },
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
