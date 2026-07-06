// src/components/contracts/payment-plan/PayRateForm.tsx
"use client";

/**
 * Form pagamento inline della rata (quick buttons Tutto/50%, metodo, data).
 * Presentazionale controllato (split G8.4 F5): la mutation arriva da RateCard,
 * importo/metodo/data sono stato UI locale del form. Il cap sull'importo è
 * validazione input-local sul `importo_residuo` del backend — zero money-math.
 */

import { useState } from "react";
import { format, parseISO } from "date-fns";
import { Loader2 } from "lucide-react";

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
import { DatePicker } from "@/components/ui/date-picker";
import { usePayRate } from "@/hooks/useRates";
import type { Rate } from "@/types/api";
import { PAYMENT_METHODS } from "@/types/api";
import { formatCurrency } from "@/lib/format";

export function PayRateForm({
  rate,
  payMutation,
  onCancel,
}: {
  rate: Rate;
  payMutation: ReturnType<typeof usePayRate>;
  onCancel: () => void;
}) {
  const residuo = rate.importo_residuo;
  const [importo, setImporto] = useState(residuo);
  const [metodo, setMetodo] = useState("CONTANTI");

  // Smart default: scadenza passata → usa data_scadenza, futura → oggi
  const scadenza = parseISO(rate.data_scadenza);
  const oggi = new Date();
  const smartDefault = scadenza <= oggi ? scadenza : oggi;
  const [dataPagamento, setDataPagamento] = useState<Date>(smartDefault);

  const isPartial = importo > 0 && importo < residuo - 0.01;
  const exceedsResiduo = importo > residuo + 0.01;
  const canPay = !payMutation.isPending && importo > 0 && !exceedsResiduo;

  const handlePay = () => {
    payMutation.mutate(
      {
        rateId: rate.id,
        importo,
        metodo,
        data_pagamento: format(dataPagamento, "yyyy-MM-dd"),
      },
      { onSuccess: onCancel }
    );
  };

  return (
    <div className="mt-3 space-y-3 rounded-lg border bg-zinc-50/80 p-4 dark:bg-zinc-800/50">
      {/* Quick buttons */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-full border px-3 py-1 text-xs font-medium hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          onClick={() => setImporto(residuo)}
        >
          Tutto ({formatCurrency(residuo)})
        </button>
        {residuo >= 2 && (
          <button
            type="button"
            className="rounded-full border px-3 py-1 text-xs font-medium hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            onClick={() => setImporto(Math.round(residuo / 2 * 100) / 100)}
          >
            50%
          </button>
        )}
        <span className="ml-auto text-[11px] text-muted-foreground">
          Residuo: {formatCurrency(residuo)}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Importo</Label>
          <Input
            type="number"
            step="0.01"
            min="0.01"
            max={residuo}
            value={importo}
            onChange={(e) => setImporto(parseFloat(e.target.value) || 0)}
          />
          {exceedsResiduo && (
            <p className="text-[11px] text-destructive">
              Supera il residuo di {formatCurrency(residuo)}
            </p>
          )}
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Metodo</Label>
          <Select value={metodo} onValueChange={setMetodo}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAYMENT_METHODS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Data Pagamento</Label>
          <DatePicker
            value={dataPagamento}
            onChange={(d) => { if (d) setDataPagamento(d); }}
          />
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={handlePay}
          disabled={!canPay}
          className="flex-1"
        >
          {payMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          {isPartial ? `Paga ${formatCurrency(importo)} (parziale)` : `Paga ${formatCurrency(importo)}`}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCancel}
          disabled={payMutation.isPending}
        >
          Annulla
        </Button>
      </div>
    </div>
  );
}
