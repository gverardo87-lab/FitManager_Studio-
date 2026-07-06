// src/components/contracts/payment-plan/FinancialBreakdown.tsx
"use client";

/**
 * Breakdown finanziario del piano rate + Mismatch Alert + banner rate scadute.
 * Presentazionale puro, sola lettura (R-SSOT-FE): ogni cifra è un campo del
 * backend formattato — zero calcoli client.
 */

import { AlertCircle, AlertTriangle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { ContractWithRates } from "@/types/api";
import { formatCurrency } from "@/lib/format";

export function FinancialBreakdown({ contract }: { contract: ContractWithRates }) {
  // Tutti i valori dal backend — zero calcoli frontend
  const overdueCount = contract.rate_scadute;
  const prezzoTotale = contract.prezzo_totale ?? 0;
  const versato = contract.totale_versato;
  const rimborsato = contract.totale_rimborsato ?? 0;  // issue B: il rimborso riconcilia prezzo−netto=residuo
  const daRateizzare = contract.importo_da_rateizzare;
  const sommaRatePendenti = contract.somma_rate_pendenti;
  const mancante = contract.importo_disallineamento;
  const hasMismatch = !contract.piano_allineato;

  return (
    <>
      {/* ── Breakdown Finanziario ── */}
      <div className="rounded-lg border bg-zinc-50/80 p-4 dark:bg-zinc-800/30">
        <table className="w-full text-sm">
          <tbody>
            <tr>
              <td className="py-0.5 text-muted-foreground">Prezzo totale</td>
              <td className="py-0.5 text-right font-semibold tabular-nums">
                {formatCurrency(prezzoTotale)}
              </td>
            </tr>
            {versato > 0 && (
              <tr>
                <td className="py-0.5 text-muted-foreground">Totale versato</td>
                <td className="py-0.5 text-right font-semibold tabular-nums text-emerald-700 dark:text-emerald-400">
                  &minus;{formatCurrency(versato)}
                </td>
              </tr>
            )}
            {rimborsato > 0.009 && (
              <tr>
                <td className="py-0.5 text-muted-foreground">Rimborsato</td>
                <td className="py-0.5 text-right font-semibold tabular-nums text-rose-700 dark:text-rose-400">
                  +{formatCurrency(rimborsato)}
                </td>
              </tr>
            )}
            <tr className="border-t">
              <td className="pt-1 font-medium">Ancora da incassare</td>
              <td className="pt-1 text-right font-bold tabular-nums">
                {formatCurrency(daRateizzare)}
              </td>
            </tr>
            <tr>
              <td className="py-0.5 text-muted-foreground">Rate pendenti</td>
              <td className={`py-0.5 text-right font-semibold tabular-nums ${
                hasMismatch
                  ? "text-amber-700 dark:text-amber-400"
                  : "text-emerald-700 dark:text-emerald-400"
              }`}>
                {formatCurrency(sommaRatePendenti)}
                {!hasMismatch && " ✓"}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Mismatch Alert — linguaggio chiaro */}
      {hasMismatch && (
        <Alert variant={mancante > 0 ? "destructive" : "default"}>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Piano rate da allineare</AlertTitle>
          <AlertDescription>
            {mancante > 0
              ? `Le rate pendenti coprono ${formatCurrency(sommaRatePendenti)} su ${formatCurrency(daRateizzare)} da incassare. Mancano ${formatCurrency(mancante)}.`
              : `Le rate pendenti superano il dovuto di ${formatCurrency(Math.abs(mancante))}. Aggiusta gli importi.`
            }
            {" "}Rigenera il piano per allinearlo.
          </AlertDescription>
        </Alert>
      )}

      {/* Alert banner per rate scadute */}
      {overdueCount > 0 && (
        <div className="flex items-center gap-2.5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-900/50 dark:bg-red-950/30">
          <AlertCircle className="h-4.5 w-4.5 shrink-0 text-red-600 dark:text-red-400" />
          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            {overdueCount} rat{overdueCount === 1 ? "a scaduta" : "e scadute"} — azione richiesta
          </p>
        </div>
      )}
    </>
  );
}
