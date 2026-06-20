// src/components/dashboard/ContractsToPlanSheet.tsx
/**
 * Sheet per contratti da pianificare (SPEC_RINNOVO §B).
 *
 * Mostra contratti aperti con residuo positivo e ZERO rate — denaro dovuto
 * che l'aging report (Rate-first) non vede. Per ciascuno:
 * - Info cliente + pacchetto + scadenza
 * - Residuo da mettere a rata (evidenziato)
 * - CTA "Definisci piano" → /contratti/{id} (tab Piano Pagamenti = default)
 */

"use client";

import Link from "next/link";
import {
  CalendarClock,
  CheckCircle2,
  User,
  Calendar,
  ArrowRight,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useContractsToPlan } from "@/hooks/useDashboard";
import { formatCurrency, formatShortDate } from "@/lib/format";

// ════════════════════════════════════════════════════════════

interface ContractsToPlanSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ContractsToPlanSheet({ open, onOpenChange }: ContractsToPlanSheetProps) {
  const { data, isLoading } = useContractsToPlan(open);
  const items = data?.items ?? [];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <CalendarClock aria-hidden="true" className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <SheetTitle>Contratti da pianificare</SheetTitle>
              <SheetDescription>
                Denaro dovuto senza piano rate — da mettere a scadenza
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <Separator />

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3 p-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-28 w-full rounded-lg" />
            ))}
          </div>
        )}

        {/* Empty */}
        {!isLoading && items.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <CheckCircle2 aria-hidden="true" className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              Tutto pianificato!
            </p>
            <p className="text-xs text-muted-foreground">
              Ogni contratto con residuo ha un piano rate
            </p>
          </div>
        )}

        {/* Lista contratti */}
        {!isLoading && items.length > 0 && (
          <ScrollArea className="min-h-0 flex-1 -mx-1 px-1">
            <div className="space-y-3 pb-4">
              {items.map((item) => (
                <div
                  key={item.contract_id}
                  className="rounded-lg border p-4 transition-shadow hover:shadow-sm"
                >
                  {/* Header: cliente */}
                  <div className="mb-2 flex items-center gap-2">
                    <User aria-hidden="true" className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-sm font-semibold">
                      {item.client_nome} {item.client_cognome}
                    </span>
                  </div>

                  {/* Pacchetto + scadenza */}
                  <div className="mb-3 flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <CalendarClock aria-hidden="true" className="h-3 w-3" />
                      <span>{item.tipo_pacchetto || "Contratto"}</span>
                    </div>
                    {item.data_scadenza && (
                      <div className="flex items-center gap-1">
                        <Calendar aria-hidden="true" className="h-3 w-3" />
                        <span>Scade il {formatShortDate(item.data_scadenza)}</span>
                      </div>
                    )}
                  </div>

                  {/* Residuo da pianificare */}
                  <div className="mb-3">
                    <p className="text-[10px] uppercase text-muted-foreground">
                      Da mettere a rata
                    </p>
                    <p className="text-lg font-bold tabular-nums text-amber-600 dark:text-amber-400">
                      {formatCurrency(item.importo_residuo)}
                    </p>
                  </div>

                  {/* CTA */}
                  <Link href={`/contratti/${item.contract_id}?from=dashboard`}>
                    <Button
                      size="sm"
                      className="h-8 w-full gap-1.5 text-xs font-medium"
                    >
                      Definisci piano
                      <ArrowRight aria-hidden="true" className="h-3 w-3" />
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  );
}
