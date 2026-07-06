// src/components/agenda/EventsTable.tsx
"use client";

/**
 * Tabella eventi presentazionale (props in, zero fetch) — condivisa dal profilo cliente
 * (SessioniTab) e dal dettaglio contratto (ContractSessioniTab).
 * Stato dal SSoT FE: label da EVENT_STATUS_LABELS (mai underscore in UI, task #14 G7.8-bis),
 * penali (Cancellato_Tardivo/No_Show) in rose — occupano il credito, non sono performance.
 */

import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { EventHydrated } from "@/hooks/useAgenda";
import { EVENT_STATUS_LABELS, type EventStatus } from "@/types/api";

function statoBadgeClass(stato: string): string {
  if (stato === "Completato")
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400";
  if (stato === "Cancellato")
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  if (stato === "Cancellato_Tardivo" || stato === "No_Show")
    return "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300";
  return "";
}

export function EventsTable({ events }: { events: EventHydrated[] }) {
  const sorted = [...events].sort(
    (a, b) => b.data_inizio.getTime() - a.data_inizio.getTime()
  );

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data</TableHead>
            <TableHead>Titolo</TableHead>
            <TableHead>Categoria</TableHead>
            <TableHead>Stato</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((e) => (
            <TableRow key={e.id}>
              <TableCell className="tabular-nums">
                {format(e.data_inizio, "dd MMM yyyy HH:mm", { locale: it })}
              </TableCell>
              <TableCell className="font-medium">{e.titolo ?? "—"}</TableCell>
              <TableCell>
                <Badge variant="outline">{e.categoria}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="secondary" className={statoBadgeClass(e.stato)}>
                  {EVENT_STATUS_LABELS[e.stato as EventStatus] ?? e.stato}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
