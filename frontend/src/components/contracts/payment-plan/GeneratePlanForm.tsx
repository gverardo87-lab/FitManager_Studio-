// src/components/contracts/payment-plan/GeneratePlanForm.tsx
"use client";

/**
 * Caso A del Piano Pagamenti: nessuna rata → form per generare il piano automatico.
 * Presentazionale controllato (split G8.4 F5): la mutation arriva dal container,
 * lo stato del form (numero rate, frequenza, data prima rata) è UI locale.
 */

import { useState } from "react";
import { format, parseISO } from "date-fns";
import { Loader2, Plus } from "lucide-react";

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
import { useGeneratePaymentPlan } from "@/hooks/useRates";
import type { ContractWithRates } from "@/types/api";
import { PLAN_FREQUENCIES } from "@/types/api";
import { formatCurrency } from "@/lib/format";

export function GeneratePlanForm({
  contract,
  generateMutation,
}: {
  contract: ContractWithRates;
  generateMutation: ReturnType<typeof useGeneratePaymentPlan>;
}) {
  // Importo dal backend: prezzo - acconto - rate saldate (unica fonte di verita')
  const remaining = contract.importo_da_rateizzare;

  const [numeroRate, setNumeroRate] = useState(3);
  const [frequenza, setFrequenza] = useState("MENSILE");
  const [dataPrimaRata, setDataPrimaRata] = useState<Date | undefined>(
    undefined
  );

  const handleGenerate = () => {
    if (!dataPrimaRata) return;

    generateMutation.mutate({
      contractId: contract.id,
      importo_da_rateizzare: remaining,
      numero_rate: numeroRate,
      data_prima_rata: format(dataPrimaRata, "yyyy-MM-dd"),
      frequenza,
    });
  };

  return (
    <div className="space-y-5 rounded-lg border border-dashed p-6">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Plus className="h-5 w-5" />
        <p className="font-medium">Nessun piano rate configurato</p>
      </div>
      <p className="text-sm text-muted-foreground/70">
        Genera un piano automatico oppure aggiungi le rate manualmente.
      </p>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Importo da rateizzare</Label>
          <Input
            value={formatCurrency(remaining)}
            disabled
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="numero_rate">Numero Rate</Label>
          <Input
            id="numero_rate"
            type="number"
            min={1}
            max={60}
            value={numeroRate}
            onChange={(e) => setNumeroRate(parseInt(e.target.value, 10) || 1)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Data Prima Rata</Label>
          <DatePicker
            value={dataPrimaRata}
            onChange={setDataPrimaRata}
            placeholder="Seleziona data..."
            maxDate={contract.data_scadenza ? parseISO(contract.data_scadenza) : undefined}
          />
        </div>
        <div className="space-y-2">
          <Label>Frequenza</Label>
          <Select value={frequenza} onValueChange={setFrequenza}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PLAN_FREQUENCIES.map((f) => (
                <SelectItem key={f} value={f}>
                  {f.charAt(0) + f.slice(1).toLowerCase()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Button
        onClick={handleGenerate}
        disabled={generateMutation.isPending || !dataPrimaRata}
        className="w-full"
      >
        {generateMutation.isPending && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        )}
        Genera Piano Pagamenti
      </Button>
    </div>
  );
}
