// src/components/agenda/AssegnaContrattoBanner.tsx
"use client";

/**
 * G9.7.2/B6 (ADR-024 D-RECUPERO-ESPLICITO) — banner di recupero per il PT orfano.
 *
 * Visibile nel dettaglio evento quando la seduta è PT, ha un cliente e NON ha contratto:
 * etichetta onesta + azione inline «Assegna» sui contratti APERTI del cliente.
 * Il riaggancio passa SOLO da POST /events/{id}/assegna-contratto (fence ADR-023 intatto).
 */

import { useState } from "react";
import { AlertTriangle, Link2, Loader2 } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useClientContracts } from "@/hooks/useContracts";
import { useAssegnaContratto } from "@/hooks/useAgenda";

interface AssegnaContrattoBannerProps {
  eventId: number;
  idCliente: number;
  onAssigned?: () => void;
}

export function AssegnaContrattoBanner({ eventId, idCliente, onAssigned }: AssegnaContrattoBannerProps) {
  const { data: contractsData } = useClientContracts(idCliente);
  const assegna = useAssegnaContratto();
  const [selectedId, setSelectedId] = useState<string>("");

  // Solo contratti APERTI: il backend rifiuta comunque i chiusi (400), qui non li offriamo proprio
  const aperti = (contractsData?.items ?? []).filter((c) => !c.chiuso);

  const handleAssign = () => {
    if (!selectedId) return;
    assegna.mutate(
      { eventId, idContratto: parseInt(selectedId, 10) },
      { onSuccess: () => onAssigned?.() },
    );
  };

  return (
    <Alert>
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="space-y-2">
        <p>
          Seduta <strong>senza contratto</strong>: non scala crediti. Assegnala a un
          contratto del cliente per farla contare.
        </p>
        {aperti.length > 0 ? (
          <div className="flex items-center gap-2">
            <Select value={selectedId} onValueChange={setSelectedId}>
              <SelectTrigger className="h-8 flex-1 text-xs">
                <SelectValue placeholder="Scegli contratto..." />
              </SelectTrigger>
              <SelectContent>
                {aperti.map((c) => (
                  <SelectItem key={c.id} value={c.id.toString()}>
                    {c.tipo_pacchetto ?? `Contratto #${c.id}`} ·{" "}
                    {(c.crediti_totali ?? 0) - c.crediti_usati} crediti residui
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              type="button"
              size="sm"
              className="h-8"
              disabled={!selectedId || assegna.isPending}
              onClick={handleAssign}
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
            Il cliente non ha contratti aperti: creane uno, oppure la seduta resterà senza
            fatto economico.
          </p>
        )}
      </AlertDescription>
    </Alert>
  );
}
