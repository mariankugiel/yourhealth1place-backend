import type { Metadata } from "next"
import ProfessionalDashboardClient from "./professional-dashboard-client"

export const metadata: Metadata = {
  title: "Dashboard | Saluso Professional",
  description: "Professional healthcare dashboard",
}

export default function ProfessionalDashboard() {
  return <ProfessionalDashboardClient />
}
