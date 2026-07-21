// src/hooks/useClientReadiness.ts
/**
 * Hook per readiness clinica di un singolo cliente.
 *
 * Wrappa useClinicalReadiness() (cache condivisa, refetch 60s) ed estrae
 * il record del cliente via .find(). Zero API call aggiuntive.
 *
 * Esporta anche computeOnboardingSteps() per calcolare la checklist
 * di onboarding basata su dati reali.
 */

import { useMemo } from "react";
import {
  HeartPulse,
  Ruler,
  Dumbbell,
  Calendar,
  FileText,
  type LucideIcon,
} from "lucide-react";
import { useClinicalReadiness } from "./useDashboard";
import type { ClinicalReadinessClientItem } from "@/types/api";

export interface OnboardingStep {
  key: string;
  label: string;
  description: string;
  completed: boolean;
  href: string;
  icon: LucideIcon;
  /** Se presente, il click esegue questa azione invece di navigare a href. */
  onAction?: () => void;
}

interface OnboardingContext {
  hasContracts: boolean;
  /** true se almeno un contratto attivo ha rate generate */
  hasContractWithRates: boolean;
  /** ID del primo contratto attivo senza rate (per deep-link al piano pagamento) */
  orphanContractId: number | null;
  hasEvents: boolean;
}

/** Calcola la checklist onboarding da dati reali. */
export function computeOnboardingSteps(
  clientId: number,
  readiness: ClinicalReadinessClientItem | null,
  ctx: OnboardingContext,
): OnboardingStep[] {
  const anamnesiDone = readiness?.anamnesi_state === "structured";
  const measurementsDone = readiness?.has_measurements ?? false;
  const workoutDone = readiness?.has_workout_plan ?? false;

  // Contratto: 3 stati — nessuno, esiste ma senza rate, completo con rate
  const contractStep: OnboardingStep = ctx.hasContractWithRates
    ? {
        key: "contratto",
        label: "Contratto",
        description: "Pacchetto e piano pagamento attivo",
        completed: true,
        href: `/contratti?new=1&cliente=${clientId}`,
        icon: FileText,
      }
    : ctx.orphanContractId
      ? {
          key: "contratto",
          label: "Piano pagamento",
          description: "Il contratto esiste — genera le rate",
          completed: false,
          href: `/contratti/${ctx.orphanContractId}`,
          icon: FileText,
        }
      : {
          key: "contratto",
          label: "Contratto",
          description: "Pacchetto e piano pagamento — da qui parte tutto",
          completed: false,
          href: `/contratti?new=1&cliente=${clientId}`,
          icon: FileText,
        };

  return [
    contractStep,
    {
      key: "anamnesi",
      label: "Anamnesi",
      description: "Questionario clinico e stile di vita",
      completed: anamnesiDone,
      href: `/clienti/${clientId}/anamnesi`,
      icon: HeartPulse,
    },
    {
      key: "misurazioni",
      label: "Misurazioni base",
      description: "Peso, composizione corporea, circonferenze",
      completed: measurementsDone,
      href: `/clienti/${clientId}/misurazioni`,
      icon: Ruler,
    },
    {
      key: "scheda",
      label: "Scheda allenamento",
      description: "Programma personalizzato",
      completed: workoutDone,
      href: `/clienti/${clientId}?tab=schede&startScheda=1`,
      icon: Dumbbell,
    },
    {
      key: "sessione",
      label: "Prima sessione",
      description: "Prenota in agenda",
      completed: ctx.hasEvents,
      href: `/agenda?newEvent=1&clientId=${clientId}`,
      icon: Calendar,
    },
  ];
}

/** Hook: readiness di un singolo cliente dalla cache condivisa. */
export function useClientReadiness(clientId: number) {
  const query = useClinicalReadiness();
  const { data, isLoading } = query;

  const readiness = useMemo(() => {
    if (!data?.items) return null;
    return data.items.find((i) => i.client_id === clientId) ?? null;
  }, [data, clientId]);

  return {
    readiness,
    isLoading,
    isError: query.isError,
    isFetching: query.isFetching,
    refetch: query.refetch,
  };
}
