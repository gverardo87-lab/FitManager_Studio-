// src/lib/contract-status.tsx
/**
 * Vocabolario UNICO degli stati contratto — fonte sola dei *nomi* (display).
 *
 * SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI §2.4.
 * Mappa SOLO valore-enum → presentazione (label + className). ZERO logica di stato,
 * ZERO date, ZERO import di date-fns: la classificazione la produce il backend
 * (contract_state.py) e arriva sul wire come enum; qui si rende, basta.
 *
 * Due assi distinti, mai fusi (FDM §2/§5): stato di vita (LIFECYCLE) e sotto-stato
 * denaro (MONEY) hanno ciascuno il proprio badge.
 */

import { Badge } from "@/components/ui/badge";
import type { ContractLifecycle, ContractMoneySubstate } from "@/types/api";

interface BadgeStyle {
  label: string;
  className: string;
}

/** Asse VITA — etichette IT canoniche (chiudono TASSONOMIA §5: stesso concetto, stessa etichetta). */
export const LIFECYCLE_BADGE: Record<ContractLifecycle, BadgeStyle> = {
  attivo: {
    label: "Attivo",
    className: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400",
  },
  sospeso: {
    label: "Sospeso",
    className: "bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400",
  },
  esaurito: {
    label: "Esaurito",
    className: "bg-orange-100 text-orange-700 hover:bg-orange-100 dark:bg-orange-900/30 dark:text-orange-400",
  },
  chiuso: {
    label: "Chiuso",
    className: "bg-zinc-100 text-zinc-600 hover:bg-zinc-100 dark:bg-zinc-800 dark:text-zinc-400",
  },
};

/** Asse DENARO — sotto-stato del residuo (ortogonale alla vita, FDM §5). */
export const MONEY_BADGE: Record<ContractMoneySubstate, BadgeStyle> = {
  saldato: {
    label: "Saldato",
    className: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400",
  },
  pianificato: {
    label: "Pianificato",
    className: "bg-blue-100 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400",
  },
  parziale: {
    label: "Parziale",
    className: "bg-sky-100 text-sky-700 hover:bg-sky-100 dark:bg-sky-900/30 dark:text-sky-400",
  },
  // "Piano mancante" → warning amber: preserva il nudge dell'ex-badge omonimo (residuo>0, zero rate).
  da_pianificare: {
    label: "Da pianificare",
    className: "bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/40 dark:text-amber-400",
  },
};

/** Badge stato di vita — legge `lifecycle` dal SSoT, non calcola nulla. */
export function ContractLifecycleBadge({ lifecycle }: { lifecycle: ContractLifecycle }) {
  const style = LIFECYCLE_BADGE[lifecycle];
  if (!style) return null;
  return <Badge className={style.className}>{style.label}</Badge>;
}

/** Badge sotto-stato denaro — legge `money_substate` dal SSoT. */
export function ContractMoneyBadge({ money }: { money: ContractMoneySubstate }) {
  const style = MONEY_BADGE[money];
  if (!style) return null;
  return <Badge className={style.className}>{style.label}</Badge>;
}
