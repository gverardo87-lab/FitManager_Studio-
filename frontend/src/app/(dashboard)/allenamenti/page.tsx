// src/app/(dashboard)/allenamenti/page.tsx
"use client";

/**
 * Pagina Monitoraggio Allenamenti — v3 (card overview + calendario).
 *
 * Card compatte per ogni programma con stato, cliente, CTA "Calendario".
 * La compliance e la gestione sessioni vivono in /allenamenti/[id] (calendario).
 *
 * Data flow:
 * - useWorkouts() → tutti i piani (filtra client-side a quelli con id_cliente)
 * - useClients() → filtro per cliente
 * - Status derivato client-side da date (zero campo DB)
 */

import { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import { loadFilters, saveFilters, getUrlParams, syncUrlParams, resolveBackNavigation } from "@/lib/url-state";
import { usePageReveal } from "@/lib/page-reveal";
import Link from "next/link";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  ClipboardList,
  Repeat,
  Plus,
  User,
  AlertTriangle,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

import { useWorkouts } from "@/hooks/useWorkouts";
import { useClients } from "@/hooks/useClients";
import type { WorkoutPlan } from "@/types/api";
import {
  getProgramStatus,
  STATUS_LABELS,
  STATUS_COLORS,
  type ProgramStatus,
} from "@/lib/workout-monitoring";

// ════════════════════════════════════════════════════════════
// KPI CONFIG
// ════════════════════════════════════════════════════════════

interface MonitoringKpiDef {
  key: string;
  label: string;
  icon: LucideIcon;
  borderColor: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  valueColor: string;
}

const MONITORING_KPI: MonitoringKpiDef[] = [
  {
    key: "attivi",
    label: "Programmi Attivi",
    icon: Activity,
    borderColor: "border-l-emerald-500",
    gradient: "from-emerald-50/80 to-white dark:from-emerald-950/40 dark:to-zinc-900",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-400",
  },
  {
    key: "da_attivare",
    label: "Da Attivare",
    icon: AlertTriangle,
    borderColor: "border-l-amber-500",
    gradient: "from-amber-50/80 to-white dark:from-amber-950/40 dark:to-zinc-900",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
    iconColor: "text-amber-600 dark:text-amber-400",
    valueColor: "text-amber-700 dark:text-amber-400",
  },
];

// ════════════════════════════════════════════════════════════
// STATUS FILTER CHIPS
// ════════════════════════════════════════════════════════════

const STATUS_CHIP_COLORS: Record<"tutti" | ProgramStatus, string> = {
  tutti: "#71717a",
  attivo: "#10b981",
  da_attivare: "#f59e0b",
  completato: "#a1a1aa",
};

const STATUS_FILTER_LABELS: Record<"tutti" | ProgramStatus, string> = {
  tutti: "Tutti",
  attivo: "Attivi",
  da_attivare: "Da attivare",
  completato: "Completati",
};

// ════════════════════════════════════════════════════════════
// CARD STYLES PER STATUS
// ════════════════════════════════════════════════════════════

const STATUS_CARD_BORDER: Record<ProgramStatus, string> = {
  attivo: "border-l-emerald-500",
  da_attivare: "border-l-amber-500",
  completato: "border-l-zinc-400",
};

const STATUS_CARD_GRADIENT: Record<ProgramStatus, string> = {
  attivo: "from-emerald-50/30 to-white dark:from-emerald-950/20 dark:to-zinc-900",
  da_attivare: "from-amber-50/30 to-white dark:from-amber-950/20 dark:to-zinc-900",
  completato: "from-zinc-50/30 to-white dark:from-zinc-900/20 dark:to-zinc-900",
};

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function AllenamentiPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const router = useRouter();
  const initialClientId = getUrlParams().get("idCliente");
  const fromParam = getUrlParams().get("from");

  const backNav = useMemo(() => {
    if (!fromParam) return null;
    const nav = resolveBackNavigation(fromParam, { href: "", label: "" }, { tab: "schede" });
    return nav.href ? nav : null;
  }, [fromParam]);

  const { data: workoutsData, isLoading: loadingWorkouts } = useWorkouts();
  const { data: clientsData } = useClients();

  // Filter state (sessionStorage → URL → default)
  const [clientFilter, setClientFilter] = useState<string>(() => {
    if (initialClientId) return initialClientId;
    const saved = loadFilters("allenamenti");
    if (saved?.clientFilter) return saved.clientFilter as string;
    return "__all__";
  });
  const [statusFilter, setStatusFilter] = useState<"tutti" | ProgramStatus>(() => {
    const saved = loadFilters("allenamenti");
    if (saved?.statusFilter) return saved.statusFilter as "tutti" | ProgramStatus;
    const s = getUrlParams().get("status");
    if (s && ["attivo", "da_attivare", "completato"].includes(s)) return s as ProgramStatus;
    return "tutti";
  });

  // ── Sync filtri → sessionStorage + URL ──
  useEffect(() => {
    saveFilters("allenamenti", {
      clientFilter: clientFilter !== "__all__" ? clientFilter : null,
      statusFilter: statusFilter !== "tutti" ? statusFilter : null,
    });
    const params = new URLSearchParams();
    if (clientFilter !== "__all__") params.set("idCliente", clientFilter);
    if (statusFilter !== "tutti") params.set("status", statusFilter);
    syncUrlParams(window.location.pathname, params);
  }, [clientFilter, statusFilter]);

  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  // Solo piani con cliente assegnato
  const plansWithClient = useMemo(() => {
    const all = workoutsData?.items ?? [];
    return all.filter((p) => p.id_cliente !== null);
  }, [workoutsData]);

  // Conteggi per status
  const statusCounts = useMemo(() => {
    const counts = { attivo: 0, da_attivare: 0, completato: 0 };
    for (const p of plansWithClient) {
      const s = getProgramStatus(p);
      counts[s]++;
    }
    return counts;
  }, [plansWithClient]);

  const kpiValues: Record<string, number> = {
    attivi: statusCounts.attivo,
    da_attivare: statusCounts.da_attivare,
  };

  // Filtro client-side
  const filteredPlans = useMemo(() => {
    let result = plansWithClient;
    if (clientFilter !== "__all__") {
      const cid = Number(clientFilter);
      result = result.filter((p) => p.id_cliente === cid);
    }
    if (statusFilter !== "tutti") {
      result = result.filter((p) => getProgramStatus(p) === statusFilter);
    }
    return result;
  }, [plansWithClient, clientFilter, statusFilter]);

  // Conteggi per chip filtro
  const chipCounts = useMemo(() => {
    const base = clientFilter === "__all__"
      ? plansWithClient
      : plansWithClient.filter((p) => p.id_cliente === Number(clientFilter));
    const counts: Record<string, number> = { tutti: base.length };
    for (const p of base) {
      const s = getProgramStatus(p);
      counts[s] = (counts[s] ?? 0) + 1;
    }
    return counts;
  }, [plansWithClient, clientFilter]);

  if (loadingWorkouts) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
            <Activity className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Monitoraggio Allenamenti</h1>
            <p className="text-sm text-muted-foreground">Monitora aderenza e progresso dei programmi</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Back banner ── */}
      {backNav && (
        <Link href={backNav.href}>
          <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground">
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            {backNav.label}
          </Button>
        </Link>
      )}

      {/* ── Header ── */}
      <div data-guide="monitoraggio-header" className={revealClass(0, "flex items-center gap-3")} style={revealStyle(0)}>
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100 to-teal-200 dark:from-teal-900/40 dark:to-teal-800/30">
          <Activity aria-hidden="true" className="h-5 w-5 text-teal-600 dark:text-teal-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Monitoraggio Allenamenti</h1>
          <p className="text-sm text-muted-foreground">Monitora aderenza e progresso dei programmi</p>
        </div>
      </div>

      {/* ── KPI Hero Cards ── */}
      <div className={revealClass(50, "grid grid-cols-2 gap-4")} style={revealStyle(50)}>
        {MONITORING_KPI.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div
              key={kpi.key}
              className={`flex items-start gap-2 rounded-xl border border-l-4 ${kpi.borderColor} bg-gradient-to-br ${kpi.gradient} p-3 shadow-sm sm:gap-3 sm:p-4`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg sm:h-10 sm:w-10 ${kpi.iconBg}`}>
                <Icon aria-hidden="true" className={`h-4 w-4 sm:h-5 sm:w-5 ${kpi.iconColor}`} />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-semibold tracking-widest text-muted-foreground/70 uppercase">
                  {kpi.label}
                </p>
                <p className={`text-xl font-extrabold tracking-tighter tabular-nums sm:text-3xl ${kpi.valueColor}`}>
                  {kpiValues[kpi.key] ?? 0}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Filtri ── */}
      <div className={revealClass(100, "flex flex-wrap gap-3 items-center")} style={revealStyle(100)}>
        <Select value={clientFilter} onValueChange={setClientFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Tutti i clienti" />
          </SelectTrigger>
          <SelectContent position="popper" sideOffset={4}>
            <SelectItem value="__all__">Tutti i clienti</SelectItem>
            {clients
              .filter((c) => plansWithClient.some((p) => p.id_cliente === c.id))
              .map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nome} {c.cognome}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>

        <div className="flex gap-1.5">
          {(["tutti", "attivo", "da_attivare", "completato"] as const).map((key) => {
            const active = statusFilter === key;
            const color = STATUS_CHIP_COLORS[key];
            const count = chipCounts[key] ?? 0;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setStatusFilter(key)}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-[11px] font-medium transition-colors sm:px-3 sm:text-xs ${
                  active
                    ? "border-transparent shadow-sm"
                    : "border-dashed border-muted-foreground/30 opacity-50"
                }`}
                style={active ? { backgroundColor: color + "20", color } : undefined}
              >
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: color, opacity: active ? 1 : 0.3 }}
                />
                {STATUS_FILTER_LABELS[key]}
                <span className="tabular-nums opacity-70">({count})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Cards ── */}
      {filteredPlans.length === 0 ? (
        <div className={revealClass(150, "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-16")} style={revealStyle(150)}>
          <ClipboardList aria-hidden="true" className="h-10 w-10 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground">
            {plansWithClient.length === 0
              ? "Nessuna scheda assegnata a un cliente"
              : "Nessun programma corrisponde ai filtri"}
          </p>
          <Button variant="outline" size="sm" onClick={() => router.push("/schede")}>
            <Plus aria-hidden="true" className="mr-2 h-4 w-4" />
            Vai alle Schede
          </Button>
        </div>
      ) : (
        <div className={revealClass(150, "space-y-3")} style={revealStyle(150)}>
          {filteredPlans.map((plan) => (
            <ProgramCard key={plan.id} plan={plan} />
          ))}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// PROGRAM CARD (compact)
// ════════════════════════════════════════════════════════════

function ProgramCard({ plan }: { plan: WorkoutPlan }) {
  const status = getProgramStatus(plan);

  const clientName = plan.client_nome && plan.client_cognome
    ? `${plan.client_nome} ${plan.client_cognome}`
    : "—";

  const hasDateRange = plan.data_inizio && plan.data_fine;
  const dateLabel = hasDateRange
    ? `${format(new Date(plan.data_inizio + "T00:00:00"), "d MMM", { locale: it })} — ${format(new Date(plan.data_fine + "T00:00:00"), "d MMM yyyy", { locale: it })}`
    : null;

  return (
    <div className={`rounded-xl border border-l-4 ${STATUS_CARD_BORDER[status]} bg-gradient-to-br ${STATUS_CARD_GRADIENT[status]} p-3 transition-shadow hover:shadow-md sm:p-4`}>
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          {/* Riga 1: nome + badge */}
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-bold tracking-tight truncate">{plan.nome}</h3>
            <Badge className={`text-[10px] ${STATUS_COLORS[status]}`}>
              {STATUS_LABELS[status]}
            </Badge>
          </div>
          {/* Riga 2: cliente + obiettivo + livello */}
          <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
            <User aria-hidden="true" className="h-3 w-3 shrink-0" />
            <Link
              href={`/clienti/${plan.id_cliente}`}
              className="text-primary hover:underline font-medium truncate"
              onClick={(e) => e.stopPropagation()}
            >
              {clientName}
            </Link>
            <span className="text-muted-foreground/40 hidden sm:inline">·</span>
            <span className="hidden sm:inline capitalize">{plan.obiettivo}</span>
            <span className="text-muted-foreground/40 hidden sm:inline">·</span>
            <span className="hidden sm:inline capitalize">{plan.livello}</span>
          </div>
          {/* Riga 3: date + frequenza */}
          <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground/70">
            {dateLabel && (
              <span className="flex items-center gap-1 tabular-nums">
                <CalendarDays aria-hidden="true" className="h-3 w-3" />
                {dateLabel}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Repeat aria-hidden="true" className="h-3 w-3" />
              {plan.sessioni_per_settimana}x/sett · {plan.sessioni.length} {plan.sessioni.length === 1 ? "sessione" : "sessioni"}
            </span>
          </div>
        </div>

        <Link href={`/allenamenti/${plan.id}`}>
          <Button
            size="sm"
            variant={status === "da_attivare" ? "default" : "outline"}
            className="gap-1.5 text-xs shrink-0"
          >
            <CalendarDays aria-hidden="true" className="h-3.5 w-3.5" />
            {status === "da_attivare" ? "Pianifica" : "Calendario"}
            <ArrowRight aria-hidden="true" className="h-3 w-3" />
          </Button>
        </Link>
      </div>
    </div>
  );
}
