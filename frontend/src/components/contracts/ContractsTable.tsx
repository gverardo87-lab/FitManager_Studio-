// src/components/contracts/ContractsTable.tsx
"use client";

/**
 * Tabella contratti enriched — colonne: Cliente, Pacchetto, Finanze, Crediti, Scadenza,
 * Stato, Pagamenti, Azioni.
 *
 * Classificazione interamente dal SSoT backend (contract_state.py via ContractListItem):
 * questo file LEGGE i campi derivati, non li ricalcola (SPEC_VOCABOLARIO §2.5).
 * - Due assi distinti, mai fusi: Stato di vita (lifecycle) + Pagamenti (money_substate),
 *   resi dai badge canonici di `lib/contract-status`.
 * - "Denaro arretrato" (ha_rate_scadute = SSoT rate_scadute): segnale di RIGA — sfondo
 *   rosso percepibile + icona AlertTriangle + aria-label — copre sia gli insolventi
 *   (scaduti) sia gli ATTIVO in ritardo (G1). Mai col solo colore (regola accessibilità,
 *   frontend/CLAUDE.md). NON è un terzo badge che compete con i due assi.
 * - Colonna Scadenza: neutra; l'urgenza la comunicano lo Stato e il segnale di riga.
 */

import { useState, useMemo } from "react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { it } from "date-fns/locale";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Search,
  FileText,
  Plus,
  AlertTriangle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import type { ContractListItem } from "@/types/api";
import { formatCurrency, getFinanceBarColor } from "@/lib/format";
import { ContractLifecycleBadge, ContractMoneyBadge } from "@/lib/contract-status";

interface ContractsTableProps {
  contracts: ContractListItem[];
  onEdit: (contract: ContractListItem) => void;
  onDelete: (contract: ContractListItem) => void;
  onNewContract?: () => void;
}

export function ContractsTable({
  contracts,
  onEdit,
  onDelete,
  onNewContract,
}: ContractsTableProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return contracts;

    const q = search.toLowerCase();
    return contracts.filter((c) => {
      const clientName = `${c.client_cognome} ${c.client_nome}`.toLowerCase();
      return (
        clientName.includes(q) ||
        c.tipo_pacchetto?.toLowerCase().includes(q)
      );
    });
  }, [contracts, search]);

  return (
    <div className="space-y-4">
      {/* ── Barra ricerca ── */}
      <div className="relative w-full sm:max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Cerca per cliente o pacchetto..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={search ? "Nessun risultato" : "Nessun contratto"}
          subtitle={search
            ? "Prova a cercare con un termine diverso"
            : "Inizia aggiungendo il primo contratto per un cliente"}
          action={!search && onNewContract ? {
            label: "Nuovo Contratto",
            onClick: onNewContract,
            icon: <Plus className="h-4 w-4" />,
          } : undefined}
        />
      ) : (
        <div className="rounded-lg border bg-white dark:bg-zinc-900 overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead className="hidden md:table-cell">Pacchetto</TableHead>
                <TableHead className="hidden sm:table-cell">Finanze</TableHead>
                <TableHead className="hidden lg:table-cell text-center">Crediti</TableHead>
                <TableHead className="hidden md:table-cell">Scadenza</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead className="hidden sm:table-cell">Pagamenti</TableHead>
                <TableHead className="w-[80px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((contract, i) => (
                <TableRow
                  key={contract.id}
                  {...(i === 0 ? { "data-guide": "contratti-table-first-row" } : {})}
                  className={`transition-colors ${
                    contract.ha_rate_scadute && !contract.chiuso
                      ? "bg-red-100/70 hover:bg-red-100 dark:bg-red-900/30 dark:hover:bg-red-900/40"
                      : "hover:bg-muted/50"
                  }`}
                >
                  {/* ── Cliente (link a scheda contratto) ── */}
                  <TableCell className="font-medium">
                    <Link href={`/contratti/${contract.id}`} className="hover:underline">
                      {contract.client_cognome} {contract.client_nome}
                    </Link>
                  </TableCell>

                  {/* ── Pacchetto (hidden mobile) ── */}
                  <TableCell className="hidden md:table-cell">{contract.tipo_pacchetto ?? "—"}</TableCell>

                  {/* ── Finanze (hidden mobile) — progress bar ── */}
                  <TableCell className="hidden sm:table-cell">
                    {contract.prezzo_totale ? (() => {
                      const prezzo = contract.prezzo_totale!;
                      const versato = contract.totale_versato;
                      const ratio = prezzo > 0 ? versato / prezzo : 0;
                      return (
                        <div className="w-28 space-y-1">
                          <div className="flex items-baseline justify-between text-[11px]">
                            <span className="font-semibold tabular-nums">
                              {formatCurrency(versato)}
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
                        </div>
                      );
                    })() : (
                      <span className="text-sm italic text-muted-foreground">—</span>
                    )}
                  </TableCell>

                  {/* ── Crediti (hidden mobile/tablet) ── */}
                  <TableCell className="hidden lg:table-cell text-center">
                    <span className="font-mono text-sm">
                      {contract.crediti_usati}/{contract.crediti_totali ?? 0}
                    </span>
                  </TableCell>

                  {/* ── Scadenza (hidden mobile) — neutra: l'urgenza la dà lo Stato + segnale riga ── */}
                  <TableCell className="hidden md:table-cell text-muted-foreground">
                    {contract.data_scadenza
                      ? format(parseISO(contract.data_scadenza), "dd MMM yyyy", { locale: it })
                      : "—"}
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
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
