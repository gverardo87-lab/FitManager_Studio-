"use client";

import { useState, useMemo, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CalendarDays, Settings2, Dumbbell, Target } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkout } from "@/hooks/useWorkouts";
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
import type { ScheduleSlot } from "@/types/api";

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
  const router = useRouter();
  const workoutId = Number(params.id);
  const { revealClass, revealStyle } = usePageReveal();

  const { data: plan, isLoading: planLoading } = useWorkout(workoutId);
  const { data: scheduleData, isLoading: scheduleLoading } = useWorkoutSchedule(workoutId);

  const [weekOffset, setWeekOffset] = useState(0);
  const [setupOpen, setSetupOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<ScheduleSlot | null>(null);

  const completeMutation = useCompleteScheduleSlot(workoutId);
  const updateMutation = useUpdateScheduleSlot(workoutId);
  const deleteMutation = useDeleteScheduleSlot(workoutId);

  const slots = scheduleData?.items ?? [];
  const hasSchedule = slots.length > 0;

  // Compliance stats
  const stats = useMemo(() => {
    if (slots.length === 0) return { completed: 0, total: 0, skipped: 0, pct: 0 };
    const completed = slots.filter((s) => s.stato === "completato").length;
    const skipped = slots.filter((s) => s.stato === "saltato").length;
    const total = slots.length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { completed, total, skipped, pct };
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
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Link
                href={resolveBackNavigation(null, { href: "/allenamenti", label: "Allenamenti" }).href}
                className="text-muted-foreground hover:text-foreground transition-colors"
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
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setSetupOpen(true)}
          >
            <Settings2 className="h-4 w-4 mr-1.5" />
            <span className="hidden sm:inline">
              {hasSchedule ? "Ripianifica" : "Pianifica"}
            </span>
          </Button>
        </div>
      </div>

      {/* KPI bar */}
      {hasSchedule && (
        <div className={revealClass(50)} style={revealStyle(50)}>
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border bg-card p-3 text-center">
              <p className="text-2xl font-bold text-emerald-600">{stats.completed}</p>
              <p className="text-xs text-muted-foreground">Completate</p>
            </div>
            <div className="rounded-lg border bg-card p-3 text-center">
              <p className={`text-2xl font-bold ${complianceColor}`}>{stats.pct}%</p>
              <p className="text-xs text-muted-foreground">Compliance</p>
            </div>
            <div className="rounded-lg border bg-card p-3 text-center">
              <p className="text-2xl font-bold text-zinc-500">
                {stats.total - stats.completed - stats.skipped}
              </p>
              <p className="text-xs text-muted-foreground">Rimanenti</p>
            </div>
          </div>
        </div>
      )}

      {/* Calendar or empty state */}
      <div className={revealClass(100)} style={revealStyle(100)}>
        {hasSchedule ? (
          <ScheduleCalendar
            slots={slots}
            currentWeekOffset={weekOffset}
            onWeekChange={setWeekOffset}
            onComplete={handleComplete}
            onSkip={handleSkip}
            onDelete={handleDelete}
            onSlotClick={handleSlotClick}
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
        onGenerated={() => setWeekOffset(0)}
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
        />
      )}
    </div>
  );
}
