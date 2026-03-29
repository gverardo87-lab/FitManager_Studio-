// training-intelligence/BalanceSection.tsx
"use client";

/**
 * Equilibrio Biomeccanico — 5 rapporti con stato, target e trend.
 */

import { Scale } from "lucide-react";
import type { BalanceRatioAnalysis } from "@/types/api";

interface BalanceSectionProps {
  ratios: BalanceRatioAnalysis[];
}

export function BalanceSection({ ratios }: BalanceSectionProps) {
  if (ratios.length === 0) return null;

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <Scale className="h-4 w-4 text-teal-600" />
        <div>
          <h3 className="text-sm font-bold">Equilibrio Biomeccanico</h3>
          <p className="text-[11px] text-muted-foreground">Rapporti tra catene muscolari (NSCA 2016, Sahrmann 2002)</p>
        </div>
      </div>

      <div className="space-y-2">
        {ratios.map((r) => (
          <RatioCard key={r.nome} ratio={r} />
        ))}
      </div>
    </section>
  );
}

function RatioCard({ ratio }: { ratio: BalanceRatioAnalysis }) {
  const ok = ratio.in_tolleranza;
  const borderColor = ok ? "border-emerald-200" : "border-amber-300";
  const bgColor = ok ? "bg-emerald-50/50" : "bg-amber-50/50";

  // Compute position of current value on the scale
  const scaleMin = Math.min(ratio.target - ratio.tolleranza * 2, ratio.valore_corrente * 0.8);
  const scaleMax = Math.max(ratio.target + ratio.tolleranza * 2, ratio.valore_corrente * 1.2);
  const range = scaleMax - scaleMin;
  const pctTarget = range > 0 ? ((ratio.target - scaleMin) / range) * 100 : 50;
  const pctCurrent = range > 0 ? ((ratio.valore_corrente - scaleMin) / range) * 100 : 50;
  const pctTolMin = range > 0 ? ((ratio.target - ratio.tolleranza - scaleMin) / range) * 100 : 30;
  const pctTolMax = range > 0 ? ((ratio.target + ratio.tolleranza - scaleMin) / range) * 100 : 70;

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} p-2.5`}>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold">{ratio.nome}</span>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold tabular-nums ${ok ? "text-emerald-700" : "text-amber-700"}`}>
            {ratio.valore_corrente.toFixed(2)}
          </span>
          <span className="text-[10px] text-muted-foreground">
            target {ratio.target.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Visual scale */}
      <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
        {/* Tolerance zone */}
        <div
          className="absolute h-full bg-emerald-200/60"
          style={{
            left: `${Math.max(pctTolMin, 0)}%`,
            width: `${Math.min(pctTolMax - Math.max(pctTolMin, 0), 100)}%`,
          }}
        />
        {/* Target line */}
        <div
          className="absolute h-full w-0.5 bg-emerald-600 z-10"
          style={{ left: `${Math.min(Math.max(pctTarget, 0), 100)}%` }}
        />
        {/* Current value dot */}
        <div
          className={`absolute top-0.5 w-2 h-2 rounded-full z-20 ${ok ? "bg-emerald-600" : "bg-amber-600"}`}
          style={{ left: `calc(${Math.min(Math.max(pctCurrent, 0), 100)}% - 4px)` }}
        />
      </div>

      {ok ? (
        <p className="text-[10px] text-emerald-600 mt-1">In equilibrio</p>
      ) : (
        <p className="text-[10px] text-amber-600 mt-1">
          {ratio.valore_corrente > ratio.target ? "Sbilanciato verso il numeratore" : "Sbilanciato verso il denominatore"}
        </p>
      )}
    </div>
  );
}
