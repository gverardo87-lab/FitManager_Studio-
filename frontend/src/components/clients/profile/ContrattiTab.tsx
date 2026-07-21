// src/components/clients/profile/ContrattiTab.tsx
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { AlertTriangle, Coins, FileText } from "lucide-react";
import { useClientContracts, useClientWalletCredits } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import { ContractLifecycleBadge, ContractMoneyBadge } from "@/lib/contract-status";
import { DataErrorState } from "@/components/ui/data-error-state";
import { TabSkeleton, EmptyTab } from "./ProfileShared";
import type { ContractListItem } from "@/types/api";

/** Badge sola-lettura del credito a wallet del cliente (G8.1, ADR-020) — link alla worklist erogazione.
 *  Self-hide se nessun credito aperto. */
function WalletCreditBadge({ clientId }: { clientId: number }) {
  const { data, isError, isFetching, refetch } = useClientWalletCredits(clientId);
  if (isError) {
    return (
      <DataErrorState
        title="Credito cliente non verificato"
        message="I contratti sono disponibili, ma il credito wallet non può essere confermato."
        onRetry={() => void refetch()}
        isRetrying={isFetching}
      />
    );
  }
  const totale = (data ?? [])
    .filter((c) => c.stato === "APERTO")
    .reduce((sum, c) => sum + c.residuo, 0);
  if (totale <= 0.009) return null;
  return (
    <Link
      href="/rinnovi-incassi"
      className="flex items-center gap-2 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 transition-colors hover:bg-rose-100 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
    >
      <Coins className="h-4 w-4 shrink-0" />
      <span>
        Credito wallet del cliente:{" "}
        <span className="font-semibold tabular-nums">{formatCurrency(totale)}</span> da erogare
      </span>
    </Link>
  );
}

export function ContrattiTab({ clientId }: { clientId: number }) {
  const router = useRouter();
  const { data, isLoading, isError, isFetching, refetch } = useClientContracts(clientId);

  if (isLoading) return <TabSkeleton />;
  if (isError) {
    return (
      <DataErrorState
        title="Contratti non disponibili"
        message="Non è possibile verificare i contratti del cliente."
        onRetry={() => void refetch()}
        isRetrying={isFetching}
      />
    );
  }

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
    <div className="space-y-3">
      <WalletCreditBadge clientId={clientId} />
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
                  {/* L1: erogato affiancato all'occupazione · G9.7.3/D3: penali spiegate */}
                  {(c.crediti_totali ?? 0) > 0 ? (
                    <p className="text-[10px] text-muted-foreground">
                      {c.sedute_completate} svolte
                      {c.sedute_penali > 0 ? (
                        <span className="text-amber-600 dark:text-amber-400"> · {c.sedute_penali} penali</span>
                      ) : null}
                    </p>
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
    </div>
  );
}
