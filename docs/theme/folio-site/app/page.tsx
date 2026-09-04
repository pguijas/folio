"use client"

import { FolioPrelanding } from "@/components/folio-prelanding"
import { LandingNavbar } from "@/components/landing-navbar"
import { ThemeStyleBootstrap } from "@/components/theme-configurator"

export default function Home() {
  return (
    <div className="min-h-screen overflow-hidden bg-background">
      <ThemeStyleBootstrap />
      <LandingNavbar minimal />
      <main id="main-content">
        <FolioPrelanding />
      </main>
    </div>
  )
}
