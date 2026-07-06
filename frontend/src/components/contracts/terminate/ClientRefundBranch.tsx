// src/components/contracts/terminate/ClientRefundBranch.tsx
"use client";

/**
 * Ramo CREDITO_CLIENTE del dialog Termina (ADR-020): rimborso EDITABILE + metodo (solo se > 0).
 * Presentazionale CONTROLLATO: props in, callback out — lo stato e il gating vivono nel container.
 */

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCurrency } from "@/lib/format";
import { METHOD_LABEL, PAYMENT_METHODS } from "./payment-methods";

interface ClientRefundBranchProps {
  creditoCliente: number;
  rimborso: string;
  onRimborsoChange: (value: string) => void;
  rimborsoNum: number;
  walletResto: number;
  metodo: string;
  onMetodoChange: (value: string) => void;
}

export function ClientRefundBranch({
  creditoCliente,
  rimborso,
  onRimborsoChange,
  rimborsoNum,
  walletResto,
  metodo,
  onMetodoChange,
}: ClientRefundBranchProps) {
  return (
    <div className="space-y-2.5">
      <div className="space-y-1.5">
        <Label className="text-xs font-medium">Importo da rimborsare</Label>
        <Input
          type="number"
          min={0}
          max={creditoCliente}
          step="0.01"
          value={rimborso}
          onChange={(e) => onRimborsoChange(e.target.value)}
          aria-label="Importo da rimborsare"
        />
        <p className="text-[11px] text-muted-foreground">
          Massimo {formatCurrency(creditoCliente)}.
          {walletResto > 0.009
            ? ` Il non rimborsato (${formatCurrency(walletResto)}) resta come credito del cliente, da erogare quando vuoi.`
            : ""}
        </p>
      </div>
      {rimborsoNum > 0.009 ? (
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Metodo di rimborso</Label>
          <Select value={metodo} onValueChange={onMetodoChange}>
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
    </div>
  );
}
