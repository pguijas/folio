import type { MetadataRoute } from "next"

export const dynamic = "force-static"

const SITE_URL: string = "__SITE_URL__"

export default function robots(): MetadataRoute.Robots {
  const sitemap =
    SITE_URL && SITE_URL.startsWith("http") ? `${SITE_URL}/sitemap.xml` : undefined

  return {
    rules: { userAgent: "*", allow: "/" },
    ...(sitemap ? { sitemap } : {}),
  }
}
