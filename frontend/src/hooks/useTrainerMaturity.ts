// src/hooks/useTrainerMaturity.ts
/**
 * Mastery Progression System — Core Hook
 *
 * Deriva il livello di maturita' del trainer (1-5) dai dati gia' in cache
 * React Query. Zero API aggiuntive. Zero localStorage.
 *
 * Il livello NON viene mai mostrato esplicitamente all'utente.
 * Guida banner contestuali, tour unlock e PageGuide adattivo.
 */

import { useMemo } from "react";
import { useDashboard, useDashboardAlerts, useClinicalReadiness } from "./useDashboard";

// ── Types ──

export type MaturityLevel = 1 | 2 | 3 | 4 | 5;

export type MaturityName =
  | "explorer"
  | "operative"
  | "structured"
  | "professional"
  | "expert";

export interface MaturitySignals {
  clientCount: number;
  avgReadiness: number;
  ghostEventCount: number;
  overdueRateCount: number;
  hasRevenue: boolean;
  workoutCount: number;
  readyClientCount: number;
}

export interface TrainerMaturity {
  level: MaturityLevel;
  levelName: MaturityName;
  signals: MaturitySignals;
  /** Suggerimento prossimo traguardo (italiano). null a livello 5. */
  nextGoal: string | null;
  isLoading: boolean;
}

// ── Level names ──

const LEVEL_NAMES: Record<MaturityLevel, MaturityName> = {
  1: "explorer",
  2: "operative",
  3: "structured",
  4: "professional",
  5: "expert",
};

// ── Next goal messages (italiano, professionale, mai gamificato) ──

const NEXT_GOALS: Record<MaturityLevel, string | null> = {
  1: "Registra il tuo primo cliente per iniziare",
  2: "Compila l'anamnesi dei tuoi clienti e crea la prima scheda",
  3: "Raggiungi 5 clienti con profilo completo e registra il primo pagamento",
  4: "Porta il readiness medio sopra l'85% e azzera le rate scadute",
  5: null,
};

// ── Hook ──

export function useTrainerMaturity(): TrainerMaturity {
  const { data: summary, isLoading: loadingSummary } = useDashboard();
  const { data: alerts, isLoading: loadingAlerts } = useDashboardAlerts();
  const { data: readiness, isLoading: loadingReadiness } = useClinicalReadiness();

  const isLoading = loadingSummary || loadingAlerts || loadingReadiness;

  return useMemo(() => {
    // Signals from existing cache
    const clientCount = summary?.active_clients ?? 0;
    const hasRevenue = (summary?.monthly_revenue ?? 0) > 0;

    const ghostEventCount =
      alerts?.items.find((a) => a.category === "ghost_events")?.count ?? 0;
    const overdueRateCount =
      alerts?.items.find((a) => a.category === "overdue_rates")?.count ?? 0;

    const items = readiness?.items ?? [];
    const avgReadiness =
      items.length > 0
        ? items.reduce((sum, i) => sum + i.readiness_score, 0) / items.length
        : 0;
    const workoutCount = items.filter((i) => i.has_workout_plan).length;
    const readyClientCount = readiness?.summary?.ready_clients ?? 0;

    const signals: MaturitySignals = {
      clientCount,
      avgReadiness,
      ghostEventCount,
      overdueRateCount,
      hasRevenue,
      workoutCount,
      readyClientCount,
    };

    // Derive level (check top-down, first match wins)
    let level: MaturityLevel = 1;

    if (
      clientCount >= 8 &&
      avgReadiness >= 85 &&
      overdueRateCount === 0
    ) {
      level = 5;
    } else if (
      clientCount >= 5 &&
      avgReadiness >= 70 &&
      ghostEventCount === 0 &&
      hasRevenue
    ) {
      level = 4;
    } else if (
      clientCount >= 3 &&
      avgReadiness >= 40 &&
      workoutCount >= 1
    ) {
      level = 3;
    } else if (clientCount >= 1) {
      level = 2;
    }

    return {
      level,
      levelName: LEVEL_NAMES[level],
      signals,
      nextGoal: NEXT_GOALS[level],
      isLoading,
    };
  }, [summary, alerts, readiness, isLoading]);
}
