// src/components/movements/AndamentoTab.tsx
"use client";

/**
 * Andamento Tab — vista temporale della finanza (Layer 1).
 *
 * Incassato per periodo (cassa), ultimi N mesi:
 * - 3 KPI: Cash flow reale, Incassi da contratti, Altri incassi (TASSONOMIA §1 Asse 1)
 * - Stacked bar: incassi_contratti + altri_incassi = cash flow reale, per mese
 *
 * Dati: GET /api/movements/financial-trend via useFinancialTrend().
 * Storni (STORNO_SPESA_FISSA) esclusi a monte dal backend.
 * (Layer 2 aggiungerà la serie "venduto"/competenza; Layer 3 la composizione.)
 */

import { useState } from "react";
import { Wallet, FileText, Coins, Tag, LineChart as LineChartIcon, PieChart } from "lucide-react";
import { Bar, BarChart, Line, ComposedChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { GradientKpiCard } from "@/components/movements/GradientKpiCard";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { useFinancialTrend } from "@/hooks/useMovements";
import { formatCurrency } from "@/lib/format";

const TREND_MONTHS = 12;

const trendConfig: ChartConfig = {
  incassi_contratti: { label: "Incassi da contratti", color: "var(--color-teal-500)" },
  altri_incassi: { label: "Altri incassi", color: "var(--color-amber-400)" },
  venduto: { label: "Venduto (competenza)", color: "var(--color-violet-500)" },
  // Composizione (Layer 3)
  incassi_nuovi: { label: "Nuovi", color: "var(--color-emerald-500)" },
  incassi_rinnovi: { label: "Rinnovi", color: "var(--color-blue-500)" },
  incassi_acconti: { label: "Acconti", color: "var(--color-teal-500)" },
  incassi_rate: { label: "Rate", color: "var(--color-amber-400)" },
};

type CompMode = "origine" | "tipo";  // origine = nuovi/rinnovi, tipo = acconti/rate

function KpiValue({ amount, color }: { amount: number; color: string }) {
  return <p className={`text-2xl font-bold tracking-tight tabular-nums ${color}`}>{formatCurrency(amount)}</p>;
}

export function AndamentoTab() {
  const { data, isLoading } = useFinancialTrend(TREND_MONTHS);
  const [compMode, setCompMode] = useState<CompMode>("origine");

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-[320px] rounded-xl" />
      </div>
    );
  }

  const periodi = data?.periodi ?? [];
  const hasData = (data?.tot_cash_flow_reale ?? 0) > 0 || (data?.tot_venduto ?? 0) > 0;

  return (
    <div className="space-y-6">
      {/* KPI — finestra ultimi N mesi */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <GradientKpiCard
          icon={<Wallet className="h-5 w-5 text-teal-600 dark:text-teal-400" />}
          iconBg="bg-teal-100 dark:bg-teal-900/30"
          label="Cash flow reale"
          value={<KpiValue amount={data?.tot_cash_flow_reale ?? 0} color="text-teal-700 dark:text-teal-400" />}
          sub={`ultimi ${TREND_MONTHS} mesi`}
          borderColor="border-l-teal-500"
          gradient="from-teal-50/80 to-white dark:from-teal-950/40 dark:to-zinc-900"
        />
        <GradientKpiCard
          icon={<FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
          iconBg="bg-blue-100 dark:bg-blue-900/30"
          label="Incassi da contratti"
          value={<KpiValue amount={data?.tot_incassi_contratti ?? 0} color="text-blue-700 dark:text-blue-400" />}
          sub="acconti + rate"
          borderColor="border-l-blue-500"
          gradient="from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900"
        />
        <GradientKpiCard
          icon={<Coins className="h-5 w-5 text-amber-600 dark:text-amber-400" />}
          iconBg="bg-amber-100 dark:bg-amber-900/30"
          label="Altri incassi"
          value={<KpiValue amount={data?.tot_altri_incassi ?? 0} color="text-amber-700 dark:text-amber-400" />}
          sub="fuori contratto"
          borderColor="border-l-amber-400"
          gradient="from-amber-50/80 to-white dark:from-amber-950/40 dark:to-zinc-900"
        />
        <GradientKpiCard
          icon={<Tag className="h-5 w-5 text-violet-600 dark:text-violet-400" />}
          iconBg="bg-violet-100 dark:bg-violet-900/30"
          label="Venduto"
          value={<KpiValue amount={data?.tot_venduto ?? 0} color="text-violet-700 dark:text-violet-400" />}
          sub="per competenza"
          borderColor="border-l-violet-500"
          gradient="from-violet-50/80 to-white dark:from-violet-950/40 dark:to-zinc-900"
        />
      </div>

      {/* Grafico andamento */}
      {hasData ? (
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="mb-1 flex items-center gap-2">
            <LineChartIcon className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Incassato vs Venduto · ultimi {TREND_MONTHS} mesi</h3>
          </div>
          <p className="mb-3 text-[11px] text-muted-foreground">
            Barre = incassato (cassa); linea = venduto (competenza). Lo scarto è il venduto non ancora incassato.
          </p>
          <ChartContainer config={trendConfig} className="h-[280px] w-full">
            <ComposedChart data={periodi} margin={{ left: 4, right: 4, top: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} interval="preserveStartEnd" />
              <YAxis
                tickLine={false}
                axisLine={false}
                width={64}
                fontSize={11}
                tickFormatter={(v) => formatCurrency(Number(v))}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="incassi_contratti" stackId="cf" fill="var(--color-incassi_contratti)" radius={[0, 0, 4, 4]} />
              <Bar dataKey="altri_incassi" stackId="cf" fill="var(--color-altri_incassi)" radius={[4, 4, 0, 0]} />
              <Line
                dataKey="venduto"
                type="monotone"
                stroke="var(--color-venduto)"
                strokeWidth={2}
                dot={{ r: 2.5 }}
                activeDot={{ r: 4 }}
              />
            </ComposedChart>
          </ChartContainer>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed py-16 text-center">
          <LineChartIcon className="h-8 w-8 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">Nessun dato negli ultimi {TREND_MONTHS} mesi</p>
          <p className="text-xs text-muted-foreground/70">Incassi e contratti venduti compaiono qui appena registrati</p>
        </div>
      )}

      {/* Composizione incassi da contratti (Layer 3) — due tagli, toggle */}
      {(data?.tot_incassi_contratti ?? 0) > 0 && (
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <PieChart className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold">Composizione incassi da contratti</h3>
            </div>
            <div className="flex gap-1 rounded-lg border bg-muted/40 p-0.5">
              <Button
                size="sm"
                variant={compMode === "origine" ? "default" : "ghost"}
                className="h-7 px-2.5 text-xs"
                onClick={() => setCompMode("origine")}
              >
                Nuovi / Rinnovi
              </Button>
              <Button
                size="sm"
                variant={compMode === "tipo" ? "default" : "ghost"}
                className="h-7 px-2.5 text-xs"
                onClick={() => setCompMode("tipo")}
              >
                Acconti / Rate
              </Button>
            </div>
          </div>
          <p className="mb-3 text-[11px] text-muted-foreground">
            {compMode === "origine"
              ? "Cresco acquisendo (nuovi) o fidelizzando (rinnovi)?"
              : "Denaro fresco (acconti) o code di contratti pregressi (rate)?"}
          </p>
          <ChartContainer config={trendConfig} className="h-[240px] w-full">
            <BarChart data={periodi} margin={{ left: 4, right: 4, top: 8 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} interval="preserveStartEnd" />
              <YAxis tickLine={false} axisLine={false} width={64} fontSize={11} tickFormatter={(v) => formatCurrency(Number(v))} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              {/* No React Fragment qui: recharts non rileva le Bar dentro un <>…</>.
                  Le serie condizionali vanno passate come array (recharts appiattisce). */}
              {(compMode === "origine"
                ? ["incassi_nuovi", "incassi_rinnovi"]
                : ["incassi_acconti", "incassi_rate"]
              ).map((key, i) => (
                <Bar
                  key={key}
                  dataKey={key}
                  stackId="comp"
                  fill={`var(--color-${key})`}
                  radius={i === 0 ? [0, 0, 4, 4] : [4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ChartContainer>
        </div>
      )}
    </div>
  );
}
