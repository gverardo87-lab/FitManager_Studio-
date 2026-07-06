// src/components/contracts/PaymentPlanTab.tsx
"use client";

/**
 * Tab Piano Pagamenti — Advanced Billing Engine.
 *
 * Tre stati:
 * A) Nessuna rata → form per generare piano automatico
 * B) Rate esistenti → lista card premium con:
 *    - Dropdown Modifica/Elimina (nascosto su SALDATE)
 *    - Alert scadenze overdue
 *    - Financial Mismatch Alert (somma rate ≠ importo da saldare)
 * C) Bottone "+ Aggiungi Rata" per rate manuali fuori piano
 *
 * Container (split G8.4 F5): stato di orchestrazione, mutation e gating vivono
 * qui; i blocchi presentazionali sono in ./payment-plan/*.
 */

import { useState } from "react";
import { Loader2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useGeneratePaymentPlan,
  useCreateRate,
  useDeleteRate,
} from "@/hooks/useRates";
import { RateEditDialog } from "./RateEditDialog";
import { RateUnpayDialog } from "./RateUnpayDialog";
import { GeneratePlanForm } from "./payment-plan/GeneratePlanForm";
import { FinancialBreakdown } from "./payment-plan/FinancialBreakdown";
import { RateCard } from "./payment-plan/RateCard";
import { AddRateForm } from "./payment-plan/AddRateForm";
import type { Rate, ContractWithRates } from "@/types/api";
import { formatCurrency } from "@/lib/format";

interface PaymentPlanTabProps {
  contract: ContractWithRates;
}

// ════════════════════════════════════════════════════════════
// Componente principale
// ════════════════════════════════════════════════════════════

export function PaymentPlanTab({ contract }: PaymentPlanTabProps) {
  const rates = contract.rate ?? [];
  const hasRates = rates.length > 0;
  const generateMutation = useGeneratePaymentPlan();

  return (
    <div data-guide="contratto-piano-rate">
      {hasRates ? (
        <RatesList rates={rates} contract={contract} />
      ) : (
        <GeneratePlanForm contract={contract} generateMutation={generateMutation} />
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Caso B: Rate esistenti → lista premium
// ════════════════════════════════════════════════════════════

function RatesList({
  rates,
  contract,
}: {
  rates: Rate[];
  contract: ContractWithRates;
}) {
  const [editRate, setEditRate] = useState<Rate | null>(null);
  const [deleteRate, setDeleteRate] = useState<Rate | null>(null);
  const [unpayRate, setUnpayRate] = useState<Rate | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const deleteMutation = useDeleteRate();
  const createMutation = useCreateRate();

  // Ordina: scadute prima, poi pendenti/parziali, poi saldate
  const sorted = [...rates].sort((a, b) => {
    const aWeight = rateWeight(a);
    const bWeight = rateWeight(b);
    if (aWeight !== bWeight) return aWeight - bWeight;
    return new Date(a.data_scadenza).getTime() - new Date(b.data_scadenza).getTime();
  });

  return (
    <div className="space-y-3">
      {/* ── Breakdown Finanziario + Mismatch Alert + banner scadute ── */}
      <FinancialBreakdown contract={contract} />

      <ScrollArea className="max-h-[50vh]">
        <div className="space-y-2.5 pr-4">
          {sorted.map((rate) => (
            <RateCard
              key={rate.id}
              rate={rate}
              onEdit={setEditRate}
              onDelete={setDeleteRate}
              onUnpay={setUnpayRate}
            />
          ))}
        </div>
      </ScrollArea>

      {/* ── Bottone Aggiungi Rata ── */}
      {showAddForm ? (
        <AddRateForm
          contractId={contract.id}
          contractScadenza={contract.data_scadenza ?? undefined}
          createMutation={createMutation}
          onClose={() => setShowAddForm(false)}
        />
      ) : (
        <Button
          variant="outline"
          size="sm"
          className="w-full border-dashed"
          onClick={() => setShowAddForm(true)}
        >
          <Plus className="mr-2 h-4 w-4" />
          Aggiungi Rata
        </Button>
      )}

      {/* ── Edit Dialog ── */}
      <RateEditDialog
        rate={editRate}
        open={editRate !== null}
        onOpenChange={(open) => { if (!open) setEditRate(null); }}
        contractScadenza={contract.data_scadenza ?? undefined}
      />

      {/* ── Unpay Dialog (conferma con "ANNULLA") ── */}
      <RateUnpayDialog
        rate={unpayRate}
        open={unpayRate !== null}
        onOpenChange={(open) => { if (!open) setUnpayRate(null); }}
      />

      {/* ── Delete Confirm ── */}
      <AlertDialog
        open={deleteRate !== null}
        onOpenChange={(open) => { if (!open) setDeleteRate(null); }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare questa rata?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteRate?.descrizione ?? `Rata #${deleteRate?.id}`} —{" "}
              {deleteRate ? formatCurrency(deleteRate.importo_previsto) : ""}
              . Questa azione e&apos; irreversibile.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>
              Annulla
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-white hover:bg-destructive/90"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (!deleteRate) return;
                deleteMutation.mutate(deleteRate.id, {
                  onSuccess: () => setDeleteRate(null),
                });
              }}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

/** Peso per ordinamento: scadute (0) → pendenti (1) → parziali (2) → saldate (3) */
function rateWeight(rate: Rate): number {
  if (rate.stato === "SALDATA") return 3;
  if (rate.is_scaduta) return 0;
  if (rate.stato === "PARZIALE") return 2;
  return 1;
}
