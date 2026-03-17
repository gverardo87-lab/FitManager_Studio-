// src/lib/template-emphasis.ts
/**
 * Emphasis modifier per template scientifici.
 *
 * Aggiusta i parametri base di SLOT_VOLUME in base alla famiglia di template:
 * - standard: usa SLOT_VOLUME invariato (tonificazione, ipertrofia)
 * - heavy: +1 serie, -2 reps, +30s riposo sui compound_primary (massa, forza)
 * - light: -15s riposo sui compound (dimagrimento — densita metabolica)
 *
 * Ogni delta e' tracciabile a fonte scientifica primaria.
 *
 * Fonti:
 * - NSCA 2016 (Essentials of Strength Training, 4th ed) — rest periods per obiettivo
 * - Schoenfeld 2017 (Dose-response relationship) — volume/hypertrophy
 * - Helms 2019 (Muscle & Strength Pyramids) — strength periodization
 * - ACSM 2009 (Position Stand on Resistance Training) — general guidelines
 */

import type { SlotType } from "./smart-programming/types";

export type EmphasisType = "standard" | "heavy" | "light";

interface SlotVolume {
  serie: number;
  ripetizioni: string;
  riposo: number;
}

/**
 * Delta per emphasis "heavy" (massa/forza).
 * Compound primary: +1 serie, -2 reps range basso, +30s riposo.
 * Fonte: NSCA 2016 Table 15.5 — forza/potenza: 3-5 min rest, 1-5RM.
 * Helms 2019: progressione in forza richiede serie pesanti con recupero completo.
 */
const HEAVY_DELTA: Partial<Record<SlotType, { serie: number; repShift: number; riposo: number }>> = {
  compound_primary: { serie: 1, repShift: -2, riposo: 30 },
};

/**
 * Delta per emphasis "light" (dimagrimento).
 * Compound primary/secondary: -15s riposo per maggiore densita metabolica.
 * Fonte: NSCA 2016 Table 15.5 — endurance/circuit: 30-60s rest.
 * ACSM 2009: periodi di riposo ridotti aumentano EPOC.
 */
const LIGHT_DELTA: Partial<Record<SlotType, { serie: number; repShift: number; riposo: number }>> = {
  compound_primary:   { serie: 0, repShift: 0, riposo: -15 },
  compound_secondary: { serie: 0, repShift: 0, riposo: -15 },
};

/** Shifta il range di ripetizioni (es. "6-8" con shift -2 diventa "4-6"). */
function shiftRepRange(range: string, shift: number): string {
  const match = range.match(/^(\d+)-(\d+)$/);
  if (!match) return range;
  const lo = Math.max(1, Number(match[1]) + shift);
  const hi = Math.max(lo, Number(match[2]) + shift);
  return `${lo}-${hi}`;
}

/**
 * Applica il modificatore emphasis ai parametri volume di uno slot.
 *
 * - standard: nessuna modifica
 * - heavy: compound_primary piu pesante (NSCA 2016, Helms 2019)
 * - light: compound piu denso metabolicamente (NSCA 2016, ACSM 2009)
 */
export function applyEmphasis(
  volume: SlotVolume,
  slotType: SlotType,
  emphasis: EmphasisType,
): SlotVolume {
  if (emphasis === "standard") return volume;

  const deltas = emphasis === "heavy" ? HEAVY_DELTA : LIGHT_DELTA;
  const delta = deltas[slotType];
  if (!delta) return volume;

  return {
    serie: volume.serie + delta.serie,
    ripetizioni: delta.repShift !== 0 ? shiftRepRange(volume.ripetizioni, delta.repShift) : volume.ripetizioni,
    riposo: Math.max(30, volume.riposo + delta.riposo),
  };
}
