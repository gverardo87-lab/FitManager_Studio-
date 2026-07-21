// src/components/clients/profile/SessioniTab.tsx
"use client";

/**
 * Tab "Sessioni" del profilo cliente: eventi del cliente.
 * Container sottile: fetch via useClientEvents, display delegato a EventsTable (condivisa
 * col dettaglio contratto — SSoT label stati, penali in rose).
 */

import { Calendar } from "lucide-react";

import { EventsTable } from "@/components/agenda/EventsTable";
import { useClientEvents } from "@/hooks/useAgenda";
import { DataErrorState } from "@/components/ui/data-error-state";
import { TabSkeleton, EmptyTab } from "./ProfileShared";

export function SessioniTab({ clientId }: { clientId: number }) {
  const { data, isLoading, isError, isFetching, refetch } = useClientEvents(clientId);

  if (isLoading) return <TabSkeleton />;
  if (isError) {
    return (
      <DataErrorState
        title="Sessioni non disponibili"
        message="Non è possibile verificare le sessioni del cliente."
        onRetry={() => void refetch()}
        isRetrying={isFetching}
      />
    );
  }

  const events = data?.items ?? [];

  if (events.length === 0) {
    return (
      <EmptyTab
        icon={Calendar}
        message="Nessuna sessione registrata"
        hint="Le sessioni si creano dall'Agenda e vengono collegate automaticamente."
        action={{ label: "Apri Agenda", href: `/agenda?newEvent=1&clientId=${clientId}` }}
      />
    );
  }

  return <EventsTable events={events} />;
}
