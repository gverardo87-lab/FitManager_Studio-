// src/components/agenda/RangeStatsBar.tsx
"use client";

/**
 * KPI contestuali al range visibile dell'agenda.
 * 4 metriche config-driven: Sessioni, Completate, Programmate, Completamento %.
 */

import { CalendarDays, CheckCircle2, Clock, Target } from "lucide-react";

export interface RangeStatsData {
  total: number;
  completed: number;
  scheduled: number;
  rate: number;
}

const RANGE_KPI = [
  {
    key: "total" as const,
    label: "Sessioni",
    icon: CalendarDays,
    borderColor: "border-l-blue-500",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
    iconColor: "text-blue-600 dark:text-blue-400",
    valueColor: "text-blue-700 dark:text-blue-300",
  },
  {
    key: "completed" as const,
    label: "Completate",
    icon: CheckCircle2,
    borderColor: "border-l-emerald-500",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    valueColor: "text-emerald-700 dark:text-emerald-300",
  },
  {
    key: "scheduled" as const,
    label: "Programmate",
    icon: Clock,
    borderColor: "border-l-amber-500",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
    iconColor: "text-amber-600 dark:text-amber-400",
    valueColor: "text-amber-700 dark:text-amber-300",
  },
  {
    key: "rate" as const,
    label: "Completamento",
    icon: Target,
    borderColor: "border-l-violet-500",
    iconBg: "bg-violet-100 dark:bg-violet-900/30",
    iconColor: "text-violet-600 dark:text-violet-400",
    valueColor: "text-violet-700 dark:text-violet-300",
    suffix: "%",
  },
];

export function RangeStatsBar({ stats, label }: { stats: RangeStatsData; label: string }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {RANGE_KPI.map((kpi) => {
        const Icon = kpi.icon;
        const value = stats[kpi.key];
        return (
          <div
            key={kpi.key}
            className={`flex items-center gap-3 rounded-lg border border-l-4 ${kpi.borderColor} bg-white p-3 shadow-sm transition-shadow hover:shadow-md dark:bg-zinc-900`}
          >
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${kpi.iconBg}`}>
              <Icon className={`h-4 w-4 ${kpi.iconColor}`} aria-hidden="true" />
            </div>
            <div>
              <p className={`text-xl font-bold tabular-nums ${kpi.valueColor}`}>
                {value}{"suffix" in kpi ? kpi.suffix : ""}
              </p>
              <p className="text-[10px] font-medium capitalize text-muted-foreground">
                {kpi.label} · {label}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
