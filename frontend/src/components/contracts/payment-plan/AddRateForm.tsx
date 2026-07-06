// src/components/contracts/payment-plan/AddRateForm.tsx
"use client";

/**
 * Form aggiunta rata manuale fuori piano (caso C del Piano Pagamenti).
 * Presentazionale controllato (split G8.4 F5): la mutation arriva dal container,
 * i valori del form (importo, scadenza, descrizione) sono stato UI locale.
 */

import { useState } from "react";
import { format, parseISO } from "date-fns";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DatePicker } from "@/components/ui/date-picker";
import { useCreateRate } from "@/hooks/useRates";

export function AddRateForm({
  contractId,
  contractScadenza,
  createMutation,
  onClose,
}: {
  contractId: number;
  contractScadenza?: string;
  createMutation: ReturnType<typeof useCreateRate>;
  onClose: () => void;
}) {
  const [importo, setImporto] = useState("");
  const [descrizione, setDescrizione] = useState("");
  const [dataScadenza, setDataScadenza] = useState<Date | undefined>(undefined);

  const handleCreate = () => {
    if (!dataScadenza || !importo) return;

    createMutation.mutate(
      {
        id_contratto: contractId,
        importo_previsto: parseFloat(importo),
        data_scadenza: format(dataScadenza, "yyyy-MM-dd"),
        descrizione: descrizione.trim() || undefined,
      },
      { onSuccess: onClose }
    );
  };

  return (
    <div className="space-y-3 rounded-lg border border-dashed bg-zinc-50/50 p-4 dark:bg-zinc-800/30">
      <p className="text-sm font-semibold">Nuova Rata Manuale</p>
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">Importo</Label>
          <Input
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0,00"
            value={importo}
            onChange={(e) => setImporto(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Data Scadenza</Label>
          <DatePicker
            value={dataScadenza}
            onChange={setDataScadenza}
            placeholder="Seleziona..."
            maxDate={contractScadenza ? parseISO(contractScadenza) : undefined}
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Descrizione</Label>
          <Input
            placeholder="es. Rata extra"
            value={descrizione}
            onChange={(e) => setDescrizione(e.target.value)}
          />
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={handleCreate}
          disabled={createMutation.isPending || !importo || !dataScadenza}
          className="flex-1"
        >
          {createMutation.isPending && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          Crea Rata
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onClose}
          disabled={createMutation.isPending}
        >
          Annulla
        </Button>
      </div>
    </div>
  );
}
