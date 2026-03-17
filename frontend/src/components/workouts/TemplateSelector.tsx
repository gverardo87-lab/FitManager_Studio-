// src/components/workouts/TemplateSelector.tsx
"use client";

/**
 * Modale per scegliere un template di partenza per una nuova scheda.
 *
 * Flusso UI:
 * 1. Selezione cliente (opzionale)
 * 2. Scheda Smart (backend-first, configurazione inline)
 * 3. 5 chip famiglia (Dimagrimento, Tonificazione, Ipertrofia, Massa, Forza)
 * 4. Click su famiglia → card varianti con frequenza/split/livello/fonte
 * 5. Click su variante → expandTemplate() → handleSelectTemplate() → builder
 * 6. Opzioni alternative in fondo: Standard e Con blocchi
 */

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Zap, TrendingUp, Flame, FileText, User, Brain, Sparkles, Layers,
  Heart, Dumbbell, ChevronLeft, Clock, BookOpen,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  SECTION_CATEGORIES,
  type WorkoutTemplate,
  type TemplateExerciseSlot,
} from "@/lib/workout-templates";
import {
  TEMPLATE_REGISTRY,
  FAMILY_META,
  getTemplatesForFamily,
  getSplitLabel,
  getLivelloLabel,
  expandTemplate,
  type TemplateFamily,
  type TemplateDescriptor,
} from "@/lib/template-registry";
import { storeSmartPlanPackage } from "@/lib/smart-plan-package-cache";
import { useCreateWorkout } from "@/hooks/useWorkouts";
import { useExercises } from "@/hooks/useExercises";
import { useClients } from "@/hooks/useClients";
import { useGeneratePlanPackage } from "@/hooks/useTrainingScience";
import type {
  Exercise,
  TSBuilderLevelChoice,
  TSBuilderObjective,
  WorkoutSessionInput,
  WorkoutExerciseInput,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// MATCHING BASE
// ════════════════════════════════════════════════════════════

const DIFFICULTY_MAP: Record<string, string> = {
  beginner: "beginner",
  intermedio: "intermediate",
  avanzato: "advanced",
};

function muscleOverlap(a: string[], b: string[]): number {
  return a.filter((m) => b.includes(m)).length;
}

function findBestExercise(
  exercises: Exercise[],
  slot: TemplateExerciseSlot,
  templateLevel: string,
  usedIds: Set<number>,
  lastEquipment?: string,
): Exercise | undefined {
  const preferred = DIFFICULTY_MAP[templateLevel] ?? "intermediate";

  let candidates: Exercise[];
  if (slot.sezione === "avviamento") {
    candidates = exercises.filter(
      (e) => SECTION_CATEGORIES.avviamento.includes(e.categoria) && !usedIds.has(e.id),
    );
  } else if (slot.sezione === "stretching") {
    candidates = exercises.filter(
      (e) => SECTION_CATEGORIES.stretching.includes(e.categoria) && !usedIds.has(e.id),
    );
  } else {
    candidates = exercises.filter(
      (e) => e.pattern_movimento === slot.pattern_hint && !usedIds.has(e.id),
    );
  }

  if (candidates.length === 0) {
    if (slot.sezione === "avviamento") {
      candidates = exercises.filter((e) => SECTION_CATEGORIES.avviamento.includes(e.categoria));
    } else if (slot.sezione === "stretching") {
      candidates = exercises.filter((e) => SECTION_CATEGORIES.stretching.includes(e.categoria));
    } else {
      candidates = exercises.filter((e) => e.pattern_movimento === slot.pattern_hint);
    }
  }

  if (candidates.length === 0) {
    return exercises.find((e) => !usedIds.has(e.id)) ?? exercises[0];
  }

  const targetMuscles = slot.muscoli_target ?? [];

  candidates.sort((a, b) => {
    let scoreA = 0;
    let scoreB = 0;

    if (a.difficolta === preferred) scoreA += 10;
    if (b.difficolta === preferred) scoreB += 10;

    if (targetMuscles.length > 0) {
      scoreA += muscleOverlap(a.muscoli_primari, targetMuscles) * 8;
      scoreB += muscleOverlap(b.muscoli_primari, targetMuscles) * 8;
    }

    if (a.categoria === "compound") scoreA += 3;
    if (b.categoria === "compound") scoreB += 3;

    if (a.categoria === "bodyweight") scoreA += 1;
    if (b.categoria === "bodyweight") scoreB += 1;

    if (lastEquipment && slot.sezione === "principale") {
      if (a.attrezzatura === lastEquipment) scoreA -= 3;
      if (b.attrezzatura === lastEquipment) scoreB -= 3;
    }

    return scoreB - scoreA;
  });

  return candidates[0];
}

// ════════════════════════════════════════════════════════════
// FAMILY ICONS (hoisted — React elements, stable references)
// ════════════════════════════════════════════════════════════

const FAMILY_ICONS: Record<TemplateFamily, React.ReactNode> = {
  dimagrimento: <Flame className="h-4 w-4" />,
  tonificazione: <Heart className="h-4 w-4" />,
  ipertrofia: <TrendingUp className="h-4 w-4" />,
  massa: <Dumbbell className="h-4 w-4" />,
  forza: <Zap className="h-4 w-4" />,
};

const FAMILY_ORDER: TemplateFamily[] = [
  "dimagrimento", "tonificazione", "ipertrofia", "massa", "forza",
];

const CHIP_COLORS: Record<TemplateFamily, string> = {
  dimagrimento: "bg-orange-100 text-orange-700 hover:bg-orange-200 dark:bg-orange-900/40 dark:text-orange-300 dark:hover:bg-orange-900/60",
  tonificazione: "bg-pink-100 text-pink-700 hover:bg-pink-200 dark:bg-pink-900/40 dark:text-pink-300 dark:hover:bg-pink-900/60",
  ipertrofia: "bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/40 dark:text-blue-300 dark:hover:bg-blue-900/60",
  massa: "bg-violet-100 text-violet-700 hover:bg-violet-200 dark:bg-violet-900/40 dark:text-violet-300 dark:hover:bg-violet-900/60",
  forza: "bg-amber-100 text-amber-700 hover:bg-amber-200 dark:bg-amber-900/40 dark:text-amber-300 dark:hover:bg-amber-900/60",
};

const CHIP_COLORS_ACTIVE: Record<TemplateFamily, string> = {
  dimagrimento: "bg-orange-500 text-white dark:bg-orange-600",
  tonificazione: "bg-pink-500 text-white dark:bg-pink-600",
  ipertrofia: "bg-blue-500 text-white dark:bg-blue-600",
  massa: "bg-violet-500 text-white dark:bg-violet-600",
  forza: "bg-amber-500 text-white dark:bg-amber-600",
};

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

interface TemplateSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId?: number;
  fromContext?: string;
}

export function TemplateSelector(props: TemplateSelectorProps) {
  const { open, clientId } = props;
  if (!open) return null;

  const dialogKey = `template-selector-${clientId ?? "none"}`;
  return <TemplateSelectorDialog key={dialogKey} {...props} />;
}

function TemplateSelectorDialog({ open, onOpenChange, clientId, fromContext }: TemplateSelectorProps) {
  const router = useRouter();
  const createWorkout = useCreateWorkout();
  const generatePlanPackage = useGeneratePlanPackage();
  const { data: exerciseData } = useExercises();
  const exercises = useMemo(() => exerciseData?.items ?? [], [exerciseData]);
  const { data: clientsData } = useClients();
  const clients = useMemo(() => clientsData?.items ?? [], [clientsData]);

  const [selectedClientId, setSelectedClientId] = useState<number | null>(clientId ?? null);
  const [selectedFamily, setSelectedFamily] = useState<TemplateFamily | null>(null);

  // Smart config
  const [smartSessions, setSmartSessions] = useState<number>(4);
  const [smartObiettivo, setSmartObiettivo] = useState<TSBuilderObjective>("generale");
  const [smartLivello, setSmartLivello] = useState<TSBuilderLevelChoice>("auto");

  // Varianti per famiglia selezionata
  const familyVariants = useMemo(
    () => (selectedFamily ? getTemplatesForFamily(selectedFamily) : []),
    [selectedFamily],
  );

  const handleSelectTemplate = useCallback(
    (template: WorkoutTemplate) => {
      if (exercises.length === 0) return;

      const sessioni: WorkoutSessionInput[] = template.sessioni.map((sess) => {
        const usedIds = new Set<number>();
        let lastEquipment: string | undefined;

        return {
          nome_sessione: sess.nome_sessione,
          focus_muscolare: sess.focus_muscolare,
          durata_minuti: sess.durata_minuti,
          esercizi: sess.slots.map((slot, slotIdx): WorkoutExerciseInput => {
            const match = findBestExercise(
              exercises, slot, template.livello, usedIds, lastEquipment,
            );
            if (match) {
              usedIds.add(match.id);
              if (slot.sezione === "principale") lastEquipment = match.attrezzatura;
            }

            return {
              id_esercizio: match?.id ?? exercises[0].id,
              ordine: slotIdx + 1,
              serie: slot.serie,
              ripetizioni: slot.ripetizioni,
              tempo_riposo_sec: slot.tempo_riposo_sec,
              note: slot.label,
            };
          }),
        };
      });

      createWorkout.mutate(
        {
          nome: template.nome,
          obiettivo: template.obiettivo_default,
          livello: template.livello,
          sessioni_per_settimana: template.sessioni_per_settimana,
          durata_settimane: template.durata_settimane,
          id_cliente: selectedClientId,
          sessioni,
        },
        {
          onSuccess: (plan) => {
            onOpenChange(false);
            router.push(`/schede/${plan.id}${fromContext ? `?from=${fromContext}` : ""}`);
          },
        },
      );
    },
    [createWorkout, selectedClientId, onOpenChange, router, exercises, fromContext],
  );

  const handleSelectDescriptor = useCallback(
    (descriptor: TemplateDescriptor) => {
      const template = expandTemplate(descriptor);
      handleSelectTemplate(template);
    },
    [handleSelectTemplate],
  );

  const handleBlankSheet = useCallback(() => {
    const firstExercise = exercises[0];
    createWorkout.mutate(
      {
        nome: "Nuova Scheda",
        obiettivo: "generale",
        livello: "intermedio",
        sessioni_per_settimana: 3,
        durata_settimane: 4,
        id_cliente: selectedClientId,
        sessioni: [
          {
            nome_sessione: "Sessione 1",
            durata_minuti: 60,
            esercizi: [
              {
                id_esercizio: firstExercise?.id ?? 1,
                ordine: 1,
                serie: 3,
                ripetizioni: "8-12",
                tempo_riposo_sec: 90,
              },
            ],
          },
        ],
      },
      {
        onSuccess: (plan) => {
          onOpenChange(false);
          router.push(`/schede/${plan.id}${fromContext ? `?from=${fromContext}` : ""}`);
        },
      },
    );
  }, [createWorkout, selectedClientId, onOpenChange, router, exercises, fromContext]);

  const handleBlankSheetHybrid = useCallback(() => {
    createWorkout.mutate(
      {
        nome: "Nuova Scheda",
        obiettivo: "generale",
        livello: "intermedio",
        sessioni_per_settimana: 3,
        durata_settimane: 4,
        id_cliente: selectedClientId,
        sessioni: [
          {
            nome_sessione: "Sessione 1",
            durata_minuti: 60,
            esercizi: [],
            blocchi: [
              {
                tipo_blocco: "circuit",
                ordine: 1,
                nome: null,
                giri: 3,
                durata_lavoro_sec: null,
                durata_riposo_sec: 15,
                durata_blocco_sec: null,
                note: null,
                esercizi: [],
              },
            ],
          },
        ],
      },
      {
        onSuccess: (plan) => {
          onOpenChange(false);
          router.push(`/schede/${plan.id}${fromContext ? `?from=${fromContext}` : ""}`);
        },
      },
    );
  }, [createWorkout, selectedClientId, onOpenChange, router, fromContext]);

  const handleSmartTemplate = useCallback(() => {
    generatePlanPackage.mutate(
      {
        client_id: selectedClientId,
        preset: {
          frequenza: smartSessions,
          obiettivo_builder: smartObiettivo,
          livello_choice: smartLivello,
        },
      },
      {
        onSuccess: (planPackage) => {
          createWorkout.mutate(
            planPackage.workout_projection.draft,
            {
              onSuccess: (plan) => {
                storeSmartPlanPackage(plan.id, planPackage);
                onOpenChange(false);
                router.push(`/schede/${plan.id}${fromContext ? `?from=${fromContext}` : ""}`);
              },
            },
          );
        },
      },
    );
  }, [
    createWorkout, generatePlanPackage, selectedClientId,
    smartSessions, smartObiettivo, smartLivello,
    onOpenChange, router, fromContext,
  ]);

  const isTemplateLoading = !exerciseData || exercises.length === 0;
  const isSmartPending = generatePlanPackage.isPending || createWorkout.isPending;
  const _templateCount = TEMPLATE_REGISTRY.length; // 11

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nuova Scheda Allenamento</DialogTitle>
          <DialogDescription>
            Scegli un template scientifico, genera con Smart o parti da zero.
          </DialogDescription>
        </DialogHeader>

        {/* Selezione cliente */}
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-muted-foreground shrink-0" />
          <Select
            value={selectedClientId ? String(selectedClientId) : "__none__"}
            onValueChange={(v) => setSelectedClientId(v === "__none__" ? null : Number(v))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Seleziona cliente (opzionale)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">Nessun cliente (scheda generica)</SelectItem>
              {clients.map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.nome} {c.cognome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Card Scheda Smart */}
        <div className="relative rounded-xl border bg-gradient-to-br from-teal-50 to-cyan-100 dark:from-teal-950/30 dark:to-cyan-900/20 border-teal-200 dark:border-teal-800 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-teal-600 dark:text-teal-400" />
            <h3 className="font-semibold text-sm">Scheda Smart</h3>
            <Badge variant="secondary" className="text-[10px] bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300">
              Backend-first
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Genera una scheda dal profilo cliente reale con piano scientifico canonico e ranking esercizi deterministico lato backend.
          </p>

          <div className="grid grid-cols-3 gap-2">
            <div className="space-y-1">
              <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Sessioni/Sett</Label>
              <Select value={String(smartSessions)} onValueChange={(v) => setSmartSessions(Number(v))}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[2, 3, 4, 5, 6].map(n => (
                    <SelectItem key={n} value={String(n)}>{n}x</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Obiettivo</Label>
              <Select value={smartObiettivo} onValueChange={(v) => setSmartObiettivo(v as TSBuilderObjective)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="generale">Generale</SelectItem>
                  <SelectItem value="forza">Forza</SelectItem>
                  <SelectItem value="ipertrofia">Ipertrofia</SelectItem>
                  <SelectItem value="resistenza">Resistenza</SelectItem>
                  <SelectItem value="dimagrimento">Dimagrimento</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">Livello</Label>
              <Select value={smartLivello} onValueChange={(v) => setSmartLivello(v as TSBuilderLevelChoice)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto (backend)</SelectItem>
                  <SelectItem value="beginner">Principiante</SelectItem>
                  <SelectItem value="intermedio">Intermedio</SelectItem>
                  <SelectItem value="avanzato">Avanzato</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex flex-wrap gap-1">
              {selectedClientId ? (
                <>
                  <Badge variant="outline" className="text-[10px] border-teal-300 dark:border-teal-700">
                    Cliente collegato
                  </Badge>
                  <Badge variant="outline" className="text-[10px] border-teal-300 dark:border-teal-700">
                    Ranking deterministico
                  </Badge>
                </>
              ) : null}
            </div>
            <Button
              size="sm"
              onClick={handleSmartTemplate}
              disabled={isSmartPending}
              className="bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {generatePlanPackage.isPending ? "Genero..." : "Genera"}
            </Button>
          </div>
        </div>

        {/* Template Scientifici — Chip famiglia */}
        <div className="space-y-3 mt-1">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Template Scientifici</span>
            <span className="text-xs text-muted-foreground">({TEMPLATE_REGISTRY.length} varianti)</span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {FAMILY_ORDER.map((fam) => {
              const meta = FAMILY_META[fam];
              const isActive = selectedFamily === fam;
              return (
                <button
                  key={fam}
                  onClick={() => setSelectedFamily(isActive ? null : fam)}
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
                    isActive ? CHIP_COLORS_ACTIVE[fam] : CHIP_COLORS[fam]
                  }`}
                >
                  {FAMILY_ICONS[fam]}
                  {meta.label}
                </button>
              );
            })}
          </div>

          {/* Varianti per famiglia selezionata */}
          {selectedFamily && familyVariants.length > 0 ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedFamily(null)}
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-0.5"
                >
                  <ChevronLeft className="h-3 w-3" />
                  Tutte le famiglie
                </button>
                <span className="text-xs text-muted-foreground">
                  {FAMILY_META[selectedFamily].descrizione}
                </span>
              </div>

              <div className="grid gap-2 sm:grid-cols-2">
                {familyVariants.map((descriptor) => (
                  <VariantCard
                    key={descriptor.id}
                    descriptor={descriptor}
                    famiglia={selectedFamily}
                    onSelect={handleSelectDescriptor}
                    disabled={createWorkout.isPending || isTemplateLoading}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </div>

        {/* Scheda vuota */}
        <div className="grid grid-cols-2 gap-2 mt-1">
          <button
            onClick={handleBlankSheet}
            disabled={createWorkout.isPending || isTemplateLoading}
            className="flex items-start gap-3 rounded-xl border border-dashed p-4 text-left transition-colors hover:bg-muted/50 disabled:opacity-50"
          >
            <FileText className="h-5 w-5 mt-0.5 text-muted-foreground shrink-0" />
            <div>
              <h3 className="font-semibold text-sm">Standard</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Esercizi per sezione: avviamento, principale, stretching.
              </p>
            </div>
          </button>

          <button
            onClick={handleBlankSheetHybrid}
            disabled={createWorkout.isPending || isTemplateLoading}
            className="flex items-start gap-3 rounded-xl border border-dashed p-4 text-left transition-colors hover:bg-muted/50 disabled:opacity-50"
          >
            <Layers className="h-5 w-5 mt-0.5 text-muted-foreground shrink-0" />
            <div>
              <h3 className="font-semibold text-sm">Con blocchi</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Parte con un circuito in Principale, pronto da riempire.
              </p>
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════
// VARIANT CARD
// ════════════════════════════════════════════════════════════

interface VariantCardProps {
  descriptor: TemplateDescriptor;
  famiglia: TemplateFamily;
  onSelect: (d: TemplateDescriptor) => void;
  disabled: boolean;
}

function VariantCard({ descriptor, famiglia, onSelect, disabled }: VariantCardProps) {
  const meta = FAMILY_META[famiglia];

  return (
    <button
      onClick={() => onSelect(descriptor)}
      disabled={disabled}
      className={`group rounded-xl border bg-gradient-to-br ${meta.gradient} p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-50`}
    >
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-sm">{getSplitLabel(descriptor.split)}</h4>
        <Badge variant="outline" className="text-[10px]">
          {descriptor.frequenza}x/sett
        </Badge>
      </div>

      <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">
        {descriptor.descrizione}
      </p>

      <div className="mt-2.5 flex flex-wrap gap-1">
        <Badge variant="secondary" className="text-[10px] gap-1">
          <Clock className="h-2.5 w-2.5" />
          {descriptor.durata_settimane} sett
        </Badge>
        <Badge variant="secondary" className="text-[10px]">
          {getLivelloLabel(descriptor.livello)}
        </Badge>
        <Badge variant="outline" className="text-[10px] text-muted-foreground">
          {descriptor.fonte}
        </Badge>
      </div>
    </button>
  );
}
