// training-intelligence/DoseResponseSection.tsx
"use client";

/**
 * Dose-Response per muscolo: barre volume effettivo vs target MEV/MAV/MRV.
 * Il cuore della differenziazione — nessun competitor mostra questo.
 */

import { BarChart3 } from "lucide-react";
import type { MuscleAnalysis } from "@/types/api";

interface DoseResponseSectionProps {
  muscles: MuscleAnalysis[];
}

const STATO_BAR_COLOR: Record<string, string> = {
  sotto_mev: "bg-blue-400",
  mev_mav: "bg-sky-400",
  ottimale: "bg-emerald-500",
  sopra_mav: "bg-amber-500",
  sopra_mrv: "bg-red-500",
};

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto", dorsali: "Dorsali", deltoide_anteriore: "Delt. Ant.",
  deltoide_laterale: "Delt. Lat.", deltoide_posteriore: "Delt. Post.",
  bicipiti: "Bicipiti", tricipiti: "Tricipiti", quadricipiti: "Quadricipiti",
  femorali: "Femorali", glutei: "Glutei", polpacci: "Polpacci",
  trapezio: "Trapezio", core: "Core", avambracci: "Avambracci", adduttori: "Adduttori",
};

export function DoseResponseSection({ muscles }: DoseResponseSectionProps) {
  // Filter only muscles with some volume or non-zero MEV
  const relevant = muscles.filter((m) => m.volume_effettivo > 0 || m.mev > 0);
  if (relevant.length === 0) return null;

  // Sort: problematic first (sotto_mev, sopra_mrv), then ottimale last
  const SORT_PRIORITY: Record<string, number> = {
    sopra_mrv: 0, sotto_mev: 1, sopra_mav: 2, mev_mav: 3, ottimale: 4,
  };
  const sorted = [...relevant].sort((a, b) =>
    (SORT_PRIORITY[a.stato] ?? 5) - (SORT_PRIORITY[b.stato] ?? 5),
  );

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-teal-600" />
        <div>
          <h3 className="text-sm font-bold">Dose-Response</h3>
          <p className="text-[11px] text-muted-foreground">Volume effettivo vs target scientifico (serie/settimana)</p>
        </div>
      </div>

      <div className="space-y-1.5">
        {sorted.map((m) => (
          <DoseBar key={m.muscolo} data={m} />
        ))}
      </div>

      {/* Fonte */}
      <p className="text-[9px] text-muted-foreground">
        Target MEV/MAV/MRV personalizzati per sesso, eta, obiettivo e livello (Israetel RP 2020, Schoenfeld 2017)
      </p>
    </section>
  );
}

function DoseBar({ data }: { data: MuscleAnalysis }) {
  const maxVal = Math.max(data.mrv, data.volume_effettivo, 1) * 1.15;
  const pctVol = (data.volume_effettivo / maxVal) * 100;
  const pctMev = (data.mev / maxVal) * 100;
  const pctMavMin = (data.mav_min / maxVal) * 100;
  const pctMavMax = (data.mav_max / maxVal) * 100;
  const pctMrv = (data.mrv / maxVal) * 100;

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-medium w-[72px] text-right shrink-0 truncate">
        {MUSCLE_LABELS[data.muscolo] ?? data.muscolo}
      </span>
      <div className="flex-1 relative h-4 bg-gray-50 rounded overflow-hidden border border-gray-100">
        {/* MAV zone (green zone) */}
        <div
          className="absolute h-full bg-emerald-100"
          style={{ left: `${pctMavMin}%`, width: `${Math.max(pctMavMax - pctMavMin, 0)}%` }}
        />
        {/* MEV marker */}
        <div className="absolute h-full w-0.5 bg-blue-300 z-10" style={{ left: `${pctMev}%` }} />
        {/* MRV marker */}
        <div className="absolute h-full w-0.5 bg-red-300 z-10" style={{ left: `${pctMrv}%` }} />
        {/* Actual bar */}
        <div
          className={`absolute h-full rounded-r transition-all ${STATO_BAR_COLOR[data.stato] ?? "bg-gray-400"}`}
          style={{ width: `${Math.min(pctVol, 100)}%`, opacity: 0.85 }}
        />
      </div>
      <span className="text-[10px] font-bold tabular-nums w-8 text-right shrink-0">
        {data.volume_effettivo}
      </span>
    </div>
  );
}
