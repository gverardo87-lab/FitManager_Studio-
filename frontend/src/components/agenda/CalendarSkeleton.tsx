// src/components/agenda/CalendarSkeleton.tsx

/**
 * Skeleton di caricamento per il calendario agenda.
 * Toolbar + griglia 7 colonne x 8 righe.
 */

import { Skeleton } from "@/components/ui/skeleton";

export function CalendarSkeleton() {
  return (
    <div className="space-y-3">
      {/* Toolbar skeleton */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1.5">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-9 w-16 rounded-md" />
          <Skeleton className="h-9 w-9 rounded-md" />
        </div>
        <Skeleton className="h-6 w-40 rounded" />
        <div className="flex gap-1.5">
          <Skeleton className="h-9 w-20 rounded-md" />
          <Skeleton className="h-9 w-24 rounded-md" />
          <Skeleton className="h-9 w-20 rounded-md" />
        </div>
      </div>
      {/* Grid skeleton */}
      <div className="rounded-lg border">
        {/* Header row */}
        <div className="flex border-b">
          <Skeleton className="h-10 w-16 shrink-0" />
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-10 flex-1 border-l" />
          ))}
        </div>
        {/* Time rows */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex border-b last:border-b-0">
            <Skeleton className="h-16 w-16 shrink-0" />
            {Array.from({ length: 7 }).map((_, j) => (
              <div key={j} className="h-16 flex-1 border-l" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
