// src/components/contracts/ContractRow.tsx
"use client";

/**
 * Riga della tabella contratti (G8.4 F5) — presentazionale CONTROLLATA: props in, callback out.
 * Classificazione interamente dal SSoT backend (SPEC_VOCABOLARIO §2.5): due assi mai fusi
 * (Stato lifecycle + Pagamenti money_substate) + segnale di riga "denaro arretrato"
 * (sfondo + icona AlertTriangle con aria-label, mai col solo colore).
 * Finanze: netto_incassato dal SSoT (G8.4 F1.a) + sub-label lordo−rimborsi (D-1, mai netto nudo).
 */

import Link from "next/link";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  FileText,
  AlertTriangle,
  HandCoins,
  Lock,
  RotateCcw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ContractListItem } from "@/types/api";
import { formatCurrency, getFinanceBarColor } from "@/lib/format";
import { ContractLifecycleBadge, ContractMoneyBadge } from "@/lib/contract-status";
import { getIncassaResiduoAmount } from "./contract-action-guards";

interface ContractRowProps {
  contract: ContractListItem;
  isFirst: boolean;
  onEdit: (contract: ContractListItem) => void;
  onDelete: (contract: ContractListItem) => void;
  onIncassa: (contract: ContractListItem) => void;
  onTerminate: (contract: ContractListItem) => void;
  onReopen: (contract: ContractListItem) => void;
}

export function ContractRow({
  contract,
  isFirst,
  onEdit,
  onDelete,
  onIncassa,
  onTerminate,
  onReopen,
}: ContractRowProps) {
  return (
    <TableRow
      {...(isFirst ? { "data-guide": "contratti-table-first-row" } : {})}
      className={`transition-colors ${
        contract.ha_rate_scadute && !contract.chiuso
          ? "bg-red-100/70 hover:bg-red-100 dark:bg-red-900/30 dark:hover:bg-red-900/40"
          : "hover:bg-muted/50"
      }`}
    >
      {/* ── Cliente (link a scheda contratto) ── */}
      <TableCell className="font-medium">
        <div className="min-w-0">
          <Link href={`/contratti/${contract.id}`} className="hover:underline">
            {contract.client_cognome} {contract.client_nome}
          </Link>
          <div className="mt-1 space-y-0.5 lg:hidden">
            <p className="font-mono text-[10px] text-muted-foreground">
              {contract.crediti_usati}/{contract.crediti_totali ?? 0} crediti
            </p>
            <p className="text-[10px] text-muted-foreground">
              {/* G9.7.3/D2: usati − svolte = penali, spiegato nella STESSA vista */}
              {contract.sedute_completate} svolte
              {contract.sedute_penali > 0 ? (
                <span className="text-amber-600 dark:text-amber-400"> · {contract.sedute_penali} penali</span>
              ) : null}
            </p>
            {contract.sedute_non_erogate_chiusura > 0 ? (
              <p className="text-[10px] text-amber-600 dark:text-amber-400">
                {contract.sedute_non_erogate_chiusura} prenotate non svolte
              </p>
            ) : null}
          </div>
        </div>
      </TableCell>

      {/* ── Pacchetto (hidden mobile) ── */}
      <TableCell className="hidden md:table-cell">{contract.tipo_pacchetto ?? "—"}</TableCell>

      {/* ── Finanze (hidden mobile) — progress bar ── */}
      <TableCell className="hidden sm:table-cell">
        {contract.prezzo_totale ? <FinanceCell contract={contract} /> : (
          <span className="text-sm italic text-muted-foreground">—</span>
        )}
      </TableCell>

      {/* ── Crediti (hidden mobile/tablet) ── */}
      <TableCell className="hidden lg:table-cell text-center">
        <span className="font-mono text-sm">
          {contract.crediti_usati}/{contract.crediti_totali ?? 0}
        </span>
        {/* L1: erogato affiancato all'occupazione · G9.7.3/D2: penali spiegate nella stessa vista */}
        {(contract.crediti_totali ?? 0) > 0 ? (
          <p className="text-[10px] text-muted-foreground">
            {contract.sedute_completate} svolte
            {contract.sedute_penali > 0 ? (
              <span className="text-amber-600 dark:text-amber-400"> · {contract.sedute_penali} penali</span>
            ) : null}
          </p>
        ) : null}
        {/* M4: COMPLETAMENTO chiuso su sole prenotate → rimborso recuperabile */}
        {contract.sedute_non_erogate_chiusura > 0 ? (
          <p className="text-[10px] text-amber-600 dark:text-amber-400">
            {contract.sedute_non_erogate_chiusura} non svolte
          </p>
        ) : null}
      </TableCell>

      {/* ── Scadenza (hidden mobile) — neutra: l'urgenza la dà lo Stato + segnale riga ── */}
      <TableCell className="hidden md:table-cell text-muted-foreground">
        {contract.data_scadenza
          ? format(parseISO(contract.data_scadenza), "dd MMM yyyy", { locale: it })
          : "Senza scadenza"}
      </TableCell>

      {/* ── Stato (asse vita) + segnale "denaro arretrato" (icona, sempre visibile) ── */}
      <TableCell>
        <div className="flex items-center gap-1.5">
          <ContractLifecycleBadge lifecycle={contract.lifecycle} />
          {contract.ha_rate_scadute && !contract.chiuso ? (
            <AlertTriangle
              role="img"
              aria-label="Rate scadute"
              className="h-3.5 w-3.5 shrink-0 text-red-600 dark:text-red-400"
            />
          ) : null}
        </div>
      </TableCell>

      {/* ── Pagamenti (asse denaro) — prezzo assente → "—", mai "Saldato" (AC-12b).
           Difesa-in-profondità vs eventuale legacy prezzo-nullo: l'invariante PREREQ-prezzo
           (FDM §9.5.7) rende il caso irraggiungibile sui nuovi. NON rimuovere. ── */}
      <TableCell className="hidden sm:table-cell">
        {contract.prezzo_totale != null ? (
          <ContractMoneyBadge money={contract.money_substate} />
        ) : (
          <span className="text-sm italic text-muted-foreground">—</span>
        )}
      </TableCell>

      {/* ── Azioni ── */}
      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
              <span className="sr-only">Azioni</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href={`/contratti/${contract.id}`}>
                <FileText className="mr-2 h-4 w-4" />
                Dettagli
              </Link>
            </DropdownMenuItem>
            {getIncassaResiduoAmount(contract) > 0 ? (
              <DropdownMenuItem onClick={() => onIncassa(contract)}>
                <HandCoins className="mr-2 h-4 w-4" />
                Incassa residuo
              </DropdownMenuItem>
            ) : null}
            {contract.lifecycle !== "chiuso" ? (
              <DropdownMenuItem onClick={() => onTerminate(contract)}>
                <Lock className="mr-2 h-4 w-4" />
                Termina
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onClick={() => onReopen(contract)}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Riapri
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={() => onEdit(contract)}>
              <Pencil className="mr-2 h-4 w-4" />
              Modifica
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDelete(contract)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Elimina
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}

function FinanceCell({ contract }: { contract: ContractListItem }) {
  const prezzo = contract.prezzo_totale!;
  const rimborsato = contract.totale_rimborsato ?? 0;
  const netto = contract.netto_incassato; // SSoT backend (G8.4 F1.a) — MAI ricalcolato client-side
  const haRimborso = rimborsato > 0.009;
  const ratio = prezzo > 0 ? netto / prezzo : 0;
  return (
    <div className="w-28 space-y-1">
      <div className="flex items-baseline justify-between text-[11px]">
        <span className="font-semibold tabular-nums">
          {formatCurrency(netto)}
        </span>
        <span className="text-muted-foreground">
          / {formatCurrency(prezzo)}
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-1.5 rounded-full transition-all ${getFinanceBarColor(ratio)}`}
          style={{ width: `${Math.min(ratio * 100, 100)}%` }}
        />
      </div>
      {haRimborso ? (
        <p className="text-[10px] tabular-nums text-muted-foreground">
          lordo {formatCurrency(contract.totale_versato)} · −{formatCurrency(rimborsato)}
        </p>
      ) : null}
    </div>
  );
}
