// src/components/contracts/payment-plan/PaymentHistory.tsx
"use client";

/**
 * Storico Pagamenti — timeline cronologica per rata (PARZIALE e SALDATA).
 * Presentazionale puro (split G8.4 F5): il collapsible "Mostra altri N" è stato
 * UI locale; le cifre (importi, totale versato/previsto) sono campi del backend.
 */

import { useState } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import { CheckCircle2 } from "lucide-react";

import type { Rate } from "@/types/api";
import { formatCurrency } from "@/lib/format";

export function PaymentHistory({ rate }: { rate: Rate }) {
  const [expanded, setExpanded] = useState(false);
  const payments = rate.pagamenti;
  const isSaldata = rate.stato === "SALDATA";

  // Mostra max 2 pagamenti, espandibile
  const visible = expanded ? payments : payments.slice(0, 2);
  const hiddenCount = payments.length - 2;

  return (
    <div className="mt-2 space-y-1">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {payments.length === 1 ? "Pagamento" : `${payments.length} Pagamenti`}
      </p>
      <div className="space-y-0.5">
        {visible.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
          >
            <CheckCircle2 className={`h-3 w-3 shrink-0 ${
              isSaldata ? "text-emerald-500" : "text-amber-500"
            }`} />
            <span className="tabular-nums font-semibold">
              {formatCurrency(p.importo)}
            </span>
            {p.metodo && (
              <span className="text-muted-foreground/70">{p.metodo}</span>
            )}
            <span className="ml-auto shrink-0">
              {format(parseISO(p.data_pagamento), "dd MMM yyyy", { locale: it })}
            </span>
          </div>
        ))}
      </div>
      {hiddenCount > 0 && !expanded && (
        <button
          type="button"
          className="text-[11px] text-primary hover:underline"
          onClick={() => setExpanded(true)}
        >
          Mostra altr{hiddenCount === 1 ? "o" : "i"} {hiddenCount}
        </button>
      )}
      {/* Totale versato / previsto */}
      {payments.length > 1 && (
        <div className="flex items-center gap-1 border-t pt-1 text-[11px] text-muted-foreground">
          <span>Totale versato:</span>
          <span className="tabular-nums font-semibold">
            {formatCurrency(rate.importo_saldato)} / {formatCurrency(rate.importo_previsto)}
          </span>
        </div>
      )}
    </div>
  );
}
