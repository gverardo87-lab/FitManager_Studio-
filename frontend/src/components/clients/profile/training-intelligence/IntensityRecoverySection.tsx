// training-intelligence/IntensityRecoverySection.tsx
"use client";

/**
 * Distribuzione Intensita (donut) + Recovery Warnings.
 */

import { Gauge, ShieldAlert } from "lucide-react";
import type { IntensityDistribution, RecoveryWarning } from "@/types/api";

interface IntensityRecoverySectionProps {
  intensity: IntensityDistribution;
  recoveryWarnings: RecoveryWarning[];
}

const ZONE_CONFIG = [
  { key: "massimale" as const, label: "Massimale", color: "bg-red-500", textColor: "text-red-700", desc: ">90% 1RM" },
  { key: "sub_massimale" as const, label: "Sub-Massimale", color: "bg-orange-500", textColor: "text-orange-700", desc: "80-90% 1RM" },
  { key: "ipertrofia" as const, label: "Ipertrofia", color: "bg-emerald-500", textColor: "text-emerald-700", desc: "67-80% 1RM" },
  { key: "resistenza" as const, label: "Resistenza", color: "bg-blue-500", textColor: "text-blue-700", desc: "50-67% 1RM" },
  { key: "attivazione" as const, label: "Attivazione", color: "bg-gray-400", textColor: "text-gray-600", desc: "<50% 1RM" },
] as const;

export function IntensityRecoverySection({ intensity, recoveryWarnings }: IntensityRecoverySectionProps) {
  const hasIntensity = Object.values(intensity).some((v) => v > 0);

  return (
    <section className="space-y-4">
      {/* Intensity */}
      {hasIntensity ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-teal-600" />
            <div>
              <h3 className="text-sm font-bold">Distribuzione Intensita</h3>
              <p className="text-[11px] text-muted-foreground">Zone NSCA (% 1RM stimata via Epley)</p>
            </div>
          </div>

          {/* Stacked bar */}
          <div className="h-6 flex rounded-full overflow-hidden">
            {ZONE_CONFIG.map((z) => {
              const pct = intensity[z.key];
              if (pct <= 0) return null;
              return (
                <div
                  key={z.key}
                  className={`${z.color} transition-all relative group`}
                  style={{ width: `${pct}%` }}
                  title={`${z.label}: ${pct}%`}
                >
                  {pct >= 10 ? (
                    <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-white">
                      {Math.round(pct)}%
                    </span>
                  ) : null}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {ZONE_CONFIG.map((z) => {
              const pct = intensity[z.key];
              if (pct <= 0) return null;
              return (
                <div key={z.key} className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${z.color}`} />
                  <span className={`text-[10px] font-medium ${z.textColor}`}>
                    {z.label} {Math.round(pct)}%
                  </span>
                  <span className="text-[9px] text-muted-foreground">({z.desc})</span>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* Recovery Warnings */}
      {recoveryWarnings.length > 0 ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-amber-600" />
            <h3 className="text-sm font-bold">Recovery Overlap</h3>
          </div>

          {recoveryWarnings.map((rw, i) => (
            <div
              key={i}
              className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-2.5"
            >
              <ShieldAlert className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-medium">
                  {rw.sessione_a} → {rw.sessione_b}
                </p>
                <p className="text-[10px] text-amber-700">
                  Muscoli in overlap: {rw.muscoli_overlap.join(", ")}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
