// training-intelligence/AlertsSection.tsx
"use client";

/**
 * Alert predittivi — avvisi intelligenti basati sull'analisi scientifica.
 */

import { AlertTriangle, ShieldAlert, Scale, Activity } from "lucide-react";
import type { TrainingAlert } from "@/types/api";

interface AlertsSectionProps {
  alerts: TrainingAlert[];
}

const ALERT_CONFIG: Record<string, {
  icon: React.ComponentType<{ className?: string }>;
  bgClass: string;
  borderClass: string;
  iconClass: string;
}> = {
  sotto_mev: { icon: AlertTriangle, bgClass: "bg-blue-50", borderClass: "border-blue-200", iconClass: "text-blue-600" },
  sopra_mrv: { icon: ShieldAlert, bgClass: "bg-red-50", borderClass: "border-red-300", iconClass: "text-red-600" },
  squilibrio: { icon: Scale, bgClass: "bg-amber-50", borderClass: "border-amber-200", iconClass: "text-amber-600" },
  recovery: { icon: Activity, bgClass: "bg-orange-50", borderClass: "border-orange-200", iconClass: "text-orange-600" },
};

export function AlertsSection({ alerts }: AlertsSectionProps) {
  if (alerts.length === 0) return null;

  // Sort: danger first, then warning, then info
  const SEVERITY_ORDER: Record<string, number> = { danger: 0, warning: 1, info: 2 };
  const sorted = [...alerts].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3),
  );

  return (
    <section className="space-y-2">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-600" />
        <h3 className="text-sm font-bold">Insight & Alert</h3>
        <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-1.5 py-0.5 rounded-full">
          {alerts.length}
        </span>
      </div>

      <div className="space-y-1.5">
        {sorted.map((alert, i) => {
          const cfg = ALERT_CONFIG[alert.tipo] ?? ALERT_CONFIG.squilibrio;
          const Icon = cfg.icon;
          return (
            <div
              key={i}
              className={`flex items-start gap-2 rounded-lg border p-2.5 ${cfg.bgClass} ${cfg.borderClass}`}
            >
              <Icon className={`h-3.5 w-3.5 shrink-0 mt-0.5 ${cfg.iconClass}`} />
              <p className="text-xs leading-relaxed">{alert.messaggio}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
