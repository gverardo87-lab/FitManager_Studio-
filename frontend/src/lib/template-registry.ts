// src/lib/template-registry.ts
/**
 * Registry di template scientifici per schede allenamento.
 *
 * Ogni template e' un descrittore compatto (~10 righe) che referenzia il sistema
 * blueprint esistente (SESSION_BLUEPRINTS + SLOT_VOLUME in blueprints.ts).
 * La funzione expandTemplate() materializza il template completo al momento della selezione.
 *
 * Vantaggi: zero duplicazione SSoT, se i parametri cambiano in SLOT_VOLUME
 * i template si aggiornano automaticamente.
 *
 * Fonti scientifiche:
 * - NSCA 2016 (Essentials of Strength Training, 4th ed)
 * - Schoenfeld 2010 (Effects of different volume-equated resistance training)
 * - Schoenfeld 2016 (Strength and hypertrophy: high vs low frequency)
 * - Schoenfeld 2017 (Dose-response relationship between volume and hypertrophy)
 * - Israetel RP 2020 (Renaissance Periodization volume landmarks)
 * - ACSM 2009 (Position Stand on Resistance Training)
 * - Helms 2019 (Muscle & Strength Pyramids)
 * - Ralston 2017 (Systematic review: strength vs hypertrophy training)
 */

import type { FitnessLevel, SlotType } from "./smart-programming/types";
import type { TemplateSession, WorkoutTemplate, TemplateExerciseSlot } from "./workout-templates";
import { SESSION_BLUEPRINTS, getSlotVolume, blueprintSlotLabel } from "./smart-programming/blueprints";
import { applyEmphasis, type EmphasisType } from "./template-emphasis";

// ── Types ──

export type TemplateFamily = "dimagrimento" | "tonificazione" | "ipertrofia" | "massa" | "forza";

export interface TemplateDescriptor {
  id: string;
  famiglia: TemplateFamily;
  nome: string;
  descrizione: string;
  frequenza: number;
  split: "FB" | "UL" | "PPL";
  livello: FitnessLevel;
  /** Obiettivo usato per lookup in SLOT_VOLUME (puo' non essere valido per il backend) */
  obiettivo_volume: string;
  /** Obiettivo salvato nel DB — deve essere in VALID_OBIETTIVI backend.
   *  Se omesso, usa obiettivo_volume. Necessario quando obiettivo_volume
   *  non e' un valore backend valido (es. "tonificazione" → "generale"). */
  obiettivo_backend?: string;
  emphasis: EmphasisType;
  durata_settimane: number;
  fonte: string;
}

// ── Family metadata (UI) ──

export interface FamilyMeta {
  label: string;
  icon: string;
  color: string;
  gradient: string;
  descrizione: string;
}

export const FAMILY_META: Record<TemplateFamily, FamilyMeta> = {
  dimagrimento: {
    label: "Dimagrimento",
    icon: "Flame",
    color: "text-orange-500",
    gradient: "from-orange-50 to-amber-100 dark:from-orange-950/30 dark:to-amber-900/20 border-orange-200 dark:border-orange-800",
    descrizione: "Circuiti ad alta densita metabolica, riposo ridotto",
  },
  tonificazione: {
    label: "Tonificazione",
    icon: "Heart",
    color: "text-pink-500",
    gradient: "from-pink-50 to-rose-100 dark:from-pink-950/30 dark:to-rose-900/20 border-pink-200 dark:border-pink-800",
    descrizione: "Volume moderato, rep medio-alte, adatto a principianti",
  },
  ipertrofia: {
    label: "Ipertrofia",
    icon: "TrendingUp",
    color: "text-blue-500",
    gradient: "from-blue-50 to-indigo-100 dark:from-blue-950/30 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800",
    descrizione: "Volume progressivo, range 6-12 rep, focus tensione meccanica",
  },
  massa: {
    label: "Massa",
    icon: "Dumbbell",
    color: "text-violet-500",
    gradient: "from-violet-50 to-purple-100 dark:from-violet-950/30 dark:to-purple-900/20 border-violet-200 dark:border-violet-800",
    descrizione: "Compound pesanti con volume ipertrofico, per intermedi-avanzati",
  },
  forza: {
    label: "Forza",
    icon: "Zap",
    color: "text-amber-500",
    gradient: "from-amber-50 to-yellow-100 dark:from-amber-950/30 dark:to-yellow-900/20 border-amber-200 dark:border-amber-800",
    descrizione: "Basse rep, alto carico, recupero completo",
  },
};

// ── Template Registry (11 template) ──

export const TEMPLATE_REGISTRY: TemplateDescriptor[] = [
  // Dimagrimento
  {
    id: "dimagrimento-3x-fb",
    famiglia: "dimagrimento",
    nome: "Full Body 3x Dimagrimento",
    descrizione: "3 sedute full body, riposo ridotto per densita metabolica. Intermedio.",
    frequenza: 3, split: "FB", livello: "intermedio",
    obiettivo_volume: "dimagrimento", emphasis: "light",
    durata_settimane: 6, fonte: "NSCA 2016",
  },
  {
    id: "dimagrimento-4x-ul",
    famiglia: "dimagrimento",
    nome: "Upper/Lower 4x Dimagrimento",
    descrizione: "4 sedute upper/lower, alta densita. Intermedio.",
    frequenza: 4, split: "UL", livello: "intermedio",
    obiettivo_volume: "dimagrimento", emphasis: "light",
    durata_settimane: 8, fonte: "NSCA 2016",
  },
  // Tonificazione
  {
    id: "tonificazione-3x-fb",
    famiglia: "tonificazione",
    nome: "Full Body 3x Tonificazione",
    descrizione: "3 sedute full body, rep medio-alte. Adatto a principianti.",
    frequenza: 3, split: "FB", livello: "beginner",
    obiettivo_volume: "tonificazione", obiettivo_backend: "generale",
    emphasis: "standard",
    durata_settimane: 6, fonte: "ACSM 2009",
  },
  {
    id: "tonificazione-4x-ul",
    famiglia: "tonificazione",
    nome: "Upper/Lower 4x Tonificazione",
    descrizione: "4 sedute upper/lower, volume bilanciato. Intermedio.",
    frequenza: 4, split: "UL", livello: "intermedio",
    obiettivo_volume: "tonificazione", obiettivo_backend: "generale",
    emphasis: "standard",
    durata_settimane: 8, fonte: "ACSM 2009",
  },
  // Ipertrofia
  {
    id: "ipertrofia-4x-ul",
    famiglia: "ipertrofia",
    nome: "Upper/Lower 4x Ipertrofia",
    descrizione: "4 sedute upper/lower, volume progressivo. Intermedio.",
    frequenza: 4, split: "UL", livello: "intermedio",
    obiettivo_volume: "ipertrofia", emphasis: "standard",
    durata_settimane: 8, fonte: "Schoenfeld 2010/2017",
  },
  {
    id: "ipertrofia-5x-ul",
    famiglia: "ipertrofia",
    nome: "Upper/Lower 5x Ipertrofia",
    descrizione: "5 sedute, frequenza alta per volume massimale. Avanzato.",
    frequenza: 5, split: "UL", livello: "avanzato",
    obiettivo_volume: "ipertrofia", emphasis: "standard",
    durata_settimane: 8, fonte: "Schoenfeld 2016",
  },
  {
    id: "ipertrofia-6x-ppl",
    famiglia: "ipertrofia",
    nome: "Push/Pull/Legs 6x Ipertrofia",
    descrizione: "6 sedute PPL, ogni muscolo 2x/sett. Avanzato.",
    frequenza: 6, split: "PPL", livello: "avanzato",
    obiettivo_volume: "ipertrofia", emphasis: "standard",
    durata_settimane: 8, fonte: "Schoenfeld 2016",
  },
  // Massa
  {
    id: "massa-4x-ul",
    famiglia: "massa",
    nome: "Upper/Lower 4x Massa",
    descrizione: "4 sedute, compound pesanti + volume accessorio. Intermedio.",
    frequenza: 4, split: "UL", livello: "intermedio",
    obiettivo_volume: "ipertrofia", emphasis: "heavy",
    durata_settimane: 8, fonte: "Helms 2019",
  },
  {
    id: "massa-5x-ul",
    famiglia: "massa",
    nome: "Upper/Lower 5x Massa",
    descrizione: "5 sedute, volume alto con compound pesanti. Avanzato.",
    frequenza: 5, split: "UL", livello: "avanzato",
    obiettivo_volume: "ipertrofia", emphasis: "heavy",
    durata_settimane: 10, fonte: "Helms 2019",
  },
  // Forza
  {
    id: "forza-3x-fb",
    famiglia: "forza",
    nome: "Full Body 3x Forza",
    descrizione: "3 sedute, basse rep con carico alto. Intermedio.",
    frequenza: 3, split: "FB", livello: "intermedio",
    obiettivo_volume: "forza", emphasis: "heavy",
    durata_settimane: 6, fonte: "NSCA 2016, Ralston 2017",
  },
  {
    id: "forza-4x-ul",
    famiglia: "forza",
    nome: "Upper/Lower 4x Forza",
    descrizione: "4 sedute upper/lower, periodizzazione forza. Avanzato.",
    frequenza: 4, split: "UL", livello: "avanzato",
    obiettivo_volume: "forza", emphasis: "heavy",
    durata_settimane: 8, fonte: "NSCA 2016, Ralston 2017",
  },
];

// ── Helpers ──

/** Filtra template per famiglia. */
export function getTemplatesForFamily(famiglia: TemplateFamily): TemplateDescriptor[] {
  return TEMPLATE_REGISTRY.filter((t) => t.famiglia === famiglia);
}

/** Split label per UI. */
const SPLIT_LABELS: Record<string, string> = {
  FB: "Full Body",
  UL: "Upper / Lower",
  PPL: "Push / Pull / Legs",
};

export function getSplitLabel(split: string): string {
  return SPLIT_LABELS[split] ?? split;
}

/** Livello label per UI. */
const LIVELLO_LABELS: Record<FitnessLevel, string> = {
  beginner: "Principiante",
  intermedio: "Intermedio",
  avanzato: "Avanzato",
};

export function getLivelloLabel(livello: FitnessLevel): string {
  return LIVELLO_LABELS[livello];
}

// ── Expand Template ──

/** Durata stimata per sessione in base al numero di slot. */
function estimateDuration(slotCount: number): number {
  if (slotCount <= 4) return 45;
  if (slotCount <= 6) return 60;
  return 70;
}

/**
 * Materializza un TemplateDescriptor in un WorkoutTemplate completo.
 *
 * Legge SESSION_BLUEPRINTS per la struttura sessione, SLOT_VOLUME per i parametri,
 * e applica l'emphasis modifier. Il risultato e' un WorkoutTemplate pronto per
 * handleSelectTemplate() — identico formato ai template statici esistenti.
 */
export function expandTemplate(descriptor: TemplateDescriptor): WorkoutTemplate {
  const blueprint = SESSION_BLUEPRINTS[descriptor.frequenza]?.[descriptor.livello];
  if (!blueprint) {
    throw new Error(
      `No blueprint for frequenza=${descriptor.frequenza}, livello=${descriptor.livello}`,
    );
  }

  const sessioni: TemplateSession[] = blueprint.sessioni.map((bp) => {
    const slots: TemplateExerciseSlot[] = bp.slots.map((slot) => {
      const baseVolume = getSlotVolume(slot.type, descriptor.obiettivo_volume);
      const volume = applyEmphasis(
        { serie: baseVolume.serie, ripetizioni: baseVolume.ripetizioni, riposo: baseVolume.riposo },
        slot.type,
        descriptor.emphasis,
      );

      return {
        sezione: "principale" as const,
        pattern_hint: slot.pattern_hint,
        label: blueprintSlotLabel(slot.type, slot.targetMuscle, slot.pattern_hint),
        serie: volume.serie,
        ripetizioni: volume.ripetizioni,
        tempo_riposo_sec: volume.riposo,
        muscoli_target: [slot.targetMuscle],
      };
    });

    return {
      nome_sessione: bp.nome,
      focus_muscolare: bp.focus,
      durata_minuti: estimateDuration(slots.length),
      slots,
    };
  });

  return {
    id: descriptor.id,
    nome: descriptor.nome,
    descrizione: descriptor.descrizione,
    livello: descriptor.livello,
    obiettivo_default: descriptor.obiettivo_backend ?? descriptor.obiettivo_volume,
    sessioni_per_settimana: descriptor.frequenza,
    durata_settimane: descriptor.durata_settimane,
    sessioni,
  };
}
