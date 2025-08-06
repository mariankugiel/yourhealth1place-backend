import { Skeleton } from "@/components/ui/skeleton"

export default function Loading() {
  return (
    <div className="container py-6 space-y-6">
      <Skeleton className="h-12 w-48" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-[600px] w-full" />
        <Skeleton className="h-[600px] w-full" />
        <Skeleton className="h-[600px] w-full" />
      </div>
    </div>
  )
}
