// src/components/contracts/ContractDettagliTab.tsx
"use client";

/**
 * Tab "Dettagli" del dettaglio contratto: info read-only (pacchetto, prezzo, date, stato, note).
 * Presentazionale puro — ogni cifra è un campo del backend formattato (R-SSOT-FE).
 */

import type { ReactNode } from "react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";
import { ContractLifecycleBadge } from "@/lib/contract-status";
import type { ContractWithRates } from "@/types/api";

export function ContractDettagliTab({ contract }: { contract: ContractWithRates }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Info contratto */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Informazioni contratto</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <DetailRow label="Tipo pacchetto" value={contract.tipo_pacchetto ?? "—"} />
          <DetailRow label="Prezzo totale" value={formatCurrency(contract.prezzo_totale ?? 0)} />
          <DetailRow
            label="Acconto"
            value={contract.acconto > 0 ? formatCurrency(contract.acconto) : "—"}
          />
          <DetailRow
            label="Crediti totali"
            value={contract.crediti_totali != null ? `${contract.crediti_totali}` : "—"}
          />
        </CardContent>
      </Card>

      {/* Date e stato */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Date e stato</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <DetailRow
            label="Data inizio"
            value={contract.data_inizio
              ? format(new Date(contract.data_inizio + "T00:00:00"), "dd MMMM yyyy", { locale: it })
              : "—"}
          />
          <DetailRow
            label="Data scadenza"
            value={contract.data_scadenza
              ? format(new Date(contract.data_scadenza + "T00:00:00"), "dd MMMM yyyy", { locale: it })
              : "Senza scadenza"}
          />
          <DetailRow label="Stato" value={<ContractLifecycleBadge lifecycle={contract.lifecycle} />} />
          {contract.note && (
            <div className="pt-2">
              <p className="text-muted-foreground">Note</p>
              <p className="mt-1 whitespace-pre-line font-medium">{contract.note}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
