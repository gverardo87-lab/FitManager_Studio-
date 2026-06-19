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
  CreditCard,
  HandCoins,
  Loader2,
  RefreshCw,
  TrendingDown,
  Wallet,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { WhatsAppButton } from "@/components/ui/whatsapp-button";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { useOverdueRates, useExpiringContracts } from "@/hooks/useDashboard";
import { usePayRate } from "@/hooks/useRates";
import { useTrainerName } from "@/hooks/useTrainerName";
import { usePageReveal } from "@/lib/page-reveal";
import { formatCurrency, formatShortDate, toISOLocal } from "@/lib/format";
import { waRenewalReminder, waRateReminder } from "@/lib/whatsapp-templates";
import type { ExpiringContractItem, OverdueRateItem } from "@/types/api";

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
// Page
// ════════════════════════════════════════════════════════════

export default function RinnoviIncassiPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const overdueQuery = useOverdueRates();
  const expiringQuery = useExpiringContracts();

  const [renewSheet, setRenewSheet] = useState(false);
  const [renewItem, setRenewItem] = useState<ExpiringContractItem | null>(null);

  const trainerName = useTrainerName();

  const overdueItems = overdueQuery.data?.items ?? [];
  const expiringItems = expiringQuery.data?.items ?? [];
  const isLoading = overdueQuery.isLoading || expiringQuery.isLoading;
  const totalActions = overdueItems.length + expiringItems.length;

  const totalOverdueAmount = overdueItems.reduce((sum, i) => sum + i.importo_residuo, 0);

  const handleRenew = (item: ExpiringContractItem) => {
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
        <div className={`grid grid-cols-2 gap-4 lg:grid-cols-3 ${revealClass(30)}`} style={revealStyle(30)}>
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
