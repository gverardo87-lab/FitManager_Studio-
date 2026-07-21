// src/app/(dashboard)/contratti/[id]/page.tsx
"use client";

/**
 * Scheda Contratto — pagina full-page con dettaglio completo.
 *
 * Layout:
 * - ContractHeader (persistente): back, nome cliente (link), pacchetto, badge stato, azioni
 * - ContractFinancialHero (persistente): KPI cards finanziarie + crediti
 * - Tabs: Piano Pagamenti | Sessioni | Storico | Dettagli (tab estratti in components/contracts, F5 G8.4)
 *
 * Pattern identico a /clienti/[id] — dynamic route con use(params).
 */

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  ArrowLeft,
  Pencil,
  Trash2,
  Receipt,
  Calendar,
  Settings2,
  AlertTriangle,
  HandCoins,
  Lock,
  RotateCcw,
  History,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DataErrorState } from "@/components/ui/data-error-state";

import { ContractFinancialHero } from "@/components/contracts/ContractFinancialHero";
import { PaymentPlanTab } from "@/components/contracts/PaymentPlanTab";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { DeleteContractDialog } from "@/components/contracts/DeleteContractDialog";
import { IncassaResiduoDialog } from "@/components/contracts/IncassaResiduoDialog";
import { TerminateContractDialog } from "@/components/contracts/TerminateContractDialog";
import { ReopenContractDialog } from "@/components/contracts/ReopenContractDialog";
import { ContractHistoryTab } from "@/components/contracts/ContractHistoryTab";
import { RenewalChainSection } from "@/components/contracts/RenewalChainSection";
import { ContractSessioniTab } from "@/components/contracts/ContractSessioniTab";
import { ContractDettagliTab } from "@/components/contracts/ContractDettagliTab";
import { useContract } from "@/hooks/useContracts";
import { resolveBackNavigation } from "@/lib/url-state";
import { ContractLifecycleBadge } from "@/lib/contract-status";
import { getIncassaResiduoAmount } from "@/components/contracts/contract-action-guards";
import { isNotFoundError } from "@/lib/query-error";

// ════════════════════════════════════════════════════════════
// PAGE COMPONENT
// ════════════════════════════════════════════════════════════

export default function ContractDetailPage({
  params,
  searchParams: searchParamsPromise,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ from?: string; returnTo?: string }>;
}) {
  const { id } = use(params);
  const { from, returnTo } = use(searchParamsPromise);
  const contractId = parseInt(id, 10);
  const validContractId = Number.isInteger(contractId) && contractId > 0 ? contractId : null;
  const router = useRouter();
  const safeReturnTo =
    returnTo && returnTo.startsWith("/") && !returnTo.startsWith("//") ? returnTo : null;
  const backNav = resolveBackNavigation(from, { href: "/contratti", label: "Torna ai contratti" }, { tab: "contratti" });
  const backHref = safeReturnTo ?? backNav.href;
  const backLabel = safeReturnTo?.startsWith("/rinnovi-incassi")
    ? "Torna a Rinnovi & Incassi"
    : backNav.label;

  const contractQuery = useContract(validContractId);
  const { data: contract, isLoading } = contractQuery;
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [incassaOpen, setIncassaOpen] = useState(false);
  const [terminateOpen, setTerminateOpen] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);

  const retryContract = () => {
    void contractQuery.refetch();
  };

  if (validContractId === null) return <ContractNotFoundState />;
  if (isLoading) return <PageSkeleton />;
  if (contractQuery.isError) {
    if (isNotFoundError(contractQuery.error)) return <ContractNotFoundState />;
    return (
      <DataErrorState
        title="Impossibile aprire il contratto"
        message="Il contratto non è stato verificato. Controlla la connessione e riprova."
        onRetry={retryContract}
        isRetrying={contractQuery.isFetching}
      />
    );
  }
  if (!contract) {
    return (
      <DataErrorState
        title="Contratto non disponibile"
        message="La richiesta è terminata senza dati verificabili. Riprova il caricamento."
        onRetry={retryContract}
        isRetrying={contractQuery.isFetching}
      />
    );
  }

  const clientName = contract.client_nome && contract.client_cognome
    ? `${contract.client_cognome} ${contract.client_nome}`
    : undefined;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div data-guide="contratto-header" className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Link
            href={backHref}
            className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-white shadow-sm transition-colors hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800"
            title={backLabel}
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight">
                {contract.tipo_pacchetto ?? "Contratto"}
              </h1>
              <ContractLifecycleBadge lifecycle={contract.lifecycle} />
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              {clientName && (
                <Link
                  href={
                    safeReturnTo
                      ? `/clienti/${contract.id_cliente}?returnTo=${encodeURIComponent(safeReturnTo)}`
                      : `/clienti/${contract.id_cliente}`
                  }
                  className="font-medium text-foreground hover:underline"
                >
                  {clientName}
                </Link>
              )}
              {contract.data_inizio && (
                <>
                  <span className="text-muted-foreground/50">|</span>
                  <span>
                    {format(new Date(contract.data_inizio + "T00:00:00"), "dd MMM yyyy", { locale: it })}
                    {contract.data_scadenza ? (
                      <> — {format(new Date(contract.data_scadenza + "T00:00:00"), "dd MMM yyyy", { locale: it })}</>
                    ) : (
                      <> — Senza scadenza</>
                    )}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        <div data-guide="contratto-azioni" className="flex flex-wrap gap-2">
          {getIncassaResiduoAmount(contract) > 0 ? (
            <Button variant="outline" size="sm" onClick={() => setIncassaOpen(true)}>
              <HandCoins className="mr-2 h-4 w-4" />
              Incassa residuo
            </Button>
          ) : null}
          {contract.lifecycle !== "chiuso" ? (
            <Button
              variant="outline"
              size="sm"
              className="text-rose-600 hover:text-rose-700"
              onClick={() => setTerminateOpen(true)}
            >
              <Lock className="mr-2 h-4 w-4" />
              Termina
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setReopenOpen(true)}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Riapri
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => setSheetOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Modifica
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-destructive hover:text-destructive"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Elimina
          </Button>
        </div>
      </div>

      {/* ── Banner ritorno contestuale ── */}
      {(safeReturnTo || backNav.href !== "/contratti") && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-2 flex items-center gap-2">
          <ArrowLeft className="h-3.5 w-3.5 text-primary" />
          <Link
            href={backHref}
            className="text-sm text-primary hover:underline"
          >
            {backLabel}
          </Link>
        </div>
      )}

      {/* ── Financial Hero KPI ── */}
      <ContractFinancialHero contract={contract} />

      {/* ── Renewal chain (solo se presente) ── */}
      {(contract.contratto_originale || contract.rinnovi_successivi.length > 0) && (
        <div data-guide="contratto-catena-rinnovi">
          <RenewalChainSection contract={contract} />
        </div>
      )}

      {/* ── Tabs ── */}
      <Tabs data-guide="contratto-tabs" defaultValue="payments">
        <TabsList>
          <TabsTrigger value="payments">
            <Receipt className="mr-2 h-4 w-4" />
            Piano Pagamenti
          </TabsTrigger>
          <TabsTrigger value="sessioni">
            <Calendar className="mr-2 h-4 w-4" />
            Sessioni
          </TabsTrigger>
          <TabsTrigger value="storico">
            <History className="mr-2 h-4 w-4" />
            Storico
          </TabsTrigger>
          <TabsTrigger value="dettagli">
            <Settings2 className="mr-2 h-4 w-4" />
            Dettagli
          </TabsTrigger>
        </TabsList>

        <TabsContent value="payments" className="mt-4">
          <PaymentPlanTab contract={contract} />
        </TabsContent>

        <TabsContent value="sessioni" className="mt-4">
          <ContractSessioniTab contractId={contractId} />
        </TabsContent>

        <TabsContent value="storico" className="mt-4">
          <ContractHistoryTab contract={contract} />
        </TabsContent>

        <TabsContent value="dettagli" className="mt-4">
          <ContractDettagliTab contract={contract} />
        </TabsContent>
      </Tabs>

      {/* ── Sheet modifica ── */}
      <ContractSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        contract={contract}
      />

      <IncassaResiduoDialog
        contractId={incassaOpen ? contract.id : null}
        residuo={getIncassaResiduoAmount(contract)}
        clientLabel={clientName ?? ""}
        open={incassaOpen}
        onOpenChange={setIncassaOpen}
      />

      <TerminateContractDialog
        contractId={terminateOpen ? contract.id : null}
        clientLabel={clientName ?? ""}
        open={terminateOpen}
        onOpenChange={setTerminateOpen}
      />

      <ReopenContractDialog
        contract={reopenOpen ? contract : null}
        clientLabel={clientName ?? ""}
        open={reopenOpen}
        onOpenChange={setReopenOpen}
      />

      {/* ── Dialog elimina (redirect dopo eliminazione) ── */}
      <DeleteContractDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        contract={contract}
        clientName={clientName}
        onDeleted={() => router.push(backHref)}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SHARED UI
// ════════════════════════════════════════════════════════════

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-lg" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-40 w-full rounded-xl" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

function ContractNotFoundState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20">
      <AlertTriangle className="h-12 w-12 text-muted-foreground/30" />
      <p className="text-lg font-medium">Contratto non trovato</p>
    </div>
  );
}
