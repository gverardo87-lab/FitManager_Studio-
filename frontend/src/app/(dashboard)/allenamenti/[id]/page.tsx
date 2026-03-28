"use client";

import { useState, useMemo, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, CalendarDays, Settings2, Dumbbell, Target } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkout } from "@/hooks/useWorkouts";
import { useExercises } from "@/hooks/useExercises";
import {
  useWorkoutSchedule,
  useCompleteScheduleSlot,
  useUpdateScheduleSlot,
  useDeleteScheduleSlot,
} from "@/hooks/useWorkoutSchedule";
import { ScheduleCalendar } from "@/components/workouts/schedule/ScheduleCalendar";
import { ScheduleSetupDialog } from "@/components/workouts/schedule/ScheduleSetupDialog";
import { SlotDetailSheet } from "@/components/workouts/schedule/SlotDetailSheet";
import { usePageReveal } from "@/lib/page-reveal";
import { resolveBackNavigation } from "@/lib/url-state";
import { MUSCLE_LABELS } from "@/components/exercises/exercise-constants";
import type { ScheduleSlot, WorkoutPlan, Exercise } from "@/types/api";

const TEMPLATE_NAME_RE = /^(full body|upper|lower|push|pull|legs|sessione\s+\d)/i;

/** Build session_id → derived name map from plan exercises + catalog muscles. */
function buildSessionNameMap(
  plan: WorkoutPlan,
  exerciseMap: Map<number, Exercise>,
): Map<number, string> {
  const map = new Map<number, string>();
  for (const s of plan.sessioni) {
    if (!TEMPLATE_NAME_RE.test(s.nome_sessione)) continue;
    const counts = new Map<string, number>();
    const allEx = [...s.esercizi, ...s.blocchi.flatMap((b) => b.esercizi)];
    for (const ex of allEx) {
      const data = exerciseMap.get(ex.id_esercizio);
      if (!data?.muscoli_primari) continue;
      for (const m of data.muscoli_primari) {
        counts.set(m, (counts.get(m) ?? 0) + 1);
      }
    }
    if (counts.size === 0) continue;
    const top3 = [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([slug]) => MUSCLE_LABELS[slug] ?? slug);
    map.set(s.id, `Sessione ${s.numero_sessione} — ${top3.join(", ")}`);
  }
  return map;
}

const OBIETTIVO_LABELS: Record<string, string> = {
  forza: "Forza",
  ipertrofia: "Ipertrofia",
  resistenza: "Resistenza",
  dimagrimento: "Dimagrimento",
  generale: "Generale",
};

const LIVELLO_LABELS: Record<string, string> = {
  beginner: "Principiante",
  intermedio: "Intermedio",
  avanzato: "Avanzato",
};

export default function WorkoutSchedulePage() {
  const params = useParams();
  const workoutId = Number(params.id);
  const fromParam = useSearchParams().get("from");
  const { revealClass, revealStyle } = usePageReveal();
  const backNav = resolveBackNavigation(fromParam, { href: "/allenamenti", label: "Allenamenti" });

  const { data: plan, isLoading: planLoading } = useWorkout(workoutId);
  const { data: scheduleData, isLoading: scheduleLoading } = useWorkoutSchedule(workoutId);
  const { data: exerciseData } = useExercises();
  const exerciseMap = useMemo(
    () => new Map((exerciseData?.items ?? []).map((e) => [e.id, e])),
    [exerciseData],
  );

  const [setupOpen, setSetupOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<ScheduleSlot | null>(null);

  const completeMutation = useCompleteScheduleSlot(workoutId);
  const updateMutation = useUpdateScheduleSlot(workoutId);
  const deleteMutation = useDeleteScheduleSlot(workoutId);

  // Derive real session names from exercises when DB has template names
  const sessionNameMap = useMemo(
    () => (plan ? buildSessionNameMap(plan, exerciseMap) : new Map<number, string>()),
    [plan, exerciseMap],
  );

  const slots = useMemo(() => {
    const raw = scheduleData?.items ?? [];
    if (sessionNameMap.size === 0) return raw;
    return raw.map((s) => {
      const derived = sessionNameMap.get(s.id_sessione);
      return derived ? { ...s, sessione_nome: derived } : s;
    });
  }, [scheduleData, sessionNameMap]);
  const hasSchedule = slots.length > 0;

  // Compliance stats + week progress (single pass)
  const stats = useMemo(() => {
    if (slots.length === 0)
      return { completed: 0, total: 0, skipped: 0, pct: 0, weeksDone: 0, weeksTotal: 0 };

    let completed = 0;
    let skipped = 0;
    const weekSlots = new Map<string, ScheduleSlot[]>();

    for (const s of slots) {
      if (s.stato === "completato") completed++;
      else if (s.stato === "saltato") skipped++;

      // Group by ISO week (monday date)
      const d = new Date(s.data_pianificata + "T00:00:00");
      const day = d.getDay();
      const diff = day === 0 ? -6 : 1 - day;
      d.setDate(d.getDate() + diff);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      const arr = weekSlots.get(key) ?? [];
      arr.push(s);
      weekSlots.set(key, arr);
    }

    const total = slots.length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    // A week is "done" when all its slots are completato or saltato
    let weeksDone = 0;
    for (const ws of weekSlots.values()) {
      if (ws.every((s) => s.stato === "completato" || s.stato === "saltato")) weeksDone++;
    }

    return { completed, total, skipped, pct, weeksDone, weeksTotal: weekSlots.size };
  }, [slots]);

  const complianceColor =
    stats.pct >= 80 ? "text-emerald-600" : stats.pct >= 50 ? "text-amber-600" : "text-red-600";

  const handleComplete = useCallback(
    (slotId: number) => completeMutation.mutate(slotId),
    [completeMutation],
  );

  const handleSkip = useCallback(
    (slotId: number) =>
      updateMutation.mutate({ slotId, stato: "saltato" }),
    [updateMutation],
  );

  const handleDelete = useCallback(
    (slotId: number) => deleteMutation.mutate(slotId),
    [deleteMutation],
  );

  const handleMove = useCallback(
    (slotId: number, newDate: string) =>
      updateMutation.mutate({ slotId, data_pianificata: newDate }),
    [updateMutation],
  );

  const handleReopen = useCallback(
    (slotId: number) =>
      updateMutation.mutate({ slotId, stato: "pianificato" }),
    [updateMutation],
  );

  const handleSlotClick = useCallback((slot: ScheduleSlot) => {
    setSelectedSlot(slot);
  }, []);

  if (planLoading || scheduleLoading) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        Scheda non trovata
      </div>
    );
  }

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div className={revealClass(0)} style={revealStyle(0)}>
        <div className="flex items-center gap-2 mb-1">
          <Link
            href={backNav.href}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title={backNav.label}
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <h1 className="text-xl font-semibold truncate">{plan.nome}</h1>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {plan.client_nome && (
            <span className="text-sm text-muted-foreground">
              {plan.client_nome} {plan.client_cognome}
            </span>
          )}
          <Badge variant="outline" className="text-xs">
            <Target className="mr-1 h-3 w-3" />
            {OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {LIVELLO_LABELS[plan.livello] ?? plan.livello}
          </Badge>
          <Badge variant="outline" className="text-xs">
            <Dumbbell className="mr-1 h-3 w-3" />
            {plan.sessioni.length} sessioni
          </Badge>
          <Button
            variant="outline"
            size="sm"
            className="ml-auto"
            onClick={() => setSetupOpen(true)}
          >
            <Settings2 className="h-4 w-4 mr-1.5" />
            <span className="hidden sm:inline">
              {hasSchedule ? "Ripianifica" : "Pianifica"}
            </span>
          </Button>
        </div>
      </div>

      {/* Inline KPI + progress */}
      {hasSchedule && (
        <div className={revealClass(50)} style={revealStyle(50)}>
          <div className="flex items-center gap-3 rounded-lg border bg-card px-4 py-2.5">
            {/* Stats */}
            <div className="flex items-center gap-4 text-sm">
              <span>
                <span className="font-semibold text-emerald-600">{stats.completed}</span>
                <span className="text-muted-foreground ml-1">completate</span>
              </span>
              <span className="text-muted-foreground/30">|</span>
              <span>
                <span className={`font-semibold ${complianceColor}`}>{stats.pct}%</span>
                <span className="text-muted-foreground ml-1">compliance</span>
              </span>
              <span className="text-muted-foreground/30">|</span>
              <span>
                <span className="font-semibold text-zinc-500">
                  {stats.total - stats.completed - stats.skipped}
                </span>
                <span className="text-muted-foreground ml-1">rimanenti</span>
              </span>
            </div>

            {/* Week progress */}
            {stats.weeksTotal > 0 ? (
              <>
                <div className="ml-auto" />
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full bg-teal-500 transition-all duration-500"
                      style={{ width: `${Math.round((stats.weeksDone / stats.weeksTotal) * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {stats.weeksDone}/{stats.weeksTotal} sett.
                  </span>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}

      {/* Calendar or empty state */}
      <div className={revealClass(100)} style={revealStyle(100)}>
        {hasSchedule ? (
          <ScheduleCalendar
            slots={slots}
            onComplete={handleComplete}
            onSkip={handleSkip}
            onDelete={handleDelete}
            onSlotClick={handleSlotClick}
            onMove={handleMove}
            onReopen={handleReopen}
          />
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed py-16 text-center">
            <CalendarDays className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium mb-1">Nessun calendario</h3>
            <p className="text-sm text-muted-foreground mb-4 max-w-sm">
              Pianifica quando il cliente si allena per avere un calendario
              visivo con monitoraggio integrato.
            </p>
            <Button onClick={() => setSetupOpen(true)}>
              <CalendarDays className="h-4 w-4 mr-2" />
              Pianifica Calendario
            </Button>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <ScheduleSetupDialog
        plan={plan}
        open={setupOpen}
        onOpenChange={setSetupOpen}
        onGenerated={() => {}}
        sessionNameMap={sessionNameMap}
      />

      {selectedSlot && (
        <SlotDetailSheet
          slot={selectedSlot}
          plan={plan}
          open={!!selectedSlot}
          onOpenChange={(open) => {
            if (!open) setSelectedSlot(null);
          }}
          onComplete={handleComplete}
          onSkip={handleSkip}
          onReopen={handleReopen}
        />
      )}
    </div>
  );
}
