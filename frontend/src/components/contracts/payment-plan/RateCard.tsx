// src/components/contracts/payment-plan/RateCard.tsx
"use client";

/**
 * Rate Card — design premium con dropdown azioni (Modifica/Revoca/Elimina).
 * Presentazionale controllato (split G8.4 F5): le azioni risalgono al container
 * via callback (onEdit/onDelete/onUnpay). `usePayRate` resta qui: un'istanza per
 * card, così `isPending` non è condiviso tra form di pagamento aperti in parallelo.
 */

import { useState } from "react";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Banknote,
  CalendarClock,
  MoreVertical,
  Pencil,
  Trash2,
  Undo2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { usePayRate } from "@/hooks/useRates";
import { PayRateForm } from "./PayRateForm";
import { PaymentHistory } from "./PaymentHistory";
import type { Rate } from "@/types/api";
import { formatCurrency } from "@/lib/format";

export function RateCard({
  rate,
  onEdit,
  onDelete,
  onUnpay,
}: {
  rate: Rate;
  onEdit: (rate: Rate) => void;
  onDelete: (rate: Rate) => void;
  onUnpay: (rate: Rate) => void;
}) {
  const payMutation = usePayRate();
  const [showPayForm, setShowPayForm] = useState(false);

  const isSaldata = rate.stato === "SALDATA";
  const isOverdue = rate.is_scaduta;
  const overdueDays = rate.giorni_ritardo;

  const cardClasses = isOverdue
    ? "rounded-lg border-2 border-red-200 bg-red-50/50 p-4 dark:border-red-900/60 dark:bg-red-950/20"
    : isSaldata
      ? "rounded-lg border border-emerald-200/60 bg-emerald-50/30 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/10"
      : "rounded-lg border bg-white p-4 dark:bg-zinc-900";

  return (
    <div className={cardClasses}>
      <div className="flex items-center justify-between gap-3">
        {/* ── Icona + info ── */}
        <div className="flex items-center gap-3 min-w-0">
          <StatusIcon isSaldata={isSaldata} isOverdue={isOverdue} />
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">
              {rate.descrizione ?? `Rata #${rate.id}`}
            </p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <CalendarClock className={`h-3 w-3 ${
                isOverdue ? "text-red-500" : "text-muted-foreground"
              }`} />
              <p className={`text-xs ${
                isOverdue
                  ? "font-semibold text-red-600 dark:text-red-400"
                  : "text-muted-foreground"
              }`}>
                {format(parseISO(rate.data_scadenza), "dd MMMM yyyy", {
                  locale: it,
                })}
              </p>
            </div>
            {/* ── Alert scaduta intelligente: giorni di ritardo ── */}
            {isOverdue && (
              <p className={`text-[11px] font-bold mt-0.5 ${
                overdueDays > 30
                  ? "text-red-700 dark:text-red-400"
                  : "text-amber-700 dark:text-amber-400"
              }`}>
                Scaduta da {overdueDays} giorn{overdueDays === 1 ? "o" : "i"}
              </p>
            )}
          </div>
        </div>

        {/* ── Importo + badge + azioni ── */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="text-right">
            <p className={`text-sm font-bold tabular-nums ${
              isSaldata ? "text-emerald-700 dark:text-emerald-400" : ""
            }`}>
              {formatCurrency(rate.importo_previsto)}
            </p>
            {rate.importo_saldato > 0 && !isSaldata && (
              <p className="text-[11px] text-muted-foreground tabular-nums">
                Versato {formatCurrency(rate.importo_saldato)}
              </p>
            )}
          </div>
          <RateStatusBadge stato={rate.stato} isOverdue={isOverdue} />

          {/* ── Dropdown azioni ── */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreVertical className="h-4 w-4" />
                <span className="sr-only">Azioni rata</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(rate)}>
                <Pencil className="mr-2 h-4 w-4" />
                Modifica
              </DropdownMenuItem>
              {rate.importo_saldato > 0 ? (
                <DropdownMenuItem
                  onClick={() => onUnpay(rate)}
                  className="text-destructive focus:text-destructive"
                >
                  <Undo2 className="mr-2 h-4 w-4" />
                  Revoca Pagamento
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={() => onDelete(rate)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Elimina
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* ── Storico pagamenti (PARZIALE e SALDATA) ── */}
      {rate.pagamenti.length > 0 && (
        <PaymentHistory rate={rate} />
      )}

      {/* ── Azione pagamento ── */}
      {!isSaldata && !showPayForm && (
        <Button
          variant={isOverdue ? "default" : "outline"}
          size="sm"
          className={`mt-3 w-full ${
            isOverdue
              ? "bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600"
              : ""
          }`}
          onClick={() => setShowPayForm(true)}
        >
          <Banknote className="mr-2 h-4 w-4" />
          {isOverdue
            ? `Paga Ora — ${overdueDays}g di ritardo`
            : "Segna come Pagata"
          }
        </Button>
      )}

      {/* ── Form pagamento inline ── */}
      {!isSaldata && showPayForm && (
        <PayRateForm
          rate={rate}
          payMutation={payMutation}
          onCancel={() => setShowPayForm(false)}
        />
      )}
    </div>
  );
}

// ── Icona stato ──

function StatusIcon({ isSaldata, isOverdue }: { isSaldata: boolean; isOverdue: boolean }) {
  if (isSaldata) {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
        <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
      </div>
    );
  }
  if (isOverdue) {
    return (
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100 animate-pulse dark:bg-red-900/30">
        <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
      </div>
    );
  }
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
      <Clock className="h-4 w-4 text-amber-600 dark:text-amber-400" />
    </div>
  );
}

// ── Badge stato rata ──

function RateStatusBadge({
  stato,
  isOverdue,
}: {
  stato: string;
  isOverdue: boolean;
}) {
  if (stato === "SALDATA") {
    return (
      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400">
        Saldata
      </Badge>
    );
  }
  if (isOverdue) {
    return (
      <Badge variant="destructive" className="animate-pulse">
        Scaduta
      </Badge>
    );
  }
  if (stato === "PARZIALE") {
    return (
      <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400">
        Parziale
      </Badge>
    );
  }
  return (
    <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400">
      Pendente
    </Badge>
  );
}
