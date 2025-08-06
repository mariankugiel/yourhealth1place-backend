import { Suspense } from "react"
import StatisticsPage from "./statistics-client-page"
import { Skeleton } from "@/components/ui/skeleton"

export default function Statistics() {
  return (
    <Suspense
      fallback={
        <div className="container py-6 space-y-6">
          <Skeleton className="h-12 w-48" />
          <div className="grid gap-6 md:grid-cols-4">
            {Array(4)
              .fill(0)
              .map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
          </div>
          <Skeleton className="h-[400px] w-full" />
        </div>
      }
    >
      <StatisticsPage />
    </Suspense>
  )
}
