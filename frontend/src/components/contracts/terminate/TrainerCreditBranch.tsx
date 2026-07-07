// src/components/contracts/terminate/TrainerCreditBranch.tsx
"use client";

/**
 * Ramo CREDITO_TRAINER del dialog Termina (ADR-018 D-SCELTA): scelta ESPLICITA obbligatoria fra
 * Incassa ora / A credito / Rinuncia — mai un default implicito (il gate 422 del backend resta
 * l'autorità). Presentazionale CONTROLLATO: `azione` e i valori vivono nel container.
 *
 * F3.a/F3.d (G8.4): la raccomandazione (`azioneConsigliata` dal backend, advisory F3.c) è SOLO
 * visiva — badge «Consigliato» + enfasi ring sul bottone suggerito; nessuna pre-selezione
 * (all'apertura nessun bottone è `aria-pressed`). Il SELEZIONATO ha marcatore non-cromatico
 * (icona Check) oltre al variant filled — mai il solo colore. Il check segna la SELEZIONE, non
 * il suggerimento: un check sul suggerito-non-scelto sembrerebbe una scelta già fatta.
 */

import { Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { formatCurrency } from "@/lib/format";
import { METHOD_LABEL, PAYMENT_METHODS } from "./payment-methods";

export type AzioneCreditoTrainer = "" | "INCASSA_ORA" | "RINUNCIA_ESPRESSA" | "A_CREDITO";

interface TrainerCreditBranchProps {
  azione: AzioneCreditoTrainer;
  azioneConsigliata: string | null;
  onPickIncassaOra: () => void;
  onPickACredito: () => void;
  onPickRinuncia: () => void;
  creditoTrainer: number;
  incasso: string;
  onIncassoChange: (value: string) => void;
  metodoPag: string;
  onMetodoPagChange: (value: string) => void;
  nota: string;
  onNotaChange: (value: string) => void;
}

export function TrainerCreditBranch({
  azione,
  azioneConsigliata,
  onPickIncassaOra,
  onPickACredito,
  onPickRinuncia,
  creditoTrainer,
  incasso,
  onIncassoChange,
  metodoPag,
  onMetodoPagChange,
  nota,
  onNotaChange,
}: TrainerCreditBranchProps) {
  return (
    <div className="space-y-2.5">
      <div
        role="group"
        aria-label="Scelta per il saldo a tuo favore"
        className="grid grid-cols-1 gap-2 sm:grid-cols-3"
      >
        <ChoiceButton
          selected={azione === "INCASSA_ORA"}
          suggested={azioneConsigliata === "INCASSA_ORA"}
          onClick={onPickIncassaOra}
        >
          Incassa ora e chiudi
        </ChoiceButton>
        <ChoiceButton
          selected={azione === "A_CREDITO"}
          suggested={azioneConsigliata === "A_CREDITO"}
          onClick={onPickACredito}
        >
          Metti a credito e chiudi
        </ChoiceButton>
        <ChoiceButton
          selected={azione === "RINUNCIA_ESPRESSA"}
          suggested={false /* la rinuncia non è MAI il suggerito (F3.a) */}
          onClick={onPickRinuncia}
        >
          Rinuncia e chiudi
        </ChoiceButton>
      </div>

      {azione === "A_CREDITO" ? (
        <p className="text-[11px] text-muted-foreground">
          Il cliente resta debitore di {formatCurrency(creditoTrainer)}: lo incassi quando paga, dalla
          worklist &quot;Crediti da incassare&quot;. Il contratto si chiude subito (residuo a zero).
        </p>
      ) : null}

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
              onChange={(e) => onIncassoChange(e.target.value)}
              aria-label="Importo da incassare"
            />
            <p className="text-[11px] text-muted-foreground">
              Massimo {formatCurrency(creditoTrainer)}. Puoi ridurlo: la differenza viene abbuonata al cliente.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Metodo di pagamento</Label>
            <Select value={metodoPag} onValueChange={onMetodoPagChange}>
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
            onChange={(e) => onNotaChange(e.target.value)}
            placeholder="Es. sconto concordato col cliente in fase di chiusura."
            rows={2}
          />
        </div>
      ) : null}
    </div>
  );
}

/** Bottone-scelta del gruppo: `aria-pressed` = stato REALE (mai pressed all'apertura, AC-G84-4);
 * selezione marcata anche col Check (non-cromatico); il suggerito porta badge «Consigliato» + ring. */
function ChoiceButton({
  selected,
  suggested,
  onClick,
  children,
}: {
  selected: boolean;
  suggested: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Button
      type="button"
      variant={selected ? "default" : "outline"}
      size="sm"
      className={suggested && !selected ? "ring-1 ring-emerald-400/70 dark:ring-emerald-500/50" : undefined}
      onClick={onClick}
      aria-pressed={selected}
    >
      {selected ? <Check className="mr-1 h-3.5 w-3.5 shrink-0" aria-hidden="true" /> : null}
      <span className="truncate">{children}</span>
      {suggested ? (
        <span className="ml-1.5 shrink-0 rounded-full border border-emerald-300 bg-emerald-50 px-1.5 py-px text-[9px] font-semibold uppercase tracking-wide text-emerald-700 dark:border-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
          Consigliato
        </span>
      ) : null}
    </Button>
  );
}
