// src/app/(dashboard)/cassa/page.tsx
"use client";

/**
 * Pagina Cassa — Financial Intelligence Dashboard.
 *
 * Layout:
 * 1. Header con filtri globali Mese/Anno
 * 2. Saldo Hero: card teal prominente con saldo attuale + sub-KPI mese
 * 3. Hero Section: 4 KPI cards (Entrate, Uscite Var, Uscite Fisse, Margine Netto)
 * 4. ComposedChart giornaliero: barre Entrate/Uscite + linea Saldo
 * 5. Tabs: "Libro Mastro" (tabella movimenti) + "Spese Fisse" (ricorrenti)
 */

import { useState, useEffect, useCallback } from "react";
import { format, parseISO } from "date-fns";
import { loadFilters, saveFilters, getUrlParams, syncUrlParams } from "@/lib/url-state";
import { PageVideoGuide } from "@/components/guide/PageVideoGuide";
import { usePageReveal } from "@/lib/page-reveal";
import {
  Plus,
  Landmark,
  TrendingUp,
  TrendingDown,
  Building2,
  Target,
  BookOpen,
  CalendarClock,
  ArrowLeftRight,
  Clock,
  LineChart,
  Wallet,
  FileSearch,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
} from "lucide-react";
import {
  Bar,
  ComposedChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Line,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DatePicker } from "@/components/ui/date-picker";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { MovementsTable } from "@/components/movements/MovementsTable";
import { MovementSheet } from "@/components/movements/MovementSheet";
import { DeleteMovementDialog } from "@/components/movements/DeleteMovementDialog";
import { RecurringExpensesTab } from "@/components/movements/RecurringExpensesTab";
import { SplitLedgerView } from "@/components/movements/SplitLedgerView";
import { AgingReport } from "@/components/movements/AgingReport";
import { ForecastTab } from "@/components/movements/ForecastTab";
import { AndamentoTab } from "@/components/movements/AndamentoTab";
import { CashAuditSheet } from "@/components/movements/CashAuditSheet";
import { GradientKpiCard, resolveMarginColors } from "@/components/movements/GradientKpiCard";
import { useMovements, useMovementStats, usePendingExpenses, useCashBalance } from "@/hooks/useMovements";
import type { CashMovement, CashProtection } from "@/types/api";
import { formatCurrency } from "@/lib/format";
import { AnimatedNumber } from "@/components/ui/animated-number";

// ── Costanti ──

const MESI = [
  { value: "1", label: "Gennaio" },
  { value: "2", label: "Febbraio" },
  { value: "3", label: "Marzo" },
  { value: "4", label: "Aprile" },
  { value: "5", label: "Maggio" },
  { value: "6", label: "Giugno" },
  { value: "7", label: "Luglio" },
  { value: "8", label: "Agosto" },
  { value: "9", label: "Settembre" },
  { value: "10", label: "Ottobre" },
  { value: "11", label: "Novembre" },
  { value: "12", label: "Dicembre" },
] as const;

type LedgerMovementFilter = "ALL" | "ENTRATA" | "USCITA";
type CassaTabKey = "ledger" | "recurring" | "split" | "aging" | "forecast" | "trend";
const CASSA_TAB_SET: ReadonlySet<CassaTabKey> = new Set([
  "ledger",
  "recurring",
  "split",
  "aging",
  "forecast",
  "trend",
]);

function isValidIsoDate(v: string | null): v is string {
  if (!v) return false;
  return /^\d{4}-\d{2}-\d{2}$/.test(v);
}

function parsePositiveInt(v: string | null): number | null {
  if (!v) return null;
  const parsed = Number.parseInt(v, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function parseLedgerTipo(v: string | null): LedgerMovementFilter {
  if (v === "ENTRATA" || v === "USCITA") return v;
  return "ALL";
}

function parseCassaTab(v: string | null): CassaTabKey {
  if (v && CASSA_TAB_SET.has(v as CassaTabKey)) return v as CassaTabKey;
  return "ledger";
}

function getYearRange(): number[] {
  const current = new Date().getFullYear();
  return Array.from({ length: 5 }, (_, i) => current - 2 + i);
}

const chartConfig: ChartConfig = {
  entrate: {
    label: "Entrate",
    color: "var(--color-emerald-500)",
  },
  uscite: {
    label: "Uscite",
    color: "var(--color-red-500)",
  },
  saldo: {
    label: "Saldo",
    color: "oklch(0.52 0.14 173)",
  },
};

// ════════════════════════════════════════════════════════════
// Pagina
// ════════════════════════════════════════════════════════════

export default function CassaPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const now = new Date();
  const currentMonth = now.getMonth() + 1;
  const currentYear = now.getFullYear();
  const deepLinkFocusId = parsePositiveInt(getUrlParams().get("focus_movement"));
  const hasFocusDeepLink = deepLinkFocusId !== null;

  // Filter state (sessionStorage → URL → default)
  const [mese, setMese] = useState(() => {
    const saved = loadFilters("cassa");
    if (saved?.mese != null) return saved.mese as number;
    const m = getUrlParams().get("mese");
    return m ? parseInt(m, 10) : currentMonth;
  });
  const [anno, setAnno] = useState(() => {
    const saved = loadFilters("cassa");
    if (saved?.anno != null) return saved.anno as number;
    const a = getUrlParams().get("anno");
    return a ? parseInt(a, 10) : currentYear;
  });
  const [activeTab, setActiveTab] = useState(() => {
    const fromUrl = getUrlParams().get("tab");
    if (hasFocusDeepLink) return fromUrl ?? "ledger";
    const saved = loadFilters("cassa");
    if (saved?.tab) return saved.tab as string;
    return fromUrl ?? "ledger";
  });
  const [ledgerTipo, setLedgerTipo] = useState<LedgerMovementFilter>(() => {
    const saved = loadFilters("cassa");
    const fromSaved = saved?.ledger_tipo;
    if (fromSaved === "ENTRATA" || fromSaved === "USCITA" || fromSaved === "ALL") {
      return fromSaved;
    }
    const fromUrl = getUrlParams().get("tipo");
    if (fromUrl === "ENTRATA" || fromUrl === "USCITA") return fromUrl;
    return "ALL";
  });
  const [ledgerDataDa, setLedgerDataDa] = useState(() => {
    const fromUrl = getUrlParams().get("da");
    if (hasFocusDeepLink && isValidIsoDate(fromUrl)) return fromUrl;
    const saved = loadFilters("cassa");
    const fromSaved = typeof saved?.ledger_da === "string" ? saved.ledger_da : null;
    if (isValidIsoDate(fromSaved)) return fromSaved;
    return isValidIsoDate(fromUrl) ? fromUrl : "";
  });
  const [ledgerDataA, setLedgerDataA] = useState(() => {
    const fromUrl = getUrlParams().get("a");
    if (hasFocusDeepLink && isValidIsoDate(fromUrl)) return fromUrl;
    const saved = loadFilters("cassa");
    const fromSaved = typeof saved?.ledger_a === "string" ? saved.ledger_a : null;
    if (isValidIsoDate(fromSaved)) return fromSaved;
    return isValidIsoDate(fromUrl) ? fromUrl : "";
  });
  const [focusedMovementId, setFocusedMovementId] = useState<number | null>(() => {
    return deepLinkFocusId;
  });

  const [sheetOpen, setSheetOpen] = useState(false);
  const [auditSheetOpen, setAuditSheetOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectedMovement, setSelectedMovement] =
    useState<CashMovement | null>(null);

  const hasLedgerDateRange = Boolean(ledgerDataDa || ledgerDataA);
  const hasLedgerAdvancedFilters = ledgerTipo !== "ALL" || hasLedgerDateRange;

  const { data: movementsData, isLoading: movementsLoading, isError, refetch } =
    useMovements({
      anno,
      mese,
      tipo: ledgerTipo === "ALL" ? undefined : ledgerTipo,
      data_da: ledgerDataDa || undefined,
      data_a: ledgerDataA || undefined,
    });
  const { data: stats, isLoading: statsLoading } =
    useMovementStats(anno, mese);
  const { data: pendingData } = usePendingExpenses(anno, mese);
  const { data: balance, isLoading: balanceLoading } = useCashBalance();
  const pendingCount = pendingData?.items.length ?? 0;
  const handleFocusConsumed = useCallback(() => {
    setFocusedMovementId(null);
  }, []);
  const handleNavigateInCashFromAudit = useCallback((href: string) => {
    let url: URL;
    try {
      url = new URL(href, window.location.origin);
    } catch {
      return;
    }

    if (url.pathname !== "/cassa") return;

    const nextTab = parseCassaTab(url.searchParams.get("tab"));
    setActiveTab(nextTab);

    if (nextTab === "ledger") {
      const nextDa = url.searchParams.get("da");
      const nextA = url.searchParams.get("a");
      setLedgerTipo(parseLedgerTipo(url.searchParams.get("tipo")));
      setLedgerDataDa(isValidIsoDate(nextDa) ? nextDa : "");
      setLedgerDataA(isValidIsoDate(nextA) ? nextA : "");
      setFocusedMovementId(parsePositiveInt(url.searchParams.get("focus_movement")));
    } else {
      setFocusedMovementId(null);
    }

    setAuditSheetOpen(false);
  }, []);

  // ── Sync filtri → sessionStorage + URL (feedback visivo) ──
  useEffect(() => {
    saveFilters("cassa", {
      mese: mese !== currentMonth ? mese : null,
      anno: anno !== currentYear ? anno : null,
      tab: activeTab !== "ledger" ? activeTab : null,
      ledger_tipo: ledgerTipo !== "ALL" ? ledgerTipo : null,
      ledger_da: ledgerDataDa || null,
      ledger_a: ledgerDataA || null,
    });
    const params = new URLSearchParams();
    if (mese !== currentMonth || anno !== currentYear) {
      params.set("mese", String(mese));
      params.set("anno", String(anno));
    }
    if (activeTab !== "ledger") params.set("tab", activeTab);
    if (ledgerTipo !== "ALL") params.set("tipo", ledgerTipo);
    if (ledgerDataDa) params.set("da", ledgerDataDa);
    if (ledgerDataA) params.set("a", ledgerDataA);
    if (focusedMovementId) params.set("focus_movement", String(focusedMovementId));
    syncUrlParams(window.location.pathname, params);
  }, [
    mese,
    anno,
    activeTab,
    ledgerTipo,
    ledgerDataDa,
    ledgerDataA,
    focusedMovementId,
    currentMonth,
    currentYear,
  ]);

  const handleDelete = (movement: CashMovement) => {
    setSelectedMovement(movement);
    setDeleteOpen(true);
  };
  const handleResetLedgerFilters = () => {
    setLedgerTipo("ALL");
    setLedgerDataDa("");
    setLedgerDataA("");
  };

  const meseLabel = MESI.find((m) => m.value === String(mese))?.label ?? "";
  const periodLabel = hasLedgerDateRange
    ? `${ledgerDataDa || "inizio"} -> ${ledgerDataA || "oggi"}`
    : `${meseLabel} ${anno}`;

  return (
    <div className="space-y-6">
      {/* ── Header + Filtri ── */}
      <div data-guide="cassa-header" className={revealClass(0, "flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between")} style={revealStyle(0)}>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-200 dark:from-emerald-900/40 dark:to-emerald-800/30">
            <Landmark className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Cassa</h1>
            <p className="text-sm text-muted-foreground">
              {periodLabel}
              {movementsData && ` — ${movementsData.total} movimenti`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <PageVideoGuide />
          <Select
            value={String(mese)}
            onValueChange={(v) => setMese(parseInt(v, 10))}
          >
            <SelectTrigger className="w-[120px] sm:w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MESI.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={String(anno)}
            onValueChange={(v) => setAnno(parseInt(v, 10))}
          >
            <SelectTrigger className="w-[80px] sm:w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {getYearRange().map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            onClick={() => setAuditSheetOpen(true)}
            className="gap-1.5"
          >
            <FileSearch className="h-4 w-4" />
            <span className="hidden sm:inline">Registro Modifiche</span>
          </Button>

          <Button data-guide="cassa-new-button" onClick={() => setSheetOpen(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white">
            <Plus className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">Nuovo Movimento</span>
          </Button>
        </div>
      </div>

      {/* ── Saldo Hero (dominant, inverted) ── */}
      <div className={revealClass(50)} style={revealStyle(50)}>
        {(balanceLoading || statsLoading) && (
          <Skeleton className="h-44 w-full rounded-2xl" />
        )}
        {balance && stats && (
          <SaldoHeroCard
            saldoAttuale={balance.saldo_attuale}
            margineMese={stats.margine_netto}
            protectionStatus={balance.protezione_cassa.stato}
          />
        )}
      </div>

      {/* ── Context Strip (secondary reference data) ── */}
      {balance && stats && (
        <div className={revealClass(80)} style={revealStyle(80)}>
          <BalanceContextStrip
            saldoInizioMese={stats.saldo_inizio_mese}
            saldoFineMese={stats.saldo_fine_mese}
            saldoPrevisto={balance.saldo_previsto}
            deltaMovimentiFuturi={balance.delta_movimenti_futuri}
            protection={balance.protezione_cassa}
          />
        </div>
      )}

      {/* ── KPI Mese ── */}
      <div className={revealClass(100)} style={revealStyle(100)}>
        {statsLoading && <KpiSkeleton />}
        {stats && <KpiCards stats={stats} />}
      </div>

      {/* ── Grafico Entrate vs Uscite + Saldo ── */}
      {stats && stats.chart_data.length > 0 && (
        <div className={revealClass(150)} style={revealStyle(150)}>
          <DailyChart data={stats.chart_data} meseLabel={meseLabel} />
        </div>
      )}

      {/* ── Tabs: Libro Mastro + Spese Fisse ── */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className={revealClass(200, "w-full")} style={revealStyle(200)}>
        <TabsList className="w-full overflow-x-auto bg-muted/50 p-1">
          <TabsTrigger value="ledger" className="flex-1 gap-1 px-2 sm:gap-1.5 sm:px-3">
            <BookOpen className="h-3.5 w-3.5 shrink-0" />
            <span className="text-[11px] sm:text-sm">Mastro</span>
          </TabsTrigger>
          <TabsTrigger value="recurring" className="flex-1 gap-1 px-2 sm:gap-1.5 sm:px-3">
            <CalendarClock className="h-3.5 w-3.5 shrink-0" />
            <span className="text-[11px] sm:text-sm"><span className="sm:hidden">Fisse</span><span className="hidden sm:inline">Spese Fisse</span></span>
            {pendingCount > 0 && (
              <Badge variant="destructive" className="ml-0.5 h-5 min-w-5 px-1.5 text-[10px] sm:ml-1">
                {pendingCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="split" className="flex-1 gap-1 px-2 sm:gap-1.5 sm:px-3">
            <ArrowLeftRight className="h-3.5 w-3.5 shrink-0" />
            <span className="text-[11px] sm:text-sm"><span className="sm:hidden">E&U</span><span className="hidden sm:inline">Entrate & Uscite</span></span>
          </TabsTrigger>
          <TabsTrigger value="aging" className="flex-1 gap-1 px-2 sm:gap-1.5 sm:px-3">
            <Clock className="h-3.5 w-3.5 shrink-0" />
            <span className="text-[11px] sm:text-sm"><span className="sm:hidden">Scad.</span><span className="hidden sm:inline">Scadenze</span></span>
          </TabsTrigger>
          <TabsTrigger value="forecast" className="flex-1 gap-1 px-2 sm:gap-1.5 sm:px-3">
            <LineChart className="h-3.5 w-3.5 shrink-0" />
            <span className="text-[11px] sm:text-sm"><span className="sm:hidden">Prev.</span><span className="hidden sm:inline">Previsioni</span></span>
          </TabsTrigger>
          <TabsTrigger value="trend" className="flex-1 gap-1 px-2 sm:gap-1.5 sm:px-3">
            <TrendingUp className="h-3.5 w-3.5 shrink-0" />
            <span className="text-[11px] sm:text-sm"><span className="sm:hidden">Trend</span><span className="hidden sm:inline">Andamento</span></span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ledger" className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <LedgerFiltersBar
            tipo={ledgerTipo}
            dataDa={ledgerDataDa}
            dataA={ledgerDataA}
            onTipoChange={setLedgerTipo}
            onDataDaChange={setLedgerDataDa}
            onDataAChange={setLedgerDataA}
            onReset={handleResetLedgerFilters}
            hasAdvancedFilters={hasLedgerAdvancedFilters}
          />

          {isError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
              <p className="text-destructive">
                Errore nel caricamento dei movimenti.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => refetch()}
              >
                Riprova
              </Button>
            </div>
          )}

          {movementsLoading && <TableSkeleton />}

          {movementsData && (
            <MovementsTable
              movements={movementsData.items}
              onDelete={handleDelete}
              focusMovementId={focusedMovementId}
              onFocusConsumed={handleFocusConsumed}
              saldoFinePeriodo={
                ledgerTipo === "ALL" ? movementsData.saldo_fine_periodo : undefined
              }
            />
          )}
        </TabsContent>

        <TabsContent value="recurring" className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <RecurringExpensesTab anno={anno} mese={mese} />
        </TabsContent>

        <TabsContent value="split" className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <SplitLedgerView />
        </TabsContent>

        <TabsContent value="aging" className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <AgingReport />
        </TabsContent>

        <TabsContent value="forecast" className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <ForecastTab />
        </TabsContent>

        <TabsContent value="trend" className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <AndamentoTab />
        </TabsContent>
      </Tabs>

      {/* ── Modals ── */}
      <MovementSheet open={sheetOpen} onOpenChange={setSheetOpen} />
      <DeleteMovementDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        movement={selectedMovement}
      />
      <CashAuditSheet
        open={auditSheetOpen}
        onOpenChange={setAuditSheetOpen}
        onNavigateInCash={handleNavigateInCashFromAudit}
      />
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Saldo Hero Card
// ════════════════════════════════════════════════════════════

function LedgerFiltersBar({
  tipo,
  dataDa,
  dataA,
  onTipoChange,
  onDataDaChange,
  onDataAChange,
  onReset,
  hasAdvancedFilters,
}: {
  tipo: LedgerMovementFilter;
  dataDa: string;
  dataA: string;
  onTipoChange: (v: LedgerMovementFilter) => void;
  onDataDaChange: (v: string) => void;
  onDataAChange: (v: string) => void;
  onReset: () => void;
  hasAdvancedFilters: boolean;
}) {
  return (
    <div className="mb-4 rounded-lg border bg-muted/20 p-3">
      <div className="flex flex-col gap-3 md:flex-row md:items-end">
        <div className="w-full md:w-[180px]">
          <p className="mb-1 text-xs font-medium text-muted-foreground">Tipo</p>
          <Select value={tipo} onValueChange={(v) => onTipoChange(v as LedgerMovementFilter)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Tutti i movimenti</SelectItem>
              <SelectItem value="ENTRATA">Solo entrate</SelectItem>
              <SelectItem value="USCITA">Solo uscite</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="w-full md:w-[180px]">
          <p className="mb-1 text-xs font-medium text-muted-foreground">Data da</p>
          <DatePicker
            value={dataDa ? parseISO(dataDa) : undefined}
            onChange={(d) => onDataDaChange(d ? format(d, "yyyy-MM-dd") : "")}
            placeholder="Data inizio..."
          />
        </div>

        <div className="w-full md:w-[180px]">
          <p className="mb-1 text-xs font-medium text-muted-foreground">Data a</p>
          <DatePicker
            value={dataA ? parseISO(dataA) : undefined}
            onChange={(d) => onDataAChange(d ? format(d, "yyyy-MM-dd") : "")}
            placeholder="Data fine..."
          />
        </div>

        <Button
          variant="outline"
          size="sm"
          className="md:ml-auto"
          onClick={onReset}
          disabled={!hasAdvancedFilters}
        >
          Reset filtri
        </Button>
      </div>

      {tipo !== "ALL" && (
        <p className="mt-2 text-xs text-muted-foreground">
          Saldo per riga nascosto con filtro tipo attivo (entrate/uscite).
        </p>
      )}
    </div>
  );
}

function SaldoHeroCard({
  saldoAttuale,
  margineMese,
  protectionStatus,
}: {
  saldoAttuale: number;
  margineMese: number;
  protectionStatus: "OK" | "ATTENZIONE" | "CRITICO";
}) {
  const isPositive = saldoAttuale >= 0;
  const marginePositive = margineMese >= 0;

  const pb = PROTECTION_BADGE[protectionStatus];
  const ProtectionIcon = pb.icon;

  return (
    <div className="rounded-2xl border border-teal-200/60 bg-gradient-to-br from-teal-50/90 via-white to-teal-50/40 px-6 py-8 shadow-sm sm:px-8 sm:py-10 dark:border-teal-800/40 dark:from-teal-950/40 dark:via-zinc-900 dark:to-teal-950/20">
      <div className="flex flex-col items-center gap-4 text-center">
        {/* Label + protection badge */}
        <div className="flex items-center gap-2.5">
          <Wallet className="h-4 w-4 text-teal-500/70 dark:text-teal-400/60" />
          <p className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
            Saldo di Cassa
          </p>
          <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${pb.cls}`}>
            <ProtectionIcon className="h-3 w-3" />
            {pb.label}
          </span>
        </div>

        {/* Main number */}
        <AnimatedNumber
          value={saldoAttuale}
          format="currency"
          className={`text-5xl font-extrabold tracking-tighter tabular-nums sm:text-6xl ${
            isPositive ? "text-teal-800 dark:text-teal-300" : "text-red-700 dark:text-red-400"
          }`}
        />

        {/* Monthly delta pill */}
        <div className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1 text-sm font-semibold ${
          marginePositive
            ? "bg-emerald-100/80 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
            : "bg-red-100/80 text-red-700 dark:bg-red-500/15 dark:text-red-400"
        }`}>
          {marginePositive ? (
            <TrendingUp className="h-3.5 w-3.5" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5" />
          )}
          {marginePositive ? "+" : ""}{formatCurrency(margineMese)} questo mese
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Protection badge config (shared by SaldoHeroCard)
// ════════════════════════════════════════════════════════════

const PROTECTION_BADGE = {
  OK: { label: "Protetta", icon: ShieldCheck, cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400" },
  ATTENZIONE: { label: "Attenzione", icon: ShieldAlert, cls: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400" },
  CRITICO: { label: "Critica", icon: ShieldX, cls: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400" },
} as const;

// ════════════════════════════════════════════════════════════
// Balance Context Strip (secondary reference data)
// ════════════════════════════════════════════════════════════

function BalanceContextStrip({
  saldoInizioMese,
  saldoFineMese,
  saldoPrevisto,
  deltaMovimentiFuturi,
  protection,
}: {
  saldoInizioMese: number;
  saldoFineMese: number;
  saldoPrevisto: number;
  deltaMovimentiFuturi: number;
  protection: CashProtection;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      <ContextCell label="Inizio Mese" value={formatCurrency(saldoInizioMese)} />
      <ContextCell label="Fine Mese" value={formatCurrency(saldoFineMese)} />
      <ContextCell
        label="Previsto"
        value={formatCurrency(saldoPrevisto)}
        sub={`${deltaMovimentiFuturi >= 0 ? "+" : ""}${formatCurrency(deltaMovimentiFuturi)} futuri`}
        subPositive={deltaMovimentiFuturi >= 0}
      />
      <ContextCell
        label="Copertura"
        value={`${protection.copertura_giorni.toFixed(0)} giorni`}
      />
      <ContextCell
        label="Costo Operativo"
        value={formatCurrency(protection.costo_operativo_mensile)}
        sub="/mese"
      />
    </div>
  );
}

function ContextCell({
  label,
  value,
  sub,
  subPositive,
}: {
  label: string;
  value: string;
  sub?: string;
  subPositive?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-muted/30 px-3 py-2.5">
      <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className="text-sm font-bold tabular-nums text-foreground">{value}</p>
      {sub != null && (
        <p className={`text-[10px] tabular-nums ${
          subPositive !== undefined
            ? (subPositive ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400")
            : "text-muted-foreground"
        }`}>
          {sub}
        </p>
      )}
    </div>
  );
}

// KPI Cards
// ════════════════════════════════════════════════════════════

type KpiKey = "totale_entrate" | "totale_uscite_variabili" | "totale_uscite_fisse" | "margine_netto";

interface CassaKpiDef {
  key: KpiKey;
  label: string;
  icon: typeof TrendingUp;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
  isMargin?: boolean;
}

const CASSA_KPI: CassaKpiDef[] = [
  {
    key: "totale_entrate",
    label: "Entrate",
    icon: TrendingUp,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "totale_uscite_variabili",
    label: "Uscite Variabili",
    icon: TrendingDown,
    borderColor: "border-l-red-500",
    gradient: "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900",
    iconBg: "bg-red-100 dark:bg-red-900/30",
    iconColor: "text-red-600 dark:text-red-400",
    valueColor: "text-red-700 dark:text-red-400",
  },
  {
    key: "totale_uscite_fisse",
    label: "Uscite Fisse",
    icon: Building2,
    borderColor: "border-l-orange-500",
    gradient: "from-orange-50/80 to-white dark:from-orange-950/40 dark:to-zinc-900",
    iconBg: "bg-orange-100 dark:bg-orange-900/30",
    iconColor: "text-orange-600 dark:text-orange-400",
    valueColor: "text-orange-700 dark:text-orange-400",
  },
  {
    key: "margine_netto",
    label: "Margine Netto",
    icon: Target,
    borderColor: "", gradient: "", iconBg: "", iconColor: "", valueColor: "",
    isMargin: true,
  },
];

function KpiCards({
  stats,
}: {
  stats: {
    totale_entrate: number;
    totale_uscite_variabili: number;
    totale_uscite_fisse: number;
    margine_netto: number;
  };
}) {
  const margin = resolveMarginColors(stats.margine_netto >= 0);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {CASSA_KPI.map((kpi) => {
        const Icon = kpi.icon;
        const bc = kpi.isMargin ? margin.borderColor : kpi.borderColor;
        const gr = kpi.isMargin ? margin.gradient : kpi.gradient;
        const ib = kpi.isMargin ? margin.iconBg : kpi.iconBg;
        const ic = kpi.isMargin ? margin.iconColor : kpi.iconColor;
        const vc = kpi.isMargin ? margin.valueColor : kpi.valueColor;

        return (
          <GradientKpiCard
            key={kpi.key}
            icon={<Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${ic}`} />}
            iconBg={ib}
            label={kpi.label}
            value={
              <AnimatedNumber
                value={stats[kpi.key]}
                format="currency"
                className={`text-xl font-extrabold tracking-tighter tabular-nums sm:text-3xl ${vc}`}
              />
            }
            sub="questo mese"
            borderColor={bc}
            gradient={gr}
          />
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Grafico giornaliero (ComposedChart: barre + linea saldo)
// ════════════════════════════════════════════════════════════

function DailyChart({
  data,
  meseLabel,
}: {
  data: { giorno: number; entrate: number; uscite: number; saldo: number }[];
  meseLabel: string;
}) {
  const hasData = data.some((d) => d.entrate > 0 || d.uscite > 0);
  if (!hasData) return null;

  const giorniAttivi = data.filter((d) => d.entrate > 0 || d.uscite > 0).length;

  return (
    <div className="rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 p-5 shadow-sm dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">
            Andamento Giornaliero — {meseLabel}
          </h3>
          <p className="text-xs text-muted-foreground">
            Entrate e uscite per giorno + saldo progressivo
          </p>
        </div>
        <Badge variant="outline" className="text-[10px]">
          {giorniAttivi} giorni attivi
        </Badge>
      </div>

      <ChartContainer config={chartConfig} className="h-[200px] w-full sm:h-[280px]">
        <ComposedChart data={data} accessibilityLayer>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="giorno"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={11}
          />
          <YAxis
            yAxisId="bars"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={11}
            tickFormatter={(v) => `\u20AC${v}`}
          />
          <YAxis
            yAxisId="saldo"
            orientation="right"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            fontSize={10}
            tickFormatter={(v) => `\u20AC${v}`}
          />
          <ChartTooltip
            cursor={{ fill: "var(--color-muted)", opacity: 0.3 }}
            content={({ payload, label }) => {
              if (!payload?.length) return null;
              return (
                <div className="rounded-lg border bg-white p-3 shadow-md dark:bg-zinc-900">
                  <p className="mb-1.5 text-xs font-semibold text-muted-foreground">
                    Giorno {label}
                  </p>
                  {payload.map((entry) => {
                    const nameMap: Record<string, string> = {
                      entrate: "Entrate",
                      uscite: "Uscite",
                      saldo: "Saldo",
                    };
                    return (
                      <div key={entry.name} className="flex items-center gap-2 text-sm">
                        <div
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-muted-foreground">
                          {nameMap[entry.name as string] ?? entry.name}
                        </span>
                        <span className="ml-auto font-bold tabular-nums">
                          {formatCurrency(Number(entry.value))}
                        </span>
                      </div>
                    );
                  })}
                </div>
              );
            }}
          />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar
            yAxisId="bars"
            dataKey="entrate"
            fill="var(--color-emerald-500)"
            radius={[4, 4, 2, 2]}
            maxBarSize={20}
            animationBegin={0}
            animationDuration={800}
          />
          <Bar
            yAxisId="bars"
            dataKey="uscite"
            fill="var(--color-red-500)"
            radius={[4, 4, 2, 2]}
            maxBarSize={20}
            animationBegin={100}
            animationDuration={800}
          />
          <Line
            yAxisId="saldo"
            dataKey="saldo"
            type="monotone"
            stroke="oklch(0.52 0.14 173)"
            strokeWidth={2}
            dot={false}
            animationBegin={200}
            animationDuration={1000}
          />
        </ComposedChart>
      </ChartContainer>
    </div>
  );
}

// ── Skeletons ──

function KpiSkeleton() {
  const borders = ["border-l-emerald-500", "border-l-red-500", "border-l-orange-500", "border-l-blue-500"];
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {borders.map((border, i) => (
        <div key={i} className={`flex items-start gap-3 rounded-xl border border-l-4 ${border} p-4`}>
          <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-2 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
