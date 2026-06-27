// src/components/contracts/TerminateContractDialog.tsx
"use client";

/**
 * Terminazione anticipata di un contratto (G7.3 + ADR-018) — dialog conferma con anteprima conguaglio.
 *
 * Posizionamento (ADR-014, SPEC §0/§4): il software PROPONE un conguaglio calcolato col metodo standard
 * pro-rata sedute; NON afferma che sia l'obbligo legale del trainer. Il `messaggio` del backend porta il
 * framing di proposta (load-bearing). Settlement BILATERALE (ADR-018): se il cliente ha ricevuto più
 * servizio di quanto versato (`esito === "CREDITO_TRAINER"`), il trainer DEVE scegliere esplicitamente se
 * incassare il saldo a suo favore (importo editabile) o rinunciarvi — mai un write-off implicito.
 *
 * Zero calcoli finanziari nel frontend: esito, importi e azioni permesse arrivano dal backend.
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useSettlementPreview, useTerminateContract } from "@/hooks/useContracts";
import type { ContractTerminate } from "@/types/api";
import { formatCurrency } from "@/lib/format";

const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;
const METHOD_LABEL: Record<string, string> = { CONTANTI: "Contanti", POS: "POS", BONIFICO: "Bonifico" };

type Azione = "" | "INCASSA_ORA" | "RINUNCIA_ESPRESSA";

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
  const [metodo, setMetodo] = useState("CONTANTI");        // rimborso (ramo cliente)
  const [azione, setAzione] = useState<Azione>("");        // ramo trainer
  const [incasso, setIncasso] = useState("");              // importo editabile INCASSA_ORA
  const [metodoPag, setMetodoPag] = useState("CONTANTI");  // metodo incasso (INCASSA_ORA)
  const [nota, setNota] = useState("");                    // motivo (RINUNCIA_ESPRESSA)

  // Reset ad ogni apertura (dialog condiviso fra righe diverse).
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setMetodo("CONTANTI");
      setAzione("");
      setIncasso("");
      setMetodoPag("CONTANTI");
      setNota("");
    }
  }

  const data = preview.data;
  const needsMetodo = data?.metodo_rimborso_richiesto ?? false;        // ramo CREDITO_CLIENTE
  const trainerCredit = data?.esito === "CREDITO_TRAINER";             // ramo CREDITO_TRAINER
  const creditoTrainer = data?.credito_trainer ?? 0;
  const incassoNum = parseFloat(incasso);
  const incassoValido = !isNaN(incassoNum) && incassoNum >= 0 && incassoNum <= creditoTrainer + 0.001;

  // Scelta obbligatoria nel ramo trainer (mai default implicito di rinuncia).
  const trainerSceltaValida =
    !trainerCredit ||
    (azione === "INCASSA_ORA" && incassoValido) ||
    (azione === "RINUNCIA_ESPRESSA" && nota.trim().length > 0);

  const canSubmit =
    contractId !== null && !!data && !preview.isLoading && !terminate.isPending && trainerSceltaValida;

  const pickIncassaOra = () => {
    setAzione("INCASSA_ORA");
    if (data) setIncasso(data.credito_trainer.toFixed(2));
  };

  const handleTerminate = () => {
    if (contractId === null || !data) return;
    let payload: Partial<ContractTerminate> = {};
    if (needsMetodo) {
      payload = { metodo_rimborso: metodo };
    } else if (trainerCredit) {
      payload =
        azione === "INCASSA_ORA"
          ? { azione_credito_trainer: "INCASSA_ORA", importo_incassato: incassoNum, metodo_pagamento: metodoPag }
          : { azione_credito_trainer: "RINUNCIA_ESPRESSA", note: nota.trim() };
    }
    terminate.mutate(
      { contractId, ...payload },
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
              {trainerCredit ? (
                <>
                  <dt className="font-medium text-emerald-700 dark:text-emerald-300">Saldo a tuo favore</dt>
                  <dd className="text-right font-medium tabular-nums text-emerald-700 dark:text-emerald-300">
                    {formatCurrency(creditoTrainer)}
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

            {/* Ramo CREDITO_CLIENTE: metodo rimborso */}
            {needsMetodo ? (
              <div className="space-y-1.5">
                <Label className="text-xs font-medium">Metodo di rimborso</Label>
                <Select value={metodo} onValueChange={setMetodo}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PAYMENT_METHODS.map((m) => (
                      <SelectItem key={m} value={m}>{METHOD_LABEL[m]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}

            {/* Ramo CREDITO_TRAINER: scelta esplicita obbligatoria (ADR-018) */}
            {trainerCredit ? (
              <div className="space-y-2.5">
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant={azione === "INCASSA_ORA" ? "default" : "outline"}
                    size="sm"
                    onClick={pickIncassaOra}
                  >
                    Incassa ora e chiudi
                  </Button>
                  <Button
                    type="button"
                    variant={azione === "RINUNCIA_ESPRESSA" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setAzione("RINUNCIA_ESPRESSA")}
                  >
                    Rinuncia e chiudi
                  </Button>
                </div>

                {azione === "INCASSA_ORA" ? (
                  <div className="space-y-2">
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Importo da incassare</Label>
                      <Input
                        type="number"
                        min={0}
                        max={creditoTrainer}
                        step="0.01"
                        value={incasso}
                        onChange={(e) => setIncasso(e.target.value)}
                        aria-label="Importo da incassare"
                      />
                      <p className="text-[11px] text-muted-foreground">
                        Massimo {formatCurrency(creditoTrainer)}. Puoi ridurlo: la differenza viene abbuonata al cliente.
                      </p>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Metodo di pagamento</Label>
                      <Select value={metodoPag} onValueChange={setMetodoPag}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PAYMENT_METHODS.map((m) => (
                            <SelectItem key={m} value={m}>{METHOD_LABEL[m]}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                ) : null}

                {azione === "RINUNCIA_ESPRESSA" ? (
                  <div className="space-y-1.5">
                    <Label className="text-xs font-medium">Motivo della rinuncia (obbligatorio)</Label>
                    <Textarea
                      value={nota}
                      onChange={(e) => setNota(e.target.value)}
                      placeholder="Es. sconto concordato col cliente in fase di chiusura."
                      rows={2}
                    />
                  </div>
                ) : null}
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
