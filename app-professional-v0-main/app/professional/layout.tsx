"use client"

import type React from "react"
import Sidebar from "@/components/professional/sidebar"
import { LanguageProvider } from "@/lib/language-context"

// Wrap the content with the language provider
function ProfessionalLayoutContent({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <Sidebar />
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  )
}

// Export the layout with the language provider
export default function ProfessionalLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <LanguageProvider>
      <ProfessionalLayoutContent>{children}</ProfessionalLayoutContent>
    </LanguageProvider>
  )
}
