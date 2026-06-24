// src/components/contracts/TerminateContractDialog.tsx
"use client";

/**
 * Terminazione anticipata di un contratto (G7.3) — dialog conferma con anteprima conguaglio.
 *
 * Posizionamento (ADR-014, SPEC_G7.3 §0/§4): il software PROPONE un conguaglio calcolato col metodo
 * standard pro-rata sedute; NON afferma che sia l'obbligo legale del trainer. Il `messaggio` del
 * backend porta il framing di proposta (load-bearing): mai "da rimborsare", sempre "calcolato,
 * verifica con le condizioni del contratto". Il default pro_sedute non esegue mai silenziosamente:
 * la preview mostra l'esito, l'utente ratifica.
 *
 * Zero calcoli finanziari nel frontend: l'esito e gli importi arrivano dal backend (settlement-preview).
 */

import { useState } from "react";
import { Loader2, AlertTriangle, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useSettlementPreview, useTerminateContract } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";

const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;

interface TerminateContractDialogProps {
  contractId: number | null;
  clientLabel: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TerminateContractDialog({
  contractId,
  clientLabel,
  open,
  onOpenChange,
}: TerminateContractDialogProps) {
  const preview = useSettlementPreview(open ? contractId : null);
  const terminate = useTerminateContract();
  const [metodo, setMetodo] = useState("CONTANTI");

  // Reset del metodo a ogni apertura (dialog condiviso fra righe diverse).
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) setMetodo("CONTANTI");
  }

  const data = preview.data;
  const needsMetodo = data?.metodo_rimborso_richiesto ?? false;
  const canSubmit =
    contractId !== null && !!data && !preview.isLoading && !terminate.isPending;

  const handleTerminate = () => {
    if (contractId === null || !data) return;
    terminate.mutate(
      { contractId, ...(needsMetodo ? { metodo_rimborso: metodo } : {}) },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RefreshCcw className="h-4.5 w-4.5 text-rose-600 dark:text-rose-400" />
            Termina contratto — {clientLabel}
          </DialogTitle>
          <DialogDescription>
            Interrompe il contratto in anticipo. Il conguaglio sotto è una proposta calcolata col
            metodo pro-rata sulle sedute erogate — non un importo dovuto per legge.
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
            Impossibile calcolare il conguaglio. Riprova.
          </div>
        ) : data ? (
          <div className="space-y-3">
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
              <dt className="text-muted-foreground">Servizio reso</dt>
              <dd className="text-right tabular-nums">{formatCurrency(data.valore_servizio_reso)}</dd>
              {data.importo_rimborso > 0 ? (
                <>
                  <dt className="font-medium text-rose-700 dark:text-rose-300">Rimborso al cliente</dt>
                  <dd className="text-right font-medium tabular-nums text-rose-700 dark:text-rose-300">
                    {formatCurrency(data.importo_rimborso)}
                  </dd>
                </>
              ) : null}
              {data.quota_da_stornare > 0 ? (
                <>
                  <dt className="text-muted-foreground">Residuo azzerato</dt>
                  <dd className="text-right tabular-nums">{formatCurrency(data.quota_da_stornare)}</dd>
                </>
              ) : null}
            </dl>

            {/* Metodo rimborso (solo se l'esito è un rimborso) */}
            {needsMetodo ? (
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Metodo di rimborso</Label>
                <Select value={metodo} onValueChange={setMetodo}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PAYMENT_METHODS.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m === "CONTANTI" ? "Contanti" : m === "POS" ? "POS" : "Bonifico"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}
          </div>
        ) : null}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={terminate.isPending}
          >
            Annulla
          </Button>
          <Button variant="destructive" onClick={handleTerminate} disabled={!canSubmit}>
            {terminate.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Termina contratto
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
