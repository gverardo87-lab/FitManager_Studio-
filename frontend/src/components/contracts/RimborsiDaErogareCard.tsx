// src/components/contracts/RimborsiDaErogareCard.tsx
"use client";

/**
 * Worklist "Rimborsi da erogare" (G8.1, ADR-020) — wallet `crediti_cliente` APERTI, gemella in USCITA di
 * CreditiDaIncassareCard.
 *
 * Credito a favore del CLIENTE (rimborso differito da una terminazione, o overpayment): denaro che il
 * trainer deve restituire. Azione: Eroga (anche parziale). Niente "annulla": non si abbuona denaro
 * dovuto al cliente (asimmetria ADR-020). Si auto-nasconde quando non ci sono crediti aperti.
 */

import { useState } from "react";
import { Coins } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EroghaRimborsoDialog } from "./EroghaRimborsoDialog";
import { formatCurrency } from "@/lib/format";
import type { RimborsoDaErogareItem } from "@/types/api";

interface RimborsiDaErogareCardProps {
  items: RimborsoDaErogareItem[];
}

export function RimborsiDaErogareCard({ items }: RimborsiDaErogareCardProps) {
  const [target, setTarget] = useState<RimborsoDaErogareItem | null>(null);
  const [open, setOpen] = useState(false);

  if (items.length === 0) return null; // niente crediti aperti → niente sezione

  const openEroga = (item: RimborsoDaErogareItem) => {
    setTarget(item);
    setOpen(true);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Coins className="h-4.5 w-4.5 text-rose-600 dark:text-rose-400" />
          Rimborsi da erogare
          <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-500/15 dark:text-rose-300">
            {items.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-[11px] text-muted-foreground">
          Credito a favore del cliente lasciato a wallet alla chiusura: denaro che gli devi restituire.
          Erogalo in cassa quando vuoi, anche in più volte.
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
                  {item.importo_erogato > 0
                    ? ` · Erogato ${formatCurrency(item.importo_erogato)}/${formatCurrency(item.importo)}`
                    : ""}
                </p>
              </div>
              <span className="font-medium tabular-nums text-rose-700 dark:text-rose-300">
                {formatCurrency(item.residuo)}
              </span>
              <Button size="sm" onClick={() => openEroga(item)}>
                Eroga
              </Button>
            </div>
          );
        })}
      </CardContent>

      <EroghaRimborsoDialog
        clientId={target?.id_cliente ?? null}
        creditoId={target?.id ?? null}
        residuo={target?.residuo ?? 0}
        clientLabel={target ? `${target.cliente_nome} ${target.cliente_cognome}`.trim() : ""}
        open={open}
        onOpenChange={setOpen}
      />
    </Card>
  );
}
