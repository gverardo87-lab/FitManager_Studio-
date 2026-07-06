// src/components/contracts/ContractsTable.tsx
"use client";

/**
 * Tabella contratti enriched — colonne: Cliente, Pacchetto, Finanze, Crediti, Scadenza,
 * Stato, Pagamenti, Azioni.
 *
 * CONTAINER (G8.4 F5): ricerca, stato dei 3 dialog condivisi (target separato da `open`,
 * anti-glitch fade-out) e wiring callback. La riga è presentazionale: `ContractRow.tsx`
 * (classificazione dal SSoT backend, SPEC_VOCABOLARIO §2.5 — LEGGE i campi derivati).
 */

import { useState, useMemo } from "react";
import { Search, FileText, Plus } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import type { ContractListItem } from "@/types/api";
import { ContractRow } from "./ContractRow";
import { IncassaResiduoDialog } from "./IncassaResiduoDialog";
import { TerminateContractDialog } from "./TerminateContractDialog";
import { ReopenContractDialog } from "./ReopenContractDialog";
import { getIncassaResiduoAmount } from "./contract-action-guards";

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
  // Dialog incasso: open separato dal target (incassaContract resta valorizzato durante la
  // ~200ms di fade-out di Radix → niente glitch "Supera il residuo di € 0,00" alla chiusura).
  const [incassaContract, setIncassaContract] = useState<ContractListItem | null>(null);
  const [incassaOpen, setIncassaOpen] = useState(false);
  // Terminazione (G7.3): stesso pattern open-separato-dal-target dell'incasso.
  const [terminateContract, setTerminateContract] = useState<ContractListItem | null>(null);
  const [terminateOpen, setTerminateOpen] = useState(false);
  // Riapertura (G7.4): inverso di terminate, per i contratti chiusi.
  const [reopenContract, setReopenContract] = useState<ContractListItem | null>(null);
  const [reopenOpen, setReopenOpen] = useState(false);

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
                <ContractRow
                  key={contract.id}
                  contract={contract}
                  isFirst={i === 0}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onIncassa={(c) => {
                    setIncassaContract(c);
                    setIncassaOpen(true);
                  }}
                  onTerminate={(c) => {
                    setTerminateContract(c);
                    setTerminateOpen(true);
                  }}
                  onReopen={(c) => {
                    setReopenContract(c);
                    setReopenOpen(true);
                  }}
                />
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Incasso residuo diretto (G6) — un solo dialog condiviso, target = riga selezionata.
          open è uno stato separato: incassaContract NON viene azzerato alla chiusura, così i
          props restano coerenti durante l'animazione di fade-out (no glitch residuo €0). */}
      <IncassaResiduoDialog
        contractId={incassaContract?.id ?? null}
        residuo={incassaContract ? getIncassaResiduoAmount(incassaContract) : 0}
        clientLabel={
          incassaContract
            ? `${incassaContract.client_cognome} ${incassaContract.client_nome}`
            : ""
        }
        open={incassaOpen}
        onOpenChange={setIncassaOpen}
      />

      {/* Terminazione (G7.3) — un solo dialog condiviso, target = riga selezionata (open separato). */}
      <TerminateContractDialog
        contractId={terminateContract?.id ?? null}
        clientLabel={
          terminateContract
            ? `${terminateContract.client_cognome} ${terminateContract.client_nome}`
            : ""
        }
        open={terminateOpen}
        onOpenChange={setTerminateOpen}
      />

      {/* Riapertura (G7.4) — inverso di terminate, per i contratti chiusi. */}
      <ReopenContractDialog
        contract={reopenContract}
        clientLabel={
          reopenContract
            ? `${reopenContract.client_cognome} ${reopenContract.client_nome}`
            : ""
        }
        open={reopenOpen}
        onOpenChange={setReopenOpen}
      />
    </div>
  );
}
