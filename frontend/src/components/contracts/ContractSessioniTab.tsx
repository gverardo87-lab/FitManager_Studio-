// src/components/contracts/ContractSessioniTab.tsx
"use client";

/**
 * Tab "Sessioni" del dettaglio contratto: eventi PT collegati al contratto.
 * Container sottile: fetch via useContractEvents, display delegato a EventsTable (condivisa).
 */

import { Skeleton } from "@/components/ui/skeleton";
import { DataErrorState } from "@/components/ui/data-error-state";
import { EventsTable } from "@/components/agenda/EventsTable";
import { useContractEvents } from "@/hooks/useAgenda";

export function ContractSessioniTab({ contractId }: { contractId: number }) {
  const { data, isLoading, isError, isFetching, refetch } = useContractEvents(contractId);

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <DataErrorState
        title="Sessioni del contratto non disponibili"
        message="Non è possibile verificare le sessioni collegate a questo contratto."
        onRetry={() => void refetch()}
        isRetrying={isFetching}
      />
    );
  }

  const events = data?.items ?? [];

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed py-12">
        <p className="text-sm text-muted-foreground">
          Nessuna sessione collegata a questo contratto
        </p>
      </div>
    );
  }

  return <EventsTable events={events} />;
}
