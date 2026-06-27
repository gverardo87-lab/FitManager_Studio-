// src/components/contracts/CreditiDaIncassareCard.tsx
"use client";

/**
 * Worklist "Crediti da incassare (post-chiusura)" (G7.10) — receivable `crediti_terminazione` APERTI.
 *
 * Il credito a favore del trainer creato da una terminazione A_CREDITO ("il cliente paga dopo"). Vive
 * FUORI da residuo() del contratto. Azioni: Incassa (anche parziale) o Annulla (rinuncia al residuo).
 * Si auto-nasconde quando non ci sono crediti aperti (zero clutter). Aging-driven dal backend.
 */

import { useState } from "react";
import { HandCoins } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { useCreditiDaIncassare, useAnnullaCredito } from "@/hooks/useContracts";
import { IncassaCreditoDialog } from "./IncassaCreditoDialog";
import { formatCurrency } from "@/lib/format";
import type { CreditoDaIncassareItem } from "@/types/api";

export function CreditiDaIncassareCard() {
  const { data, isLoading } = useCreditiDaIncassare();
  const annulla = useAnnullaCredito();
  const [incassoTarget, setIncassoTarget] = useState<CreditoDaIncassareItem | null>(null);
  const [incassoOpen, setIncassoOpen] = useState(false);
  const [annulTarget, setAnnulTarget] = useState<CreditoDaIncassareItem | null>(null);

  const items = data?.items ?? [];
  if (isLoading || items.length === 0) return null; // niente crediti aperti → niente sezione

  const openIncasso = (item: CreditoDaIncassareItem) => {
    setIncassoTarget(item);
    setIncassoOpen(true);
  };

  const confirmAnnulla = () => {
    if (!annulTarget) return;
    annulla.mutate(
      { contractId: annulTarget.id_contratto, creditoId: annulTarget.id },
      { onSettled: () => setAnnulTarget(null) },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <HandCoins className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
          Crediti da incassare
          <span className="rounded-full bg-teal-100 px-2 py-0.5 text-xs font-medium text-teal-700 dark:bg-teal-500/15 dark:text-teal-300">
            {items.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-[11px] text-muted-foreground">
          Saldi a tuo favore lasciati &quot;a credito&quot; alla chiusura: il cliente paga dopo. Incassali
          quando salda, o annullali se rinunci.
        </p>
        {items.map((item) => {
          const label = `${item.cliente_nome} ${item.cliente_cognome}`.trim();
          return (
            <div
              key={item.id}
              className="flex flex-wrap items-center gap-2 rounded-md border p-2.5 text-sm"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{label}</p>
                <p className="text-[11px] text-muted-foreground">
                  Aperto da {item.giorni_aperto} {item.giorni_aperto === 1 ? "giorno" : "giorni"}
                  {item.importo_incassato > 0
                    ? ` · Incassato ${formatCurrency(item.importo_incassato)}/${formatCurrency(item.importo)}`
                    : ""}
                </p>
              </div>
              <span className="font-medium tabular-nums text-teal-700 dark:text-teal-300">
                {formatCurrency(item.residuo)}
              </span>
              <div className="flex items-center gap-1.5">
                <Button size="sm" onClick={() => openIncasso(item)}>
                  Incassa
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAnnulTarget(item)}
                  disabled={annulla.isPending}
                >
                  Annulla
                </Button>
              </div>
            </div>
          );
        })}
      </CardContent>

      <IncassaCreditoDialog
        contractId={incassoTarget?.id_contratto ?? null}
        creditoId={incassoTarget?.id ?? null}
        residuo={incassoTarget?.residuo ?? 0}
        clientLabel={
          incassoTarget ? `${incassoTarget.cliente_nome} ${incassoTarget.cliente_cognome}`.trim() : ""
        }
        open={incassoOpen}
        onOpenChange={setIncassoOpen}
      />

      <AlertDialog open={annulTarget !== null} onOpenChange={(o) => !o && setAnnulTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Annullare il credito?</AlertDialogTitle>
            <AlertDialogDescription>
              Rinunci al residuo non incassato
              {annulTarget ? ` di ${formatCurrency(annulTarget.residuo)}` : ""}. Non viene mosso denaro: il
              credito esce dalla lista come &quot;annullato&quot;.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Indietro</AlertDialogCancel>
            <AlertDialogAction onClick={confirmAnnulla}>Annulla credito</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
