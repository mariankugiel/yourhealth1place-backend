import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="container py-6 space-y-6">
      <Skeleton className="h-12 w-48" />
      <div className="grid grid-cols-7 gap-4">
        {Array(35)
          .fill(0)
          .map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
      </div>
    </div>
  )
}
