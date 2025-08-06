import { Suspense } from "react"
import HealthPlansClientPage from "./health-plans-client-page"
import { Skeleton } from "@/components/ui/skeleton"

export default function HealthPlansPage() {
  return (
    <Suspense
      fallback={
        <div className="container py-6 space-y-4">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-32" />
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        </div>
      }
    >
      <HealthPlansClientPage />
    </Suspense>
  )
}
