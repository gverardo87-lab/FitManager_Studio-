// src/components/contracts/IncassaCreditoDialog.tsx
"use client";

/**
 * Incassa credito differito (G7.10) — dialog di cassa sul receivable `crediti_terminazione`.
 *
 * Il credito a favore del trainer creato da una terminazione A_CREDITO ("il cliente paga dopo").
 * Vive FUORI da residuo() del contratto (che resta CHIUSO): incassarlo genera una ENTRATA
 * INCASSO_CONGUAGLIO_CONTRATTO e fa crescere totale_versato. Supporta l'incasso PARZIALE.
 * UX clonata da IncassaResiduoDialog (G6). Cap UX = residuo del credito; il backend è l'autorità (422).
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
import { useIncassaCredito } from "@/hooks/useContracts";
import { formatCurrency, toISOLocal } from "@/lib/format";

const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;

interface IncassaCreditoDialogProps {
  contractId: number | null;
  creditoId: number | null;
  residuo: number;
  clientLabel: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function IncassaCreditoDialog({
  contractId,
  creditoId,
  residuo,
  clientLabel,
  open,
  onOpenChange,
}: IncassaCreditoDialogProps) {
  const incassaCredito = useIncassaCredito();
  const [importo, setImporto] = useState(residuo);
  const [metodo, setMetodo] = useState("CONTANTI");
  const [dataPagamento, setDataPagamento] = useState<Date>(() => new Date());

  // Reset a OGNI apertura (dialog condiviso fra righe diverse): l'importo segue il credito corrente.
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
    contractId !== null && creditoId !== null && !incassaCredito.isPending && importo > 0 && !exceedsResiduo;

  const handleIncassa = () => {
    if (contractId === null || creditoId === null) return;
    incassaCredito.mutate(
      {
        contractId,
        creditoId,
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
            Incassa credito — {clientLabel}
          </DialogTitle>
          <DialogDescription>
            Registra l&apos;incasso del credito differito (anche parziale). Il movimento entra nel libro
            mastro come entrata legata al contratto; il contratto resta chiuso.
          </DialogDescription>
        </DialogHeader>

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
            disabled={incassaCredito.isPending}
          >
            Annulla
          </Button>
          <Button onClick={handleIncassa} disabled={!canSubmit}>
            {incassaCredito.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isPartial
              ? `Incassa ${formatCurrency(importo)} (parziale)`
              : `Incassa ${formatCurrency(importo)}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
