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
 * CONTAINER (G8.4 F5): TUTTO lo stato e la gating-logic vivono qui; i figli `terminate/*`
 * (SettlementBreakdown, ClientRefundBranch, TrainerCreditBranch) sono presentazionali controllati.
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
import { Skeleton } from "@/components/ui/skeleton";
import { useSettlementPreview, useTerminateContract } from "@/hooks/useContracts";
import type { ContractTerminate } from "@/types/api";
import { SettlementBreakdown } from "./terminate/SettlementBreakdown";
import { ClientRefundBranch } from "./terminate/ClientRefundBranch";
import { TrainerCreditBranch, type AzioneCreditoTrainer } from "./terminate/TrainerCreditBranch";

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
  const [rimborso, setRimborso] = useState("");            // importo editabile rimborso (ramo cliente, G8.1)
  const [prevPreviewKey, setPrevPreviewKey] = useState<number | null>(null); // sync default rimborso
  const [azione, setAzione] = useState<AzioneCreditoTrainer>("");  // ramo trainer
  const [incasso, setIncasso] = useState("");              // importo editabile INCASSA_ORA
  const [metodoPag, setMetodoPag] = useState("CONTANTI");  // metodo incasso (INCASSA_ORA)
  const [nota, setNota] = useState("");                    // motivo (RINUNCIA_ESPRESSA)

  // Reset ad ogni apertura (dialog condiviso fra righe diverse).
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setMetodo("CONTANTI");
      setRimborso("");
      setAzione("");
      setIncasso("");
      setMetodoPag("CONTANTI");
      setNota("");
    }
  }

  const data = preview.data;
  const isRimborso = data?.metodo_rimborso_richiesto ?? false;         // ramo CREDITO_CLIENTE (rimborso)
  const trainerCredit = data?.esito === "CREDITO_TRAINER";             // ramo CREDITO_TRAINER
  const creditoTrainer = data?.credito_trainer ?? 0;
  const creditoCliente = data?.importo_rimborso ?? 0;                  // cap del rimborso editabile
  const incassoNum = parseFloat(incasso);
  const incassoValido = !isNaN(incassoNum) && incassoNum >= 0 && incassoNum <= creditoTrainer + 0.001;
  const rimborsoNum = parseFloat(rimborso);
  const rimborsoValido = !isNaN(rimborsoNum) && rimborsoNum >= 0 && rimborsoNum <= creditoCliente + 0.001;
  const walletResto = Math.max(creditoCliente - (isNaN(rimborsoNum) ? 0 : rimborsoNum), 0);

  // Default del rimborso = pieno: sync quando arriva il preview CREDITO_CLIENTE (guard render-safe;
  // gcTime 0 → il preview passa per undefined ad ogni apertura, quindi il default si ri-applica).
  const previewKey = isRimborso ? creditoCliente : null;
  if (previewKey !== prevPreviewKey) {
    setPrevPreviewKey(previewKey);
    setRimborso(previewKey != null ? previewKey.toFixed(2) : "");
  }

  // Scelta obbligatoria nel ramo trainer (mai default implicito di rinuncia).
  const trainerSceltaValida =
    !trainerCredit ||
    (azione === "INCASSA_ORA" && incassoValido) ||
    (azione === "RINUNCIA_ESPRESSA" && nota.trim().length > 0) ||
    azione === "A_CREDITO";

  // Ramo cliente: rimborso valido + metodo solo se rimborso > 0 (ADR-020).
  const clienteSceltaValida =
    !isRimborso || (rimborsoValido && (rimborsoNum <= 0.009 || metodo.length > 0));

  const canSubmit =
    contractId !== null && !!data && !preview.isLoading && !terminate.isPending &&
    trainerSceltaValida && clienteSceltaValida;

  const pickIncassaOra = () => {
    setAzione("INCASSA_ORA");
    if (data) setIncasso(data.credito_trainer.toFixed(2));
  };

  const handleTerminate = () => {
    if (contractId === null || !data) return;
    let payload: Partial<ContractTerminate> = {};
    if (isRimborso) {
      payload = { importo_rimborso: rimborsoNum };
      if (rimborsoNum > 0.009) payload.metodo_rimborso = metodo;
    } else if (trainerCredit) {
      if (azione === "INCASSA_ORA") {
        payload = { azione_credito_trainer: "INCASSA_ORA", importo_incassato: incassoNum, metodo_pagamento: metodoPag };
      } else if (azione === "RINUNCIA_ESPRESSA") {
        payload = { azione_credito_trainer: "RINUNCIA_ESPRESSA", note: nota.trim() };
      } else {
        payload = { azione_credito_trainer: "A_CREDITO" };
      }
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
            <SettlementBreakdown data={data} />

            {/* Ramo CREDITO_CLIENTE: rimborso EDITABILE + metodo (solo se rimborso > 0) — ADR-020 */}
            {isRimborso ? (
              <ClientRefundBranch
                creditoCliente={creditoCliente}
                rimborso={rimborso}
                onRimborsoChange={setRimborso}
                rimborsoNum={rimborsoNum}
                walletResto={walletResto}
                metodo={metodo}
                onMetodoChange={setMetodo}
              />
            ) : null}

            {/* Ramo CREDITO_TRAINER: scelta esplicita obbligatoria (ADR-018) */}
            {trainerCredit ? (
              <TrainerCreditBranch
                azione={azione}
                azioneConsigliata={data.azione_consigliata ?? null}
                onPickIncassaOra={pickIncassaOra}
                onPickACredito={() => setAzione("A_CREDITO")}
                onPickRinuncia={() => setAzione("RINUNCIA_ESPRESSA")}
                creditoTrainer={creditoTrainer}
                incasso={incasso}
                onIncassoChange={setIncasso}
                metodoPag={metodoPag}
                onMetodoPagChange={setMetodoPag}
                nota={nota}
                onNotaChange={setNota}
              />
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
