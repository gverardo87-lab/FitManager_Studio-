// training-intelligence/MuscleHeatmap.tsx
"use client";

/**
 * Mappa muscolare con heatmap colore basata su stato volume MEV/MAV/MRV.
 * Vista anteriore + posteriore del corpo, click per drill-down.
 */

import { useState } from "react";
import { Activity } from "lucide-react";
import type { MuscleAnalysis } from "@/types/api";

interface MuscleHeatmapProps {
  muscles: MuscleAnalysis[];
}

// Colori per stato volume
const STATO_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  sotto_mev: { bg: "bg-blue-100 border-blue-300", text: "text-blue-800", label: "Sotto MEV" },
  mev_mav: { bg: "bg-sky-100 border-sky-300", text: "text-sky-800", label: "MEV-MAV" },
  ottimale: { bg: "bg-emerald-100 border-emerald-400", text: "text-emerald-800", label: "Ottimale" },
  sopra_mav: { bg: "bg-amber-100 border-amber-400", text: "text-amber-800", label: "Sopra MAV" },
  sopra_mrv: { bg: "bg-red-100 border-red-400", text: "text-red-800", label: "Sopra MRV" },
};

const STATO_DOT: Record<string, string> = {
  sotto_mev: "bg-blue-400",
  mev_mav: "bg-sky-400",
  ottimale: "bg-emerald-500",
  sopra_mav: "bg-amber-500",
  sopra_mrv: "bg-red-500",
};

// Nomi italiani per i muscoli
const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto",
  dorsali: "Dorsali",
  deltoide_anteriore: "Delt. Ant.",
  deltoide_laterale: "Delt. Lat.",
  deltoide_posteriore: "Delt. Post.",
  bicipiti: "Bicipiti",
  tricipiti: "Tricipiti",
  quadricipiti: "Quadricipiti",
  femorali: "Femorali",
  glutei: "Glutei",
  polpacci: "Polpacci",
  trapezio: "Trapezio",
  core: "Core",
  avambracci: "Avambracci",
  adduttori: "Adduttori",
};

// Muscoli anteriori e posteriori
const ANTERIOR = ["petto", "deltoide_anteriore", "deltoide_laterale", "bicipiti", "quadricipiti", "core", "adduttori", "avambracci"];
const POSTERIOR = ["dorsali", "deltoide_posteriore", "tricipiti", "trapezio", "femorali", "glutei", "polpacci"];

export function MuscleHeatmap({ muscles }: MuscleHeatmapProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const muscleMap = new Map(muscles.map((m) => [m.muscolo, m]));

  const selectedData = selected ? muscleMap.get(selected) : null;

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <Activity className="h-4 w-4 text-teal-600" />
        <div>
          <h3 className="text-sm font-bold">Mappa Muscolare</h3>
          <p className="text-[11px] text-muted-foreground">Volume effettivo vs target scientifico per muscolo</p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(STATO_COLORS).map(([key, val]) => (
          <span key={key} className="flex items-center gap-1 text-[10px]">
            <span className={`w-2 h-2 rounded-full ${STATO_DOT[key]}`} />
            {val.label}
          </span>
        ))}
      </div>

      {/* Muscle grid: Anteriore + Posteriore */}
      <div className="grid grid-cols-2 gap-3">
        <MuscleColumn title="Anteriore" muscleKeys={ANTERIOR} muscleMap={muscleMap} selected={selected} onSelect={setSelected} />
        <MuscleColumn title="Posteriore" muscleKeys={POSTERIOR} muscleMap={muscleMap} selected={selected} onSelect={setSelected} />
      </div>

      {/* Drill-down */}
      {selectedData ? (
        <div className={`rounded-lg border p-3 ${STATO_COLORS[selectedData.stato]?.bg ?? "bg-muted"}`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-sm font-bold ${STATO_COLORS[selectedData.stato]?.text ?? ""}`}>
              {MUSCLE_LABELS[selectedData.muscolo] ?? selectedData.muscolo}
            </span>
            <span className="text-[10px] font-semibold uppercase">{STATO_COLORS[selectedData.stato]?.label}</span>
          </div>
          <VolumeMiniBar data={selectedData} />
          <div className="grid grid-cols-4 gap-2 mt-2">
            <MiniStat label="MEV" value={selectedData.mev} />
            <MiniStat label="MAV min" value={selectedData.mav_min} />
            <MiniStat label="MAV max" value={selectedData.mav_max} />
            <MiniStat label="MRV" value={selectedData.mrv} />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <TrendBadge trend={selectedData.trend} />
            <span className="text-xs text-muted-foreground">
              {selectedData.volume_effettivo} serie/sett effettive
            </span>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function MuscleColumn({
  title, muscleKeys, muscleMap, selected, onSelect,
}: {
  title: string;
  muscleKeys: string[];
  muscleMap: Map<string, MuscleAnalysis>;
  selected: string | null;
  onSelect: (m: string | null) => void;
}) {
  return (
    <div>
      <p className="text-[10px] font-semibold text-muted-foreground uppercase mb-1">{title}</p>
      <div className="space-y-1">
        {muscleKeys.map((key) => {
          const data = muscleMap.get(key);
          if (!data || data.volume_effettivo <= 0) return null;
          const isSelected = selected === key;
          return (
            <button
              key={key}
              className={`w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors text-xs ${
                isSelected ? "ring-2 ring-teal-400 bg-white shadow-sm" : "hover:bg-muted/60"
              }`}
              onClick={() => onSelect(isSelected ? null : key)}
            >
              <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${STATO_DOT[data.stato] ?? "bg-gray-300"}`} />
              <span className="flex-1 font-medium truncate">{MUSCLE_LABELS[key] ?? key}</span>
              <span className="tabular-nums text-muted-foreground">{data.volume_effettivo}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function VolumeMiniBar({ data }: { data: MuscleAnalysis }) {
  const max = Math.max(data.mrv, data.volume_effettivo) * 1.1;
  const pctVol = max > 0 ? (data.volume_effettivo / max) * 100 : 0;
  const pctMev = max > 0 ? (data.mev / max) * 100 : 0;
  const pctMavMin = max > 0 ? (data.mav_min / max) * 100 : 0;
  const pctMavMax = max > 0 ? (data.mav_max / max) * 100 : 0;
  const pctMrv = max > 0 ? (data.mrv / max) * 100 : 0;

  return (
    <div className="relative h-5 bg-gray-100 rounded-full overflow-hidden">
      {/* Target zones */}
      <div className="absolute h-full bg-emerald-200/50" style={{ left: `${pctMavMin}%`, width: `${pctMavMax - pctMavMin}%` }} />
      {/* MEV line */}
      <div className="absolute h-full w-px bg-blue-400" style={{ left: `${pctMev}%` }} />
      {/* MRV line */}
      <div className="absolute h-full w-px bg-red-400" style={{ left: `${pctMrv}%` }} />
      {/* Actual volume */}
      <div
        className={`absolute h-full rounded-full transition-all ${STATO_DOT[data.stato]}`}
        style={{ width: `${Math.min(pctVol, 100)}%`, opacity: 0.8 }}
      />
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="text-xs font-bold tabular-nums">{value}</p>
    </div>
  );
}

function TrendBadge({ trend }: { trend: string }) {
  const config: Record<string, { icon: string; cls: string }> = {
    crescente: { icon: "↑", cls: "text-emerald-700 bg-emerald-50" },
    stabile: { icon: "→", cls: "text-zinc-600 bg-zinc-50" },
    calante: { icon: "↓", cls: "text-red-700 bg-red-50" },
  };
  const c = config[trend] ?? config.stabile;
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${c.cls}`}>
      {c.icon} {trend}
    </span>
  );
}
