// src/components/contracts/terminate/TrainerCreditBranch.tsx
"use client";

/**
 * Ramo CREDITO_TRAINER del dialog Termina (ADR-018 D-SCELTA): scelta ESPLICITA obbligatoria fra
 * Incassa ora / A credito / Rinuncia — mai un default implicito (il gate 422 del backend resta
 * l'autorità). Presentazionale CONTROLLATO: `azione` e i valori vivono nel container.
 */

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
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <Button
          type="button"
          variant={azione === "INCASSA_ORA" ? "default" : "outline"}
          size="sm"
          onClick={onPickIncassaOra}
        >
          Incassa ora e chiudi
        </Button>
        <Button
          type="button"
          variant={azione === "A_CREDITO" ? "default" : "outline"}
          size="sm"
          onClick={onPickACredito}
        >
          Metti a credito e chiudi
        </Button>
        <Button
          type="button"
          variant={azione === "RINUNCIA_ESPRESSA" ? "default" : "outline"}
          size="sm"
          onClick={onPickRinuncia}
        >
          Rinuncia e chiudi
        </Button>
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
