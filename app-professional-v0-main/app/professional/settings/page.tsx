import { Suspense } from "react"
import SettingsClientPage from "./settings-client-page"
import { Skeleton } from "@/components/ui/skeleton"

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="container py-6 space-y-4">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-32" />
          <div className="grid gap-6">
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        </div>
      }
    >
      <SettingsClientPage />
    </Suspense>
  )
}
