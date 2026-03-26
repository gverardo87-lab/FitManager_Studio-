// src/components/agenda/FilterBar.tsx
"use client";

/**
 * Barra filtri a 2 assi per l'agenda: Categoria (riga 1) + Stato (riga 2).
 * Chip toggle con Eye/EyeOff, colori coerenti col color system.
 */

import { Eye, EyeOff } from "lucide-react";
import { CATEGORY_LEGEND, STATUS_LEGEND } from "./calendar-setup";

interface FilterBarProps {
  activeCategories: Set<string>;
  onToggleCategory: (cat: string) => void;
  activeStatuses: Set<string>;
  onToggleStatus: (stato: string) => void;
}

export function FilterBar({
  activeCategories,
  onToggleCategory,
  activeStatuses,
  onToggleStatus,
}: FilterBarProps) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border bg-gradient-to-br from-white to-zinc-50/50 px-3 py-2 shadow-sm sm:px-4 sm:py-2.5 dark:from-zinc-900 dark:to-zinc-800/50">
      {/* Riga 1: filtri categoria */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <span className="text-xs font-medium text-muted-foreground sm:w-16">Tipo:</span>
        {CATEGORY_LEGEND.map((cat) => {
          const active = activeCategories.has(cat.categoria);
          const Icon = active ? Eye : EyeOff;
          return (
            <button
              key={cat.categoria}
              type="button"
              onClick={() => onToggleCategory(cat.categoria)}
              aria-pressed={active}
              aria-label={`Filtra ${cat.label}: ${active ? "visibile" : "nascosto"}`}
              className={`flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-all duration-200 sm:gap-1.5 sm:px-3 sm:text-xs ${
                active
                  ? "border-transparent shadow-sm"
                  : "border-dashed border-muted-foreground/30 opacity-40"
              }`}
              style={
                active
                  ? { backgroundColor: cat.borderColor + "20", color: cat.borderColor }
                  : undefined
              }
            >
              <div
                className="h-2.5 w-2.5 rounded-full transition-opacity"
                style={{ backgroundColor: cat.borderColor, opacity: active ? 1 : 0.3 }}
              />
              {cat.label}
              <Icon className="h-3 w-3" aria-hidden="true" />
            </button>
          );
        })}
      </div>

      {/* Riga 2: filtri stato */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <span className="text-xs font-medium text-muted-foreground sm:w-16">Stato:</span>
        {STATUS_LEGEND.map((s) => {
          const active = activeStatuses.has(s.stato);
          const Icon = active ? Eye : EyeOff;
          return (
            <button
              key={s.stato}
              type="button"
              onClick={() => onToggleStatus(s.stato)}
              aria-pressed={active}
              aria-label={`Filtra ${s.label}: ${active ? "visibile" : "nascosto"}`}
              className={`flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-all duration-200 sm:gap-1.5 sm:px-3 sm:text-xs ${
                active
                  ? "border-transparent shadow-sm"
                  : "border-dashed border-muted-foreground/30 opacity-40"
              }`}
              style={
                active
                  ? { backgroundColor: s.backgroundColor, color: s.color }
                  : undefined
              }
            >
              <div
                className="h-2.5 w-2.5 rounded-full transition-opacity"
                style={{ backgroundColor: s.color, opacity: active ? 1 : 0.3 }}
              />
              {s.label}
              <Icon className="h-3 w-3" aria-hidden="true" />
            </button>
          );
        })}
      </div>
    </div>
  );
}
