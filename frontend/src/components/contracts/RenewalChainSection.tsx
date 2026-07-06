// src/components/contracts/RenewalChainSection.tsx
"use client";

/**
 * Catena rinnovi del contratto (originale → corrente → rinnovi successivi).
 * Presentazionale: legge la catena già presente sul dettaglio (`contratto_originale` +
 * `rinnovi_successivi`); ogni nodo porta il PROPRIO lifecycle reale (SPEC_VOCABOLARIO §2.7/G3).
 */

import Link from "next/link";
import { RefreshCw } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { ContractLifecycleBadge } from "@/lib/contract-status";
import type { ContractWithRates, RenewalChainItem } from "@/types/api";

export function RenewalChainSection({ contract }: { contract: ContractWithRates }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-2 p-4">
        <div className="flex items-center gap-2 text-sm font-medium">
          <RefreshCw className="h-4 w-4 text-primary" />
          Catena rinnovi
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {contract.contratto_originale && (
            <RenewalChainLink item={contract.contratto_originale} label="Originale" />
          )}
          {contract.contratto_originale && (
            <span className="text-muted-foreground">→</span>
          )}
          <span className="rounded-md border-2 border-primary/30 bg-primary/5 px-3 py-1 font-medium">
            {contract.tipo_pacchetto ?? "Contratto corrente"}
          </span>
          {contract.rinnovi_successivi.map((item) => (
            <span key={item.id} className="flex items-center gap-2">
              <span className="text-muted-foreground">→</span>
              <RenewalChainLink item={item} label="Rinnovo" />
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function RenewalChainLink({ item, label }: { item: RenewalChainItem; label: string }) {
  return (
    <Link
      href={`/contratti/${item.id}`}
      className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1 transition-colors hover:bg-muted"
    >
      <span>{item.tipo_pacchetto ?? label}</span>
      <ContractLifecycleBadge lifecycle={item.lifecycle} />
    </Link>
  );
}
