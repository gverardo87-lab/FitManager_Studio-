// src/components/dashboard/OrphanEventsSheet.tsx
/**
 * G9.7.2/B6 (ADR-024 D-RECUPERO-ESPLICITO) — worklist dei PT senza contratto.
 *
 * Ogni riga porta l'AZIONE (D-SEGNALE-AZIONE): select dei contratti APERTI del cliente
 * (già sul wire, con crediti residui) + «Assegna» inline via useAssegnaContratto.
 * Mai limbo invisibile: se il cliente non ha contratti aperti la riga lo DICE.
 */

"use client";

import { useState } from "react";
import { Link2, Unlink, Calendar, User, Loader2, CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useOrphanEvents } from "@/hooks/useDashboard";
import { useAssegnaContratto } from "@/hooks/useAgenda";
import type { OrphanEventItem } from "@/types/api";

function formatEventDate(iso: string): string {
  const d = new Date(iso.replace(" ", "T"));
  return d.toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" });
}

function formatEventTime(iso: string): string {
  const d = new Date(iso.replace(" ", "T"));
  return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

interface OrphanEventsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function OrphanRow({ item }: { item: OrphanEventItem }) {
  const assegna = useAssegnaContratto();
  const [selectedId, setSelectedId] = useState<string>("");
  const assegnabili = item.contratti_aperti.filter((c) => c.crediti_residui > 0);

  return (
    <div className="rounded-lg border p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {item.titolo ?? "Seduta PT"}
          </p>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            <span>
              {formatEventDate(item.data_inizio)} · {formatEventTime(item.data_inizio)}
            </span>
            <User className="h-3 w-3" />
            <span className="truncate">
              {item.cliente_nome} {item.cliente_cognome ?? ""}
            </span>
          </div>
        </div>
        <Badge variant="outline" className="shrink-0 text-[10px]">
          {item.stato}
        </Badge>
      </div>

      {assegnabili.length > 0 ? (
        <div className="flex items-center gap-2">
          <Select value={selectedId} onValueChange={setSelectedId}>
            <SelectTrigger className="h-8 flex-1 text-xs">
              <SelectValue placeholder="Scegli contratto..." />
            </SelectTrigger>
            <SelectContent>
              {assegnabili.map((c) => (
                <SelectItem key={c.id} value={c.id.toString()}>
                  {c.tipo_pacchetto ?? `Contratto #${c.id}`} · {c.crediti_residui} crediti
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="sm"
            className="h-8"
            disabled={!selectedId || assegna.isPending}
            onClick={() =>
              assegna.mutate({ eventId: item.id, idContratto: parseInt(selectedId, 10) })
            }
          >
            {assegna.isPending ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Link2 className="mr-1 h-3.5 w-3.5" />
            )}
            Assegna
          </Button>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">
          Nessun contratto aperto con crediti: creane uno dal profilo del cliente.
        </p>
      )}
    </div>
  );
}

export function OrphanEventsSheet({ open, onOpenChange }: OrphanEventsSheetProps) {
  const { data, isLoading } = useOrphanEvents(open);
  const items = data?.items ?? [];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col overflow-hidden sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Unlink className="h-5 w-5 text-amber-500" />
            Sedute senza contratto
          </SheetTitle>
          <SheetDescription>
            Queste sedute PT non scalano crediti. Assegnale a un contratto aperto del
            cliente per farle contare.
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="min-h-0 flex-1 pr-3">
          <div className="space-y-3 py-2">
            {isLoading &&
              [0, 1, 2].map((i) => <Skeleton key={i} className="h-24 w-full rounded-lg" />)}

            {!isLoading && items.length === 0 && (
              <div className="flex flex-col items-center gap-2 py-10 text-center">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                <p className="text-sm font-medium">Nessuna seduta orfana</p>
                <p className="text-xs text-muted-foreground">
                  Tutte le sedute PT sono agganciate a un contratto.
                </p>
              </div>
            )}

            {items.map((item) => (
              <OrphanRow key={item.id} item={item} />
            ))}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
