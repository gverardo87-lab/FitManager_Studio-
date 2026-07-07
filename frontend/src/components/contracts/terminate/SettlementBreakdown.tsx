// src/components/contracts/terminate/SettlementBreakdown.tsx
"use client";

/**
 * Anteprima conguaglio del dialog Termina (G8.4 F5) — presentazionale puro, sola lettura.
 * Ogni cifra è un campo del backend formattato (R-SSOT-FE): messaggio-proposta (framing ADR-014),
 * breakdown numerico, avviso prenotate-escluse (D2).
 */

import { formatCurrency } from "@/lib/format";
import type { ContractSettlementPreview } from "@/types/api";

export function SettlementBreakdown({ data }: { data: ContractSettlementPreview }) {
  const trainerCredit = data.esito === "CREDITO_TRAINER";

  return (
    <>
      {/* Messaggio proposta (framing §0/§4) */}
      <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
        {data.messaggio}
      </div>

      {/* Breakdown numerico (sola lettura, dal backend) */}
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
        <dt className="text-muted-foreground">Sedute erogate</dt>
        <dd className="text-right tabular-nums">
          {data.sedute_erogate}
          {data.sedute_totali != null ? ` / ${data.sedute_totali}` : ""}
        </dd>
        {/* F3.e (G7.8-bis): penali contabilizzate nel conguaglio — conteggio SEPARATO, mai
            sommato alle erogate a video (audit conteggi separati vere/penali) */}
        {data.sedute_penali > 0 ? (
          <>
            <dt className="text-amber-700 dark:text-amber-300">Sedute penali (contabilizzate)</dt>
            <dd className="text-right tabular-nums text-amber-700 dark:text-amber-300">
              {data.sedute_penali}
            </dd>
          </>
        ) : null}
        <dt className="text-muted-foreground">Servizio reso</dt>
        <dd className="text-right tabular-nums">{formatCurrency(data.valore_servizio_reso)}</dd>
        {data.importo_rimborso > 0 ? (
          <>
            <dt className="font-medium text-rose-700 dark:text-rose-300">Credito del cliente</dt>
            <dd className="text-right font-medium tabular-nums text-rose-700 dark:text-rose-300">
              {formatCurrency(data.importo_rimborso)}
            </dd>
          </>
        ) : null}
        {trainerCredit ? (
          <>
            <dt className="font-medium text-emerald-700 dark:text-emerald-300">Saldo a tuo favore</dt>
            <dd className="text-right font-medium tabular-nums text-emerald-700 dark:text-emerald-300">
              {formatCurrency(data.credito_trainer)}
            </dd>
          </>
        ) : data.quota_da_stornare > 0 ? (
          <>
            <dt className="text-muted-foreground">Residuo azzerato</dt>
            <dd className="text-right tabular-nums">{formatCurrency(data.quota_da_stornare)}</dd>
          </>
        ) : null}
      </dl>

      {/* D2: avviso prenotate-escluse — solo se ci sono PT prenotate ma non svolte */}
      {data.sedute_prenotate > 0 ? (
        <p className="text-[11px] text-muted-foreground">
          Le {data.sedute_prenotate} sedute prenotate ma non ancora svolte non riducono il conguaglio:
          si basa solo sulle sedute già erogate.
        </p>
      ) : null}
    </>
  );
}
