import { Geist, Geist_Mono, Sora, JetBrains_Mono } from "next/font/google"
import { ThemeProvider } from "@/components/theme-provider"
import "nextra-theme-docs/style.css"
import "katex/dist/katex.min.css"
import "./globals.css"

const configuredSiteUrl = "__SITE_URL__"
const siteUrl = configuredSiteUrl.startsWith("http")
  ? configuredSiteUrl.replace(/\/$/, "")
  : ""
const rootUrl = siteUrl ? `${siteUrl}/` : ""
const projectName = "__PROJECT_NAME__"
const projectDescription = "__PROJECT_DESCRIPTION__"
const rootOgImageUrl = siteUrl ? `${siteUrl}/opengraph-image` : "/opengraph-image"
const structuredData = siteUrl
  ? JSON.stringify({
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      name: projectName,
      description: projectDescription,
      applicationCategory: "DeveloperApplication",
      operatingSystem: "Any",
      url: rootUrl,
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
    }).replace(/</g, "\\u003c")
  : ""

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
})

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
  display: "swap",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
})

export const metadata = {
  ...(siteUrl
    ? {
        metadataBase: new URL(siteUrl),
        alternates: {
          canonical: rootUrl,
        },
      }
    : {}),
  title: {
    default: projectName,
    template: `%s - ${projectName}`,
  },
  description: projectDescription,
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    ...(rootUrl ? { url: rootUrl } : {}),
    title: projectName,
    description: projectDescription,
    images: [
      {
        url: rootOgImageUrl,
        width: 1200,
        height: 630,
        alt: projectName,
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: projectName,
    description: projectDescription,
    images: [rootOgImageUrl],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning className={`${sora.variable} ${jetbrainsMono.variable} ${geistSans.variable} ${geistMono.variable}`}>
      <head>
        {structuredData ? (
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: structuredData }}
          />
        ) : null}
      </head>
      <body>
        <ThemeProvider>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary-foreground"
          >
            Skip to content
          </a>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
