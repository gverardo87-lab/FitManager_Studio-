// src/components/contracts/ContractHistoryTab.tsx
"use client";

/**
 * Tab "Storico" del dettaglio contratto (G8.1.1 / F5 + F6) — livello CRM aziendale.
 *
 * Due storici complementari, mai fusi:
 * - F5 — Movimenti di cassa: ledger unificato dei CashMovement del contratto (acconto, rate,
 *   rimborsi USCITA, conguagli ENTRATA) con segno + saldo netto progressivo. Legge `contract.movimenti`
 *   (già nel dettaglio). L'erogazione wallet (id_contratto=None) NON è qui — è cassa a livello cliente.
 * - F6 — Stato & attività: timeline curata dello stato di vita (creazione, terminazione, riapertura,
 *   saldo, transizioni) da `GET /contracts/{id}/history`.
 */

import { useMemo } from "react";
import {
  Sparkles,
  Lock,
  RotateCcw,
  CheckCircle2,
  Activity,
  Pencil,
  Trash2,
  Undo2,
  ArrowDownLeft,
  ArrowUpRight,
  Wallet,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatShortDate, formatDateTime } from "@/lib/format";
import { useContractHistory } from "@/hooks/useContracts";
import type {
  ContractWithRates,
  ContractMovementItem,
  ContractHistoryEvent,
} from "@/types/api";

const CATEGORIA_LABEL: Record<string, string> = {
  ACCONTO_CONTRATTO: "Acconto",
  PAGAMENTO_RATA: "Pagamento rata",
  INCASSO_CONGUAGLIO_CONTRATTO: "Conguaglio incassato",
  RIMBORSO_CONTRATTO: "Rimborso",
};

const EVENT_STYLE: Record<
  ContractHistoryEvent["tipo"],
  { Icon: typeof Sparkles; className: string }
> = {
  creato: { Icon: Sparkles, className: "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400" },
  terminato: { Icon: Lock, className: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400" },
  riaperto: { Icon: RotateCcw, className: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
  saldato: { Icon: CheckCircle2, className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" },
  stato: { Icon: Activity, className: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300" },
  modificato: { Icon: Pencil, className: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" },
  eliminato: { Icon: Trash2, className: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
  ripristinato: { Icon: Undo2, className: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300" },
};

function categoriaLabel(m: ContractMovementItem): string {
  if (m.categoria && CATEGORIA_LABEL[m.categoria]) return CATEGORIA_LABEL[m.categoria];
  return m.categoria ?? (m.tipo === "ENTRATA" ? "Entrata" : "Uscita");
}

export function ContractHistoryTab({ contract }: { contract: ContractWithRates }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <CashLedgerCard movimenti={contract.movimenti} />
      <StatusTimelineCard contractId={contract.id} />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// F5 — Movimenti di cassa (ledger con saldo netto progressivo)
// ════════════════════════════════════════════════════════════

function CashLedgerCard({ movimenti }: { movimenti: ContractMovementItem[] }) {
  // Saldo netto progressivo: ENTRATA +, USCITA − (cronologico asc, come da backend).
  const rows = useMemo(() => {
    let saldo = 0;
    return movimenti.map((m) => {
      const segno = m.tipo === "ENTRATA" ? 1 : -1;
      saldo = Math.round((saldo + segno * m.importo) * 100) / 100;
      return { m, saldo };
    });
  }, [movimenti]);

  const netto = rows.length > 0 ? rows[rows.length - 1].saldo : 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Wallet className="h-4 w-4 text-primary" aria-hidden="true" />
          Movimenti di cassa
        </CardTitle>
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Netto incassato</p>
          <p className="text-base font-bold tabular-nums">{formatCurrency(netto)}</p>
        </div>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Nessun movimento di cassa registrato.
          </p>
        ) : (
          <ul className="divide-y">
            {rows.map(({ m, saldo }) => {
              const isEntrata = m.tipo === "ENTRATA";
              const Sign = isEntrata ? ArrowDownLeft : ArrowUpRight;
              return (
                <li key={m.id} className="flex items-center gap-3 py-2.5">
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      isEntrata
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                        : "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400"
                    }`}
                  >
                    <Sign className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{categoriaLabel(m)}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatShortDate(m.data_effettiva)}
                      {m.metodo ? <> · {m.metodo}</> : null}
                      {m.note ? <> · {m.note}</> : null}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-sm font-semibold tabular-nums ${
                        isEntrata ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                      }`}
                    >
                      {isEntrata ? "+" : "−"}
                      {formatCurrency(m.importo)}
                    </p>
                    <p className="text-[11px] tabular-nums text-muted-foreground">
                      saldo {formatCurrency(saldo)}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// F6 — Stato & attività (timeline curata, recente in cima)
// ════════════════════════════════════════════════════════════

function StatusTimelineCard({ contractId }: { contractId: number }) {
  const { data, isLoading } = useContractHistory(contractId);

  // Più recente in cima (il backend ordina cronologico asc).
  const events = useMemo(() => (data ? [...data].reverse() : []), [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Activity className="h-4 w-4 text-primary" aria-hidden="true" />
          Stato &amp; attività
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : events.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Nessuna attività registrata.
          </p>
        ) : (
          <ol className="space-y-4">
            {events.map((e, idx) => {
              const { Icon, className } = EVENT_STYLE[e.tipo] ?? EVENT_STYLE.stato;
              return (
                <li key={`${e.data}-${idx}`} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${className}`}>
                      <Icon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    {idx < events.length - 1 ? <span className="mt-1 w-px flex-1 bg-border" /> : null}
                  </div>
                  <div className="min-w-0 flex-1 pb-1">
                    <p className="text-sm font-medium">{e.titolo}</p>
                    {e.dettaglio ? (
                      <p className="text-xs text-muted-foreground">{e.dettaglio}</p>
                    ) : null}
                    <p className="mt-0.5 text-[11px] text-muted-foreground/80">{formatDateTime(e.data)}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
