// src/components/clients/profile/ContrattiTab.tsx
"use client";

import { useRouter } from "next/navigation";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { AlertTriangle, FileText } from "lucide-react";
import { useClientContracts } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import { ContractLifecycleBadge, ContractMoneyBadge } from "@/lib/contract-status";
import { TabSkeleton, EmptyTab } from "./ProfileShared";
import type { ContractListItem } from "@/types/api";

export function ContrattiTab({ clientId }: { clientId: number }) {
  const router = useRouter();
  const { data, isLoading } = useClientContracts(clientId);

  if (isLoading) return <TabSkeleton />;

  const contracts = data?.items ?? [];

  if (contracts.length === 0) {
    return (
      <EmptyTab
        icon={FileText}
        message="Nessun contratto attivo"
        hint="Il contratto definisce il pacchetto, i crediti e il piano pagamento."
        action={{ label: "Crea Contratto", href: `/contratti?new=1&cliente=${clientId}` }}
      />
    );
  }

  return (
    <div className="rounded-lg border bg-white dark:bg-zinc-900 overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Pacchetto</TableHead>
            <TableHead>Finanze</TableHead>
            <TableHead className="text-center">Crediti</TableHead>
            <TableHead>Stato</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contracts.map((c: ContractListItem) => {
            const prezzo = c.prezzo_totale ?? 0;
            return (
              <TableRow key={c.id} className="cursor-pointer hover:bg-muted/50" onClick={() => router.push(`/contratti/${c.id}?from=clienti-${clientId}`)}>
                <TableCell className="font-medium">{c.tipo_pacchetto ?? "—"}</TableCell>
                <TableCell>
                  {prezzo > 0 ? (
                    <span className="text-sm tabular-nums">
                      {formatCurrency(c.totale_versato)} / {formatCurrency(prezzo)}
                    </span>
                  ) : "—"}
                </TableCell>
                <TableCell className="text-center">
                  <span className="font-mono text-sm">{c.crediti_usati}/{c.crediti_totali ?? 0}</span>
                  {/* L1: erogato (servizio reso) affiancato all'occupazione — niente ricalcolo */}
                  {(c.crediti_totali ?? 0) > 0 ? (
                    <p className="text-[10px] text-muted-foreground">{c.sedute_completate} svolte</p>
                  ) : null}
                  {/* M4: COMPLETAMENTO chiuso su sedute solo prenotate → rimborso recuperabile */}
                  {c.sedute_non_erogate_chiusura > 0 ? (
                    <p className="text-[10px] text-amber-600 dark:text-amber-400">
                      {c.sedute_non_erogate_chiusura} prenotate non svolte
                    </p>
                  ) : null}
                </TableCell>
                <TableCell>
                  {/* M3: due assi dal SSoT (vita × denaro) — niente più cascata off-SSoT che collassava
                      Sospeso/Esaurito in "Attivo" (divergeva da /contratti). */}
                  <div className="flex flex-col items-start gap-1">
                    <ContractLifecycleBadge lifecycle={c.lifecycle} />
                    <ContractMoneyBadge money={c.money_substate} />
                    {c.ha_rate_scadute && !c.chiuso ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-red-600 dark:text-red-400">
                        <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                        Rate scadute
                      </span>
                    ) : null}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
