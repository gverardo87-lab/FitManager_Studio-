"use client";

/**
 * Rinnovi & Incassi — pagina operativa CRM-grade.
 *
 * Due sezioni actionable:
 * 1. Contratti da rinnovare (in scadenza / scaduti con crediti)
 * 2. Rate in ritardo (con pagamento inline)
 *
 * Visual: KPI gradient strip + card con severity coloring.
 */

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  CalendarPlus,
  CreditCard,
  HandCoins,
  HeartHandshake,
  Loader2,
  Lock,
  PauseCircle,
  RefreshCw,
  TrendingDown,
  UserMinus,
  Wallet,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { DatePicker } from "@/components/ui/date-picker";
import { WhatsAppButton } from "@/components/ui/whatsapp-button";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { IncassaResiduoDialog } from "@/components/contracts/IncassaResiduoDialog";
import { TerminateContractDialog } from "@/components/contracts/TerminateContractDialog";
import { CreditiDaIncassareCard } from "@/components/contracts/CreditiDaIncassareCard";
import { useOverdueRates, useExpiringContracts, useClientsToRecover, useSuspendedContracts } from "@/hooks/useDashboard";
import { usePayRate } from "@/hooks/useRates";
import { useMarkRenewalOutcome, useUpdateContract } from "@/hooks/useContracts";
import { useTrainerName } from "@/hooks/useTrainerName";
import { usePageReveal } from "@/lib/page-reveal";
import { formatCurrency, formatShortDate, toISOLocal } from "@/lib/format";
import { waRenewalReminder, waRateReminder, waCheckIn } from "@/lib/whatsapp-templates";
import type { ExpiringContractItem, OverdueRateItem, ClientToRecoverItem, SuspendedContractItem } from "@/types/api";

// Target comune per il rinnovo (compatibile con ExpiringContractItem e ClientToRecoverItem)
interface RenewTarget {
  client_id: number;
  contract_id: number;
  tipo_pacchetto: string | null;
  crediti_totali: number;
  prezzo_totale: number | null;
  data_inizio: string | null;
  data_scadenza: string | null;
}

const MOTIVI_NON_RINNOVA: { value: string; label: string }[] = [
  { value: "prezzo", label: "Prezzo / economico" },
  { value: "trasferito", label: "Trasferito / logistica" },
  { value: "infortunio", label: "Infortunio / salute" },
  { value: "insoddisfatto", label: "Insoddisfatto" },
  { value: "altro", label: "Altro" },
];

const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;

// ════════════════════════════════════════════════════════════
// KPI Card
// ════════════════════════════════════════════════════════════

interface KpiCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sublabel?: string;
  border: string;
  bg: string;
  iconBg: string;
  iconColor: string;
}

function KpiCard({ icon: Icon, label, value, sublabel, border, bg, iconBg, iconColor }: KpiCardProps) {
  return (
    <div className={`rounded-xl border border-l-4 ${border} bg-gradient-to-br ${bg} p-4 shadow-sm`}>
      <div className="flex items-center gap-3">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
          <Icon className={`h-4.5 w-4.5 ${iconColor}`} />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="text-lg font-bold tracking-tight">{value}</p>
          {sublabel ? <p className="text-[11px] text-muted-foreground">{sublabel}</p> : null}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// RenewalCard — card rinnovo contratto
// ════════════════════════════════════════════════════════════

function RenewalCard({
  item,
  onRenew,
  trainerName,
}: {
  item: ExpiringContractItem;
  onRenew: (item: ExpiringContractItem) => void;
  trainerName: string;
}) {
  const isExpired = item.giorni_rimasti <= 0;
  const urgencyClass = isExpired
    ? "border-l-red-500 bg-gradient-to-br from-red-50/60 to-white dark:from-red-950/20 dark:to-zinc-900"
    : item.giorni_rimasti <= 7
      ? "border-l-amber-500 bg-gradient-to-br from-amber-50/60 to-white dark:from-amber-950/20 dark:to-zinc-900"
      : "border-l-blue-400 bg-gradient-to-br from-blue-50/40 to-white dark:from-blue-950/20 dark:to-zinc-900";
  const daysLabel = isExpired
    ? `Scaduto da ${Math.abs(item.giorni_rimasti)}g`
    : item.giorni_rimasti === 1
      ? "Scade domani"
      : `Scade tra ${item.giorni_rimasti}g`;
  const creditProgress = item.crediti_totali > 0
    ? ((item.crediti_totali - item.crediti_residui) / item.crediti_totali) * 100
    : 0;

  return (
    <div className={`rounded-xl border border-l-4 ${urgencyClass} p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/clienti/${item.client_id}`}
              className="text-sm font-semibold hover:underline"
            >
              {item.client_nome} {item.client_cognome}
            </Link>
            <Badge
              variant={isExpired ? "destructive" : "outline"}
              className={`text-xs ${!isExpired && item.giorni_rimasti <= 7 ? "border-amber-300 bg-amber-50 text-amber-700 dark:bg-amber-900/30" : ""}`}
            >
              {daysLabel}
            </Badge>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>{item.tipo_pacchetto}</span>
            <span className="text-muted-foreground/40">·</span>
            <span>{item.crediti_residui}/{item.crediti_totali} crediti</span>
            {item.prezzo_totale ? (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span className="font-medium">{formatCurrency(item.prezzo_totale)}</span>
              </>
            ) : null}
          </div>
          {/* Progress bar crediti */}
          <div className="flex items-center gap-2">
            <Progress value={creditProgress} className="h-1.5 flex-1" />
            <span className="text-[10px] tabular-nums text-muted-foreground">{Math.round(creditProgress)}%</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <WhatsAppButton
            phone={item.client_telefono}
            message={waRenewalReminder(
              item.client_nome,
              trainerName,
              item.tipo_pacchetto || "allenamento",
              item.giorni_rimasti,
              item.crediti_residui,
            )}
            variant="icon"
          />
          <Button size="sm" asChild variant="ghost" className="text-xs">
            <Link href={`/contratti/${item.contract_id}`}>
              Dettaglio
              <ArrowRight className="ml-1 h-3 w-3" />
            </Link>
          </Button>
          <Button size="sm" onClick={() => onRenew(item)}>
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Rinnova
          </Button>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// OverdueRateCard — rata in ritardo con pagamento inline
// ════════════════════════════════════════════════════════════

function OverdueRateCard({ item, trainerName }: { item: OverdueRateItem; trainerName: string }) {
  const payRate = usePayRate();
  const [method, setMethod] = useState("CONTANTI");
  const isPaying = payRate.isPending;

  const handlePay = () => {
    payRate.mutate({
      rateId: item.rate_id,
      importo: item.importo_residuo,
      metodo: method,
      data_pagamento: toISOLocal(new Date()).slice(0, 10),
    });
  };

  const severityClass = item.giorni_ritardo > 30
    ? "border-l-red-600 bg-gradient-to-br from-red-50/80 to-white dark:from-red-950/30 dark:to-zinc-900"
    : item.giorni_ritardo > 7
      ? "border-l-red-400 bg-gradient-to-br from-red-50/50 to-white dark:from-red-950/20 dark:to-zinc-900"
      : "border-l-amber-500 bg-gradient-to-br from-amber-50/50 to-white dark:from-amber-950/20 dark:to-zinc-900";

  return (
    <div className={`rounded-xl border border-l-4 ${severityClass} p-4 shadow-sm transition-all duration-200 ${isPaying ? "scale-[0.98] opacity-50" : "hover:-translate-y-0.5 hover:shadow-md"}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/clienti/${item.client_id}`}
              className="text-sm font-semibold hover:underline"
            >
              {item.client_nome} {item.client_cognome}
            </Link>
            <WhatsAppButton
              phone={item.client_telefono}
              message={waRateReminder(item.client_nome, trainerName, item.importo_residuo, item.data_scadenza)}
              variant="icon"
            />
            <Badge variant="destructive" className="text-xs">
              {item.giorni_ritardo === 1
                ? "1 giorno"
                : `${item.giorni_ritardo} giorni`} di ritardo
            </Badge>
          </div>
          <p className="mt-1.5 text-xs text-muted-foreground">
            {item.tipo_pacchetto} · Scadenza {formatShortDate(item.data_scadenza)}
            {item.importo_saldato > 0
              ? ` · Versato ${formatCurrency(item.importo_saldato)}/${formatCurrency(item.importo_previsto)}`
              : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="whitespace-nowrap text-base font-bold text-red-600 tabular-nums dark:text-red-400">
            {formatCurrency(item.importo_residuo)}
          </span>
          <Select value={method} onValueChange={setMethod} disabled={isPaying}>
            <SelectTrigger className="h-8 w-[110px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper">
              {PAYMENT_METHODS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m === "CONTANTI" ? "Contanti" : m === "POS" ? "POS" : "Bonifico"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" onClick={handlePay} disabled={isPaying}>
            {isPaying ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <CreditCard className="mr-1.5 h-3.5 w-3.5" />
            )}
            Incassa
          </Button>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// RecoverCard — cliente da recuperare (lapsed) + dialog "Non rinnova"
// ════════════════════════════════════════════════════════════

function RecoverCard({
  item,
  onRenew,
  trainerName,
}: {
  item: ClientToRecoverItem;
  onRenew: (t: RenewTarget) => void;
  trainerName: string;
}) {
  const markOutcome = useMarkRenewalOutcome();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [motivo, setMotivo] = useState("");
  const [note, setNote] = useState("");

  const ritardoLabel = item.giorni_ritardo === 1
    ? "Scaduto da 1 giorno"
    : `Scaduto da ${item.giorni_ritardo} giorni`;

  const handleNonRinnova = () => {
    if (!motivo) return;
    markOutcome.mutate(
      { contractId: item.contract_id, motivo, note: note.trim() || undefined },
      { onSuccess: () => { setDialogOpen(false); setMotivo(""); setNote(""); } },
    );
  };

  return (
    <div className="rounded-xl border border-l-4 border-l-red-400 bg-gradient-to-br from-red-50/50 to-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md dark:from-red-950/20 dark:to-zinc-900">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <Link href={`/clienti/${item.client_id}`} className="text-sm font-semibold hover:underline">
              {item.client_nome} {item.client_cognome}
            </Link>
            <Badge variant="destructive" className="text-xs">{ritardoLabel}</Badge>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span>{item.tipo_pacchetto || "Contratto"}</span>
            {item.data_scadenza ? (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span>Scaduto il {formatShortDate(item.data_scadenza)}</span>
              </>
            ) : null}
            {item.residuo > 0 ? (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span className="font-medium">Residuo {formatCurrency(item.residuo)}</span>
              </>
            ) : null}
            {item.crediti_residui > 0 ? (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span>{item.crediti_residui} {item.crediti_residui === 1 ? "seduta" : "sedute"} non usate</span>
              </>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <WhatsAppButton
            phone={item.client_telefono}
            message={waCheckIn(item.client_nome, trainerName, item.giorni_ritardo)}
            variant="icon"
          />
          <Button size="sm" variant="ghost" className="text-xs" onClick={() => setDialogOpen(true)}>
            <UserMinus className="mr-1 h-3.5 w-3.5" />
            Non rinnova
          </Button>
          <Button size="sm" onClick={() => onRenew(item)}>
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Rinnova
          </Button>
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Non rinnova — {item.client_nome} {item.client_cognome}</DialogTitle>
            <DialogDescription>
              Registra il motivo. Il cliente esce dalla lista ma resta nello storico (reversibile).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Motivo</Label>
              <Select value={motivo} onValueChange={setMotivo}>
                <SelectTrigger><SelectValue placeholder="Seleziona motivo..." /></SelectTrigger>
                <SelectContent>
                  {MOTIVI_NON_RINNOVA.map((m) => (
                    <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Note (opzionale)</Label>
              <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Dettaglio..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Annulla</Button>
            <Button onClick={handleNonRinnova} disabled={!motivo || markOutcome.isPending}>
              {markOutcome.isPending ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
              Conferma
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SuspendedCard — contratto SOSPESO (sedute prepagate da erogare) + Estendi
// ════════════════════════════════════════════════════════════

function SuspendedCard({ item }: { item: SuspendedContractItem }) {
  const updateContract = useUpdateContract();
  const [extendOpen, setExtendOpen] = useState(false);
  const [incassaOpen, setIncassaOpen] = useState(false);
  const [terminateOpen, setTerminateOpen] = useState(false);
  const [newDate, setNewDate] = useState<Date | undefined>(undefined);
  const isExtending = updateContract.isPending;
  const hasResiduo = item.residuo > 0.009;

  const ritardoLabel = item.giorni_ritardo === 1
    ? "Sospeso da 1 giorno"
    : `Sospeso da ${item.giorni_ritardo} giorni`;

  const openExtend = () => {
    const d = new Date();
    d.setDate(d.getDate() + 30); // default: +30 giorni da oggi
    setNewDate(d);
    setExtendOpen(true);
  };

  const handleExtend = () => {
    if (!newDate) return;
    updateContract.mutate(
      { id: item.contract_id, data_scadenza: toISOLocal(newDate).slice(0, 10) },
      { onSuccess: () => setExtendOpen(false) },
    );
  };

  return (
    <div className="rounded-xl border border-l-4 border-l-violet-500 bg-gradient-to-br from-violet-50/50 to-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md dark:from-violet-950/20 dark:to-zinc-900">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <Link href={`/clienti/${item.client_id}`} className="text-sm font-semibold hover:underline">
              {item.client_nome} {item.client_cognome}
            </Link>
            <Badge className="border-violet-300 bg-violet-100 text-xs text-violet-700 dark:bg-violet-900/30 dark:text-violet-300" variant="outline">
              {ritardoLabel}
            </Badge>
          </div>
          {/* Doppio debito esplicito: sedute (asse crediti) ≠ denaro (asse denaro) — non un doppione */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span>{item.tipo_pacchetto || "Contratto"}</span>
            <span className="text-muted-foreground/40">·</span>
            <span className="font-medium text-violet-700 dark:text-violet-300">
              {item.crediti_residui} {item.crediti_residui === 1 ? "seduta" : "sedute"} da recuperare
            </span>
            {item.residuo > 0 ? (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span className="font-medium">Denaro da incassare {formatCurrency(item.residuo)}</span>
              </>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Termina contratto (G7.3): conguaglio derivato (rimborso o storno) + chiusura, in un atto.
              L'unico endpoint terminate copre sia "chiudi con conguaglio" sia "decadi": l'esito lo
              determina il calcolo pro-rata sedute (mostrato in anteprima). */}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setTerminateOpen(true)}
            className="text-xs text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-400 dark:hover:bg-rose-950/30"
            title="Termina il contratto con conguaglio"
          >
            <Lock className="mr-1 h-3 w-3" />
            Termina
          </Button>
          {/* Incassa residuo diretto (G6): denaro dovuto su contratto scaduto non rateizzabile */}
          {hasResiduo ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIncassaOpen(true)}
              className="text-xs"
            >
              <HandCoins className="mr-1.5 h-3.5 w-3.5" />
              Incassa {formatCurrency(item.residuo)}
            </Button>
          ) : null}
          <Button size="sm" onClick={openExtend} disabled={isExtending}>
            {isExtending ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <CalendarPlus className="mr-1.5 h-3.5 w-3.5" />
            )}
            Estendi
          </Button>
        </div>
      </div>

      {hasResiduo ? (
        <IncassaResiduoDialog
          contractId={incassaOpen ? item.contract_id : null}
          residuo={item.residuo}
          clientLabel={`${item.client_nome} ${item.client_cognome}`}
          open={incassaOpen}
          onOpenChange={setIncassaOpen}
        />
      ) : null}

      <TerminateContractDialog
        contractId={terminateOpen ? item.contract_id : null}
        clientLabel={`${item.client_nome} ${item.client_cognome}`}
        open={terminateOpen}
        onOpenChange={setTerminateOpen}
      />

      <Dialog open={extendOpen} onOpenChange={setExtendOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Estendi contratto — {item.client_nome} {item.client_cognome}</DialogTitle>
            <DialogDescription>
              Sposta la scadenza in avanti: il contratto torna attivo e le {item.crediti_residui} sedute
              residue restano erogabili.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label>Nuova scadenza</Label>
            <DatePicker value={newDate} onChange={setNewDate} minDate={new Date()} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExtendOpen(false)}>Annulla</Button>
            <Button onClick={handleExtend} disabled={!newDate || isExtending}>
              {isExtending ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
              Conferma
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Page
// ════════════════════════════════════════════════════════════

export default function RinnoviIncassiPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const overdueQuery = useOverdueRates();
  const expiringQuery = useExpiringContracts();
  const recoverQuery = useClientsToRecover();
  const suspendedQuery = useSuspendedContracts();

  const [renewSheet, setRenewSheet] = useState(false);
  const [renewItem, setRenewItem] = useState<RenewTarget | null>(null);

  const trainerName = useTrainerName();

  const overdueItems = overdueQuery.data?.items ?? [];
  const expiringItems = expiringQuery.data?.items ?? [];
  const recoverItems = recoverQuery.data?.items ?? [];
  const suspendedItems = suspendedQuery.data?.items ?? [];
  const isLoading = overdueQuery.isLoading || expiringQuery.isLoading || recoverQuery.isLoading || suspendedQuery.isLoading;
  const totalActions = overdueItems.length + expiringItems.length + recoverItems.length + suspendedItems.length;

  const totalOverdueAmount = overdueItems.reduce((sum, i) => sum + i.importo_residuo, 0);

  const handleRenew = (item: RenewTarget) => {
    setRenewItem(item);
    setRenewSheet(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="hidden h-20 rounded-xl lg:block" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className={revealClass(0)} style={revealStyle(0)}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-amber-100 to-amber-200 dark:from-amber-900/40 dark:to-amber-800/30">
              <HandCoins className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Rinnovi &amp; Incassi</h1>
              <p className="text-sm text-muted-foreground">
                {totalActions === 0
                  ? "Nessuna azione richiesta"
                  : `${totalActions} ${totalActions === 1 ? "azione richiesta" : "azioni richieste"}`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── KPI Strip ── */}
      {totalActions > 0 ? (
        <div className={`grid grid-cols-2 gap-4 lg:grid-cols-5 ${revealClass(30)}`} style={revealStyle(30)}>
          <KpiCard
            icon={RefreshCw}
            label="Da rinnovare"
            value={String(expiringItems.length)}
            sublabel={expiringItems.length > 0
              ? `${expiringItems.filter(i => i.giorni_rimasti <= 0).length} scaduti`
              : undefined}
            border="border-l-amber-500"
            bg="from-amber-50/80 to-white dark:from-amber-950/30 dark:to-zinc-900"
            iconBg="bg-amber-100 dark:bg-amber-900/50"
            iconColor="text-amber-600 dark:text-amber-400"
          />
          <KpiCard
            icon={PauseCircle}
            label="Sospesi"
            value={String(suspendedItems.length)}
            sublabel={suspendedItems.length > 0 ? "sedute da erogare" : undefined}
            border="border-l-violet-500"
            bg="from-violet-50/80 to-white dark:from-violet-950/30 dark:to-zinc-900"
            iconBg="bg-violet-100 dark:bg-violet-900/50"
            iconColor="text-violet-600 dark:text-violet-400"
          />
          <KpiCard
            icon={HeartHandshake}
            label="Da recuperare"
            value={String(recoverItems.length)}
            sublabel={recoverItems.length > 0 ? "clienti lapsed" : undefined}
            border="border-l-rose-500"
            bg="from-rose-50/80 to-white dark:from-rose-950/30 dark:to-zinc-900"
            iconBg="bg-rose-100 dark:bg-rose-900/50"
            iconColor="text-rose-600 dark:text-rose-400"
          />
          <KpiCard
            icon={TrendingDown}
            label="Rate in ritardo"
            value={String(overdueItems.length)}
            sublabel={overdueItems.length > 0
              ? `Max ${Math.max(...overdueItems.map(i => i.giorni_ritardo))}g ritardo`
              : undefined}
            border="border-l-red-500"
            bg="from-red-50/80 to-white dark:from-red-950/30 dark:to-zinc-900"
            iconBg="bg-red-100 dark:bg-red-900/50"
            iconColor="text-red-600 dark:text-red-400"
          />
          <KpiCard
            icon={Wallet}
            label="Da incassare"
            value={formatCurrency(totalOverdueAmount)}
            border="border-l-teal-500"
            bg="from-teal-50/80 to-white dark:from-teal-950/30 dark:to-zinc-900"
            iconBg="bg-teal-100 dark:bg-teal-900/50"
            iconColor="text-teal-600 dark:text-teal-400"
          />
        </div>
      ) : null}

      {/* ── Empty state ── */}
      {totalActions === 0 ? (
        <Card className={revealClass(60)} style={revealStyle(60)}>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900/40">
              <BadgeCheck className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h2 className="mt-5 text-lg font-semibold">Tutto in regola</h2>
            <p className="mt-2 max-w-sm text-sm text-muted-foreground">
              Nessun contratto da rinnovare e nessuna rata in ritardo.
            </p>
            <div className="mt-5 flex gap-2">
              <Button variant="outline" size="sm" asChild>
                <Link href="/contratti">
                  Contratti
                  <ArrowRight className="ml-1 h-3.5 w-3.5" />
                </Link>
              </Button>
              <Button variant="outline" size="sm" asChild>
                <Link href="/cassa">
                  Cassa
                  <ArrowRight className="ml-1 h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {/* ── Sezione: Contratti da rinnovare ── */}
      {expiringItems.length > 0 ? (
        <section className={revealClass(60)} style={revealStyle(60)}>
          <div className="mb-3 flex items-center gap-2">
            <RefreshCw className="h-4 w-4 text-amber-600" />
            <h2 className="text-sm font-semibold">
              Contratti da rinnovare
              <span className="ml-1.5 font-normal text-muted-foreground">
                ({expiringItems.length})
              </span>
            </h2>
          </div>
          <div className="space-y-2">
            {expiringItems.map((item) => (
              <RenewalCard key={item.contract_id} item={item} onRenew={handleRenew} trainerName={trainerName} />
            ))}
          </div>
        </section>
      ) : null}

      {/* ── Sezione: Contratti sospesi (sedute prepagate da erogare) ── */}
      {suspendedItems.length > 0 ? (
        <section className={revealClass(75)} style={revealStyle(75)}>
          <div className="mb-1 flex items-center gap-2">
            <PauseCircle className="h-4 w-4 text-violet-600" />
            <h2 className="text-sm font-semibold">
              Contratti sospesi
              <span className="ml-1.5 font-normal text-muted-foreground">
                ({suspendedItems.length})
              </span>
            </h2>
          </div>
          <p className="mb-3 text-xs text-muted-foreground">
            Scaduti con sedute prepagate ancora da erogare — gliele devi. Estendi per riattivarli.
          </p>
          <div className="space-y-2">
            {suspendedItems.map((item) => (
              <SuspendedCard key={item.contract_id} item={item} />
            ))}
          </div>
        </section>
      ) : null}

      {/* ── Sezione: Crediti da incassare (post-chiusura, G7.10) — auto-nascosta se vuota ── */}
      <CreditiDaIncassareCard />

      {/* ── Sezione: Clienti da recuperare (lapsed) ── */}
      {recoverItems.length > 0 ? (
        <section className={revealClass(90)} style={revealStyle(90)}>
          <div className="mb-1 flex items-center gap-2">
            <HeartHandshake className="h-4 w-4 text-rose-600" />
            <h2 className="text-sm font-semibold">
              Clienti da recuperare
              <span className="ml-1.5 font-normal text-muted-foreground">
                ({recoverItems.length})
              </span>
            </h2>
          </div>
          <p className="mb-3 text-xs text-muted-foreground">
            Contratto scaduto e nessuna copertura attiva — opportunità di win-back.
          </p>
          <div className="space-y-2">
            {recoverItems.map((item) => (
              <RecoverCard key={item.client_id} item={item} onRenew={handleRenew} trainerName={trainerName} />
            ))}
          </div>
        </section>
      ) : null}

      {/* ── Sezione: Rate in ritardo ── */}
      {overdueItems.length > 0 ? (
        <section className={revealClass(120)} style={revealStyle(120)}>
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <h2 className="text-sm font-semibold">
              Incassi in ritardo
              <span className="ml-1.5 font-normal text-muted-foreground">
                ({overdueItems.length})
              </span>
            </h2>
          </div>
          <div className="space-y-2">
            {overdueItems.map((item) => (
              <OverdueRateCard key={item.rate_id} item={item} trainerName={trainerName} />
            ))}
          </div>
        </section>
      ) : null}

      {/* ── Quick links ── */}
      {totalActions > 0 ? (
        <div className={`flex flex-wrap gap-2 ${revealClass(180)}`} style={revealStyle(180)}>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/contratti">
              Tutti i contratti
              <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/cassa">
              Libro mastro
              <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      ) : null}

      {/* Sheet rinnovo — pre-compilato con dati del contratto scadente */}
      <ContractSheet
        open={renewSheet}
        onOpenChange={setRenewSheet}
        contract={null}
        renewContractId={renewItem?.contract_id}
        renewalDefaults={renewItem ? {
          id_cliente: renewItem.client_id,
          tipo_pacchetto: renewItem.tipo_pacchetto ?? "",
          crediti_totali: renewItem.crediti_totali,
          prezzo_totale: renewItem.prezzo_totale ?? 0,
          data_inizio: renewItem.data_inizio,
          data_scadenza: renewItem.data_scadenza,
        } : undefined}
      />
    </div>
  );
}
