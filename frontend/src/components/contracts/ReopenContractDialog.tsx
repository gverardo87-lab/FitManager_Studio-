// src/components/contracts/ReopenContractDialog.tsx
"use client";

/**
 * Riapertura di un contratto chiuso (G7.4 → G8.1/ADR-019: ricalcola-e-instrada, NON-distruttiva).
 *
 * reopen NON cancella più la cassa di terminazione: le scritture restano (fatti datati), il contratto
 * RICALCOLA il residuo (net-aware) e instrada/annulla i ledger non-cash (storno, receivable, wallet).
 * Il dialog mostra l'impatto pieno dal `reopen-preview` (cosa RESTA / cosa si ANNULLA) e, se esiste un
 * rinnovo ancora attivo a valle, lo segnala perché l'utente decida (mai azione silenziosa, D-PROPONE).
 */

import { Loader2, RotateCcw, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useReopenContract, useReopenPreview } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import type { Contract } from "@/types/api";

interface ReopenContractDialogProps {
  contract: Contract | null;
  clientLabel: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ReopenContractDialog({
  contract,
  clientLabel,
  open,
  onOpenChange,
}: ReopenContractDialogProps) {
  const reopen = useReopenContract();
  const preview = useReopenPreview(open && contract ? contract.id : null);
  const data = preview.data;

  const handleReopen = () => {
    if (contract === null) return;
    reopen.mutate(contract.id, { onSuccess: () => onOpenChange(false) });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="h-4.5 w-4.5 text-sky-600 dark:text-sky-400" />
            Riapri contratto — {clientLabel}
          </DialogTitle>
          <DialogDescription>
            Annulla la chiusura e riporta il contratto ad aperto. La cassa già registrata NON viene
            cancellata: il residuo si ricalcola di conseguenza.
          </DialogDescription>
        </DialogHeader>

        {preview.isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : preview.isError ? (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            Impossibile calcolare l&apos;impatto della riapertura. Riprova.
          </div>
        ) : data ? (
          <div className="space-y-3">
            {/* Messaggio riepilogo (framing ADR-019: la cassa resta) */}
            <div className="rounded-md border border-sky-300 bg-sky-50 p-3 text-sm text-sky-900 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-200">
              {data.messaggio}
            </div>

            {/* Cosa resta / cosa si annulla */}
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {data.rimborso_che_resta > 0.009 ? (
                <li>
                  • Il rimborso di{" "}
                  <span className="font-medium text-foreground">{formatCurrency(data.rimborso_che_resta)}</span>{" "}
                  già erogato <span className="font-medium">resta</span> (diventa rimborso sul contratto).
                </li>
              ) : null}
              {data.incasso_che_resta > 0.009 ? (
                <li>
                  • L&apos;incasso di conguaglio di{" "}
                  <span className="font-medium text-foreground">{formatCurrency(data.incasso_che_resta)}</span>{" "}
                  <span className="font-medium">resta</span> (diventa pagamento sul contratto).
                </li>
              ) : null}
              <li>
                • Il residuo del contratto si ricalcola a{" "}
                <span className="font-medium text-foreground">{formatCurrency(data.residuo_dopo)}</span>.
              </li>
              {data.rate_da_ripristinare > 0 ? (
                <li>
                  • {data.rate_da_ripristinare}{" "}
                  {data.rate_da_ripristinare === 1 ? "rata viene ripristinata" : "rate vengono ripristinate"}.
                </li>
              ) : null}
              {data.receivable_da_annullare > 0 ? (
                <li>• {data.receivable_da_annullare} credito differito viene annullato.</li>
              ) : null}
              {data.wallet_da_annullare > 0 ? (
                <li>• {data.wallet_da_annullare} credito a wallet del cliente viene annullato.</li>
              ) : null}
              {data.wallet_erogato_riassorbito > 0.009 ? (
                <li>
                  • Il cliente ha già riavuto{" "}
                  <span className="font-medium text-foreground">
                    {formatCurrency(data.wallet_erogato_riassorbito)}
                  </span>{" "}
                  dal wallet: <span className="font-medium">torna dovuto</span> sul contratto riaperto.
                </li>
              ) : null}
            </ul>

            {/* Avviso rinnovo vivo (S5, D-PROPONE) */}
            {data.ha_rinnovo_vivo ? (
              <div className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  Attenzione: esiste un <span className="font-medium">rinnovo ancora attivo</span>
                  {data.id_rinnovo_vivo != null ? ` (contratto #${data.id_rinnovo_vivo})` : ""}. Riaprendo
                  questo contratto potresti avere due contratti attivi sullo stesso periodo: verifica prima
                  di procedere.
                </span>
              </div>
            ) : null}
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={reopen.isPending}>
            Annulla
          </Button>
          <Button onClick={handleReopen} disabled={contract === null || reopen.isPending}>
            {reopen.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Riapri contratto
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
