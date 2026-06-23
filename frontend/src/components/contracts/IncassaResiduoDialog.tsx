// src/components/contracts/IncassaResiduoDialog.tsx
"use client";

/**
 * Incassa residuo diretto (G6) — dialog di cassa ENTRATA legata al contratto SENZA rata.
 *
 * Azione per i contratti SCADUTI aperti (SOSPESO/ESAURITO) il cui residuo non è più
 * rateizzabile (bucket "da incassare scaduto"). UX clonata da PayRateForm:
 * quick "Tutto (€residuo)" cap-limitato, importo/metodo/data, validazione max = residuo.
 *
 * Zero calcoli finanziari nel frontend oltre al cap UX: il backend è l'autorità (422 se
 * l'importo supera il residuo). Date via toISOLocal (mai toISOString → perde il fuso).
 */

import { useState } from "react";
import { Loader2, HandCoins } from "lucide-react";

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
import { DatePicker } from "@/components/ui/date-picker";
import { useIncassaResiduo } from "@/hooks/useContracts";
import { formatCurrency, toISOLocal } from "@/lib/format";

const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;

interface IncassaResiduoDialogProps {
  contractId: number | null;
  residuo: number;
  clientLabel: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function IncassaResiduoDialog({
  contractId,
  residuo,
  clientLabel,
  open,
  onOpenChange,
}: IncassaResiduoDialogProps) {
  const incassaResiduo = useIncassaResiduo();
  const [importo, setImporto] = useState(residuo);
  const [metodo, setMetodo] = useState("CONTANTI");
  const [dataPagamento, setDataPagamento] = useState<Date>(() => new Date());

  // Reset dei campi a OGNI apertura (transizione open false→true): l'importo deve seguire
  // il residuo del contratto corrente — questo dialog è condiviso fra righe diverse, quindi
  // un reset legato al solo contractId non basta. Pattern React "adjust state on prop change".
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setImporto(residuo);
      setMetodo("CONTANTI");
      setDataPagamento(new Date());
    }
  }

  const isPartial = importo > 0 && importo < residuo - 0.01;
  const exceedsResiduo = importo > residuo + 0.01;
  const canSubmit =
    contractId !== null && !incassaResiduo.isPending && importo > 0 && !exceedsResiduo;

  const handleIncassa = () => {
    if (contractId === null) return;
    incassaResiduo.mutate(
      {
        contractId,
        importo,
        metodo,
        data_pagamento: toISOLocal(dataPagamento).slice(0, 10),
      },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HandCoins className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
            Incassa residuo — {clientLabel}
          </DialogTitle>
          <DialogDescription>
            Registra direttamente l&apos;incasso del residuo dovuto, senza creare una rata.
            Il movimento entra nel libro mastro come entrata legata al contratto.
          </DialogDescription>
        </DialogHeader>

        {/* Quick buttons + residuo */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-full border px-3 py-1 text-xs font-medium transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800"
            onClick={() => setImporto(residuo)}
          >
            Tutto ({formatCurrency(residuo)})
          </button>
          {residuo >= 2 && (
            <button
              type="button"
              className="rounded-full border px-3 py-1 text-xs font-medium transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800"
              onClick={() => setImporto(Math.round((residuo / 2) * 100) / 100)}
            >
              50%
            </button>
          )}
          <span className="ml-auto text-[11px] text-muted-foreground">
            Residuo: {formatCurrency(residuo)}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
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
                    {m === "CONTANTI" ? "Contanti" : m === "POS" ? "POS" : "Bonifico"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">Data incasso</Label>
            <DatePicker
              value={dataPagamento}
              onChange={(d) => {
                if (d) setDataPagamento(d);
              }}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={incassaResiduo.isPending}
          >
            Annulla
          </Button>
          <Button onClick={handleIncassa} disabled={!canSubmit}>
            {incassaResiduo.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isPartial
              ? `Incassa ${formatCurrency(importo)} (parziale)`
              : `Incassa ${formatCurrency(importo)}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
