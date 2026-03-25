// src/components/workouts/ExerciseSelector.tsx
"use client";

/**
 * Exercise Selector — dialog professionale split-panel (stile FoodSearchSidebar).
 *
 * Layout: max-w-[1100px] h-[82vh]
 * - Sinistra (60%): search + tab pattern + lista tabellare
 * - Destra (40%): dettaglio esercizio selezionato (muscoli, safety, biomeccanica, alternative)
 *
 * Pattern adattato da FoodSearchSidebar (ADR-008 upgrade).
 */

import { useState, useMemo, useCallback, useEffect, useRef, memo } from "react";
import {
  Search, X, Dumbbell, ShieldAlert, AlertTriangle, Info, CheckCircle2,
  RefreshCw, ArrowRightLeft, ChevronDown, Target,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

import { useExercises, useExerciseRelations } from "@/hooks/useExercises";
import { ExerciseDetailPanel } from "./ExerciseDetailPanel";
import { getReplacementReason, getReplacementScore } from "@/lib/exercise-replacement";
import type { Exercise, ExerciseSafetyEntry, TSExerciseFeasibilityEntry } from "@/types/api";
import {
  MUSCLE_LABELS,
  MUSCLE_COLORS,
  EQUIPMENT_LABELS,
  DIFFICULTY_LABELS,
  FORCE_TYPE_LABELS,
  LATERAL_PATTERN_LABELS,
} from "@/components/exercises/exercise-constants";

// ════════════════════════════════════════════════════════════
// RECENT EXERCISES (sessionStorage)
// ════════════════════════════════════════════════════════════

type RecentSection = "avviamento" | "principale" | "stretching";
interface RecentExerciseItem { id: number; section: RecentSection; ts: number; }

const RECENT_STORAGE_KEY = "workout-builder-recent-exercises-v1";
const RECENT_MAX_GLOBAL = 60;
const RECENT_MAX_PER_SECTION = 12;

function resolveRecentSection(categoryFilter?: string[]): RecentSection {
  if (categoryFilter?.includes("avviamento")) return "avviamento";
  if (categoryFilter?.some((c) => c === "stretching" || c === "mobilita")) return "stretching";
  return "principale";
}

function loadRecentExercises(): RecentExerciseItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(RECENT_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((item): item is RecentExerciseItem =>
        !!item && typeof item === "object" &&
        typeof (item as RecentExerciseItem).id === "number" &&
        typeof (item as RecentExerciseItem).section === "string" &&
        typeof (item as RecentExerciseItem).ts === "number",
      )
      .slice(0, RECENT_MAX_GLOBAL);
  } catch { return []; }
}

function saveRecentExercises(items: RecentExerciseItem[]): void {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(items.slice(0, RECENT_MAX_GLOBAL))); }
  catch { /* best effort */ }
}

function pushRecentExercise(exerciseId: number, section: RecentSection): RecentExerciseItem[] {
  const now = Date.now();
  const current = loadRecentExercises();
  const next = [
    { id: exerciseId, section, ts: now },
    ...current.filter((item) => !(item.id === exerciseId && item.section === section)),
  ].slice(0, RECENT_MAX_GLOBAL);
  saveRecentExercises(next);
  return next;
}

function clearRecentSection(section: RecentSection): RecentExerciseItem[] {
  const current = loadRecentExercises();
  const next = current.filter((item) => item.section !== section);
  saveRecentExercises(next);
  return next;
}

// ════════════════════════════════════════════════════════════
// CONSTANTS
// ════════════════════════════════════════════════════════════

const PATTERN_TABS: { value: string | null; label: string }[] = [
  { value: null, label: "Tutti" },
  { value: "squat", label: "Squat" },
  { value: "hinge", label: "Hinge" },
  { value: "push_h", label: "Push O." },
  { value: "push_v", label: "Push V." },
  { value: "pull_h", label: "Pull O." },
  { value: "pull_v", label: "Pull V." },
  { value: "core", label: "Core" },
  { value: "carry", label: "Carry" },
];

const EQUIPMENT_TABS: { value: string | null; label: string }[] = [
  { value: null, label: "Tutti" },
  { value: "corpo_libero", label: "Corpo libero" },
  { value: "bilanciere", label: "Bilanciere" },
  { value: "manubri", label: "Manubri" },
  { value: "kettlebell", label: "Kettlebell" },
  { value: "cavi", label: "Cavi" },
  { value: "macchina", label: "Macchina" },
  { value: "trx", label: "TRX" },
  { value: "elastici", label: "Elastici" },
];

const PRINCIPALE_CATEGORIES = new Set(["compound", "isolation", "bodyweight", "cardio"]);
const RELATION_LABELS: Record<string, string> = { regression: "Regressione", variation: "Variante", progression: "Progressione" };

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface ExerciseSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (exercise: Exercise) => void;
  patternHint?: string;
  categoryFilter?: string[];
  safetyMap?: Record<number, ExerciseSafetyEntry>;
  schedaId?: number;
  usedExerciseIds?: Set<number>;
  feasibilityDetails?: Record<number, TSExerciseFeasibilityEntry>;
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════

export function ExerciseSelector({
  open, onOpenChange, onSelect, patternHint, categoryFilter,
  safetyMap, schedaId, usedExerciseIds, feasibilityDetails,
}: ExerciseSelectorProps) {
  const [rawSearch, setRawSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);
  const [selectedEquipment, setSelectedEquipment] = useState<string | null>(null);
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);
  const [recentStore, setRecentStore] = useState<RecentExerciseItem[]>(loadRecentExercises);

  const handleSearchChange = useCallback((value: string) => {
    setRawSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(value), 200);
  }, []);

  useEffect(() => {
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, []);

  const { data } = useExercises();
  const exercises = useMemo(() => data?.items ?? [], [data]);
  const recentSection = useMemo(() => resolveRecentSection(categoryFilter), [categoryFilter]);
  const exerciseMap = useMemo(() => new Map(exercises.map((e) => [e.id, e])), [exercises]);

  const isPrincipale = !categoryFilter || categoryFilter.length === 0 ||
    categoryFilter.some((c) => PRINCIPALE_CATEGORIES.has(c));

  const sectionPool = useMemo(() => {
    if (categoryFilter && categoryFilter.length > 0) {
      return exercises.filter((e) => categoryFilter.includes(e.categoria));
    }
    return exercises;
  }, [exercises, categoryFilter]);

  // ── Filtering ──
  const filtered = useMemo(() => {
    const q = debouncedSearch.trim().toLowerCase();
    const result = sectionPool.filter((e) => {
      if (selectedPattern && e.pattern_movimento !== selectedPattern) return false;
      if (selectedEquipment && e.attrezzatura !== selectedEquipment) return false;
      if (q) {
        const matches =
          e.nome.toLowerCase().includes(q) ||
          e.categoria.toLowerCase().includes(q) ||
          e.attrezzatura.toLowerCase().includes(q) ||
          (EQUIPMENT_LABELS[e.attrezzatura] ?? "").toLowerCase().includes(q) ||
          e.muscoli_primari.some((m) => m.toLowerCase().includes(q)) ||
          e.muscoli_primari.some((m) => (MUSCLE_LABELS[m] ?? "").toLowerCase().includes(q));
        if (!matches) return false;
      }
      return true;
    });
    if (patternHint && !selectedPattern) {
      const hinted: Exercise[] = [];
      const rest: Exercise[] = [];
      for (const e of result) (e.pattern_movimento === patternHint ? hinted : rest).push(e);
      return [...hinted, ...rest];
    }
    return result;
  }, [sectionPool, debouncedSearch, patternHint, selectedPattern, selectedEquipment]);

  const recentExercises = useMemo(() => {
    const allowedIds = new Set(sectionPool.map((e) => e.id));
    const ids = recentStore
      .filter((item) => item.section === recentSection)
      .sort((a, b) => b.ts - a.ts)
      .map((item) => item.id);
    return Array.from(new Set(ids)).slice(0, RECENT_MAX_PER_SECTION)
      .filter((id) => allowedIds.has(id))
      .map((id) => exerciseMap.get(id))
      .filter((ex): ex is Exercise => ex !== undefined);
  }, [recentStore, recentSection, sectionPool, exerciseMap]);

  const recentExerciseIds = useMemo(() => new Set(recentExercises.map((e) => e.id)), [recentExercises]);
  const hasActiveFilters = !!selectedPattern || !!selectedEquipment || !!rawSearch;
  const showRecent = recentExercises.length > 0 && !hasActiveFilters;
  const visibleFiltered = useMemo(() => {
    if (!showRecent) return filtered;
    return filtered.filter((e) => !recentExerciseIds.has(e.id));
  }, [filtered, showRecent, recentExerciseIds]);

  // ── Handlers ──
  const resetFilters = useCallback(() => {
    setRawSearch(""); setDebouncedSearch("");
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setSelectedPattern(null); setSelectedEquipment(null);
    setSelectedExercise(null);
  }, []);

  const handleSelect = useCallback((exercise: Exercise) => {
    setRecentStore(pushRecentExercise(exercise.id, recentSection));
    onSelect(exercise);
    onOpenChange(false);
    resetFilters();
  }, [recentSection, onSelect, onOpenChange, resetFilters]);

  const handleSelectById = useCallback((exerciseId: number) => {
    const ex = exerciseMap.get(exerciseId);
    if (ex) handleSelect(ex);
  }, [exerciseMap, handleSelect]);

  const handleClearRecent = useCallback(() => {
    setRecentStore(clearRecentSection(recentSection));
  }, [recentSection]);

  const sectionLabel = categoryFilter?.includes("avviamento")
    ? "Avviamento" : categoryFilter?.includes("stretching") ? "Stretching & Mobilita" : null;

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) resetFilters(); }}>
      <DialogContent className="sm:max-w-[1100px] h-[85vh] p-0 flex flex-col overflow-hidden">
        {/* ── Header ── */}
        <DialogHeader className="px-5 pt-4 pb-0 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10">
              <Dumbbell className="h-4.5 w-4.5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-base">
                {sectionLabel ? `Seleziona ${sectionLabel}` : "Seleziona Esercizio"}
              </DialogTitle>
            </div>
            <span className="text-xs text-muted-foreground tabular-nums">{filtered.length} esercizi</span>
            {usedExerciseIds && usedExerciseIds.size > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary tabular-nums">
                {usedExerciseIds.size} in scheda
              </span>
            )}
          </div>
        </DialogHeader>

        {/* ── Search bar ── */}
        <div className="px-5 py-3 shrink-0">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
            <Input
              placeholder="Cerca per nome, muscolo, attrezzatura..."
              value={rawSearch}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10 h-10 rounded-xl bg-muted/40 border-0 focus-visible:ring-1 focus-visible:ring-primary/30"
              autoFocus
            />
            {rawSearch && (
              <button onClick={() => handleSearchChange("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        {/* ── Tab filters (pattern + equipment) ── */}
        {isPrincipale && (
          <div className="px-5 pb-2 shrink-0 space-y-1.5">
            {/* Pattern tabs */}
            <div className="flex gap-1 overflow-x-auto">
              {PATTERN_TABS.map((tab) => (
                <button
                  key={tab.value ?? "all"}
                  onClick={() => setSelectedPattern(tab.value)}
                  className={`shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                    selectedPattern === tab.value
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            {/* Equipment tabs */}
            <div className="flex gap-1 overflow-x-auto">
              {EQUIPMENT_TABS.map((tab) => (
                <button
                  key={tab.value ?? "all-eq"}
                  onClick={() => setSelectedEquipment(tab.value)}
                  className={`shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                    selectedEquipment === tab.value
                      ? "bg-muted text-foreground shadow-sm ring-1 ring-border/50"
                      : "text-muted-foreground/60 hover:bg-muted/40 hover:text-foreground"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Split body ── */}
        <div className="flex-1 flex min-h-0 border-t">
          {/* ── Left panel: exercise list (60%) ── */}
          <div className="w-full md:w-[60%] flex flex-col min-h-0">
            {/* Column header */}
            <div className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b bg-background/95 backdrop-blur-sm px-5 py-2">
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Esercizio</span>
              <div className="flex gap-3 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                <span className="w-16 text-center">Pattern</span>
                <span className="w-14 text-center">Diff.</span>
              </div>
            </div>

            <ScrollArea className="flex-1">
              {visibleFiltered.length === 0 && !showRecent ? (
                <div className="flex flex-col items-center justify-center py-16 gap-2">
                  <Dumbbell className="h-8 w-8 text-muted-foreground/20" />
                  <p className="text-sm text-muted-foreground">Nessun esercizio trovato</p>
                  {hasActiveFilters && (
                    <button onClick={resetFilters} className="text-xs text-primary hover:underline">Resetta filtri</button>
                  )}
                </div>
              ) : (
                <div>
                  {/* Recent section */}
                  {showRecent && (
                    <div className="border-b">
                      <div className="flex items-center justify-between px-5 py-1.5">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-primary">Recenti</span>
                        <button onClick={handleClearRecent} className="text-[10px] text-muted-foreground hover:text-foreground">Pulisci</button>
                      </div>
                      {recentExercises.map((exercise) => (
                        <ExerciseListRow
                          key={`r-${exercise.id}`}
                          exercise={exercise}
                          safety={safetyMap?.[exercise.id]}
                          isUsed={usedExerciseIds?.has(exercise.id)}
                          isSelected={selectedExercise?.id === exercise.id}
                          feasibility={feasibilityDetails?.[exercise.id]}
                          onClickRow={() => setSelectedExercise(exercise)}
                          onDoubleClick={() => handleSelect(exercise)}
                        />
                      ))}
                    </div>
                  )}

                  {/* All exercises */}
                  {visibleFiltered.map((exercise) => (
                    <ExerciseListRow
                      key={exercise.id}
                      exercise={exercise}
                      safety={safetyMap?.[exercise.id]}
                      isUsed={usedExerciseIds?.has(exercise.id)}
                      isSelected={selectedExercise?.id === exercise.id}
                      feasibility={feasibilityDetails?.[exercise.id]}
                      onClickRow={() => setSelectedExercise(exercise)}
                      onDoubleClick={() => handleSelect(exercise)}
                    />
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* ── Right panel: detail (40%) ── */}
          <div className="hidden md:flex md:w-[40%] md:flex-col md:border-l min-h-0">
            {selectedExercise ? (
              <ExerciseDetailSide
                exercise={selectedExercise}
                safety={safetyMap?.[selectedExercise.id]}
                safetyEntries={safetyMap}
                exerciseMap={exerciseMap}
                schedaId={schedaId}
                isUsed={usedExerciseIds?.has(selectedExercise.id)}
                feasibility={feasibilityDetails?.[selectedExercise.id]}
                onSelect={() => handleSelect(selectedExercise)}
                onSelectById={handleSelectById}
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
                <div className="h-16 w-16 rounded-2xl bg-muted/30 flex items-center justify-center mb-4">
                  <Target className="h-7 w-7 text-muted-foreground/30" />
                </div>
                <p className="text-sm font-medium text-muted-foreground/60">Seleziona un esercizio dalla lista</p>
                <p className="text-xs text-muted-foreground/40 mt-1">Clicca per vedere i dettagli, doppio click per selezionare</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ════════════════════════════════════════════════════════════
// EXERCISE LIST ROW — compact tabular row (like FoodRow)
// ════════════════════════════════════════════════════════════

const ExerciseListRow = memo(function ExerciseListRow({
  exercise, safety, isUsed, isSelected, feasibility, onClickRow, onDoubleClick,
}: {
  exercise: Exercise;
  safety?: ExerciseSafetyEntry;
  isUsed?: boolean;
  isSelected?: boolean;
  feasibility?: TSExerciseFeasibilityEntry;
  onClickRow: () => void;
  onDoubleClick: () => void;
}) {
  const safetyBg = safety?.severity === "avoid"
    ? "bg-red-50/40 dark:bg-red-950/10"
    : safety?.severity === "caution"
      ? "bg-amber-50/40 dark:bg-amber-950/10"
      : "";

  const DIFF_COLORS: Record<string, string> = {
    beginner: "text-emerald-600 dark:text-emerald-400",
    intermediate: "text-amber-600 dark:text-amber-400",
    advanced: "text-red-600 dark:text-red-400",
  };

  return (
    <button
      onClick={onClickRow}
      onDoubleClick={onDoubleClick}
      className={`w-full flex items-center justify-between gap-3 px-5 py-2.5 text-left transition-colors cursor-pointer border-l-2 ${
        isSelected
          ? "bg-primary/5 dark:bg-primary/10 border-l-primary"
          : `border-l-transparent hover:bg-muted/40 ${safetyBg}`
      }`}
    >
      {/* Left: name + badges */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          {safety && (
            <span className={`shrink-0 ${safety.severity === "avoid" ? "text-red-500" : safety.severity === "caution" ? "text-amber-500" : "text-blue-500"}`}>
              {safety.severity === "avoid" ? <ShieldAlert className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
            </span>
          )}
          <span className="text-[13px] font-medium truncate">{exercise.nome}</span>
          {isUsed && (
            <span className="shrink-0 text-[9px] font-medium text-primary bg-primary/10 px-1.5 py-0.5 rounded-full">In scheda</span>
          )}
          {feasibility && (
            <span className={`shrink-0 text-[9px] font-medium px-1.5 py-0.5 rounded-full ${
              feasibility.verdict === "infeasible_for_auto_draft"
                ? "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-400"
                : "bg-violet-100 text-violet-700 dark:bg-violet-950/50 dark:text-violet-400"
            }`}>
              {feasibility.verdict === "infeasible_for_auto_draft" ? "Escluso" : "Scoraggiato"}
            </span>
          )}
        </div>
        {/* Muscles inline */}
        <div className="flex gap-0.5 mt-0.5">
          {exercise.muscoli_primari.slice(0, 3).map((m) => (
            <span key={m} className={`text-[8px] font-semibold rounded px-1 py-px uppercase tracking-wide ${MUSCLE_COLORS[m] ?? "bg-muted/30 text-muted-foreground/60"}`}>
              {MUSCLE_LABELS[m] ?? m}
            </span>
          ))}
        </div>
      </div>

      {/* Right: pattern + difficulty */}
      <div className="flex gap-3 shrink-0">
        <span className="w-16 text-center text-[11px] text-muted-foreground truncate">
          {exercise.pattern_movimento ? exercise.pattern_movimento.replace("_", " ") : "—"}
        </span>
        <span className={`w-14 text-center text-[11px] font-medium ${DIFF_COLORS[exercise.difficolta] ?? "text-muted-foreground"}`}>
          {DIFFICULTY_LABELS[exercise.difficolta] ?? exercise.difficolta}
        </span>
      </div>
    </button>
  );
});

// ════════════════════════════════════════════════════════════
// EXERCISE DETAIL SIDE PANEL
// ════════════════════════════════════════════════════════════

function ExerciseDetailSide({
  exercise, safety, safetyEntries, exerciseMap, schedaId,
  isUsed, feasibility, onSelect, onSelectById,
}: {
  exercise: Exercise;
  safety?: ExerciseSafetyEntry;
  safetyEntries?: Record<number, ExerciseSafetyEntry>;
  exerciseMap: Map<number, Exercise>;
  schedaId?: number;
  isUsed?: boolean;
  feasibility?: TSExerciseFeasibilityEntry;
  onSelect: () => void;
  onSelectById: (id: number) => void;
}) {
  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1">
        <div className="p-5 space-y-4">
          {/* Identity */}
          <div>
            <h3 className="text-base font-bold tracking-tight">{exercise.nome}</h3>
            {exercise.nome_en && (
              <p className="text-xs text-muted-foreground/50 italic">{exercise.nome_en}</p>
            )}
            <div className="flex flex-wrap gap-1.5 mt-2">
              <Badge variant="outline" className="text-[10px]">{exercise.categoria}</Badge>
              <Badge variant="outline" className="text-[10px]">{EQUIPMENT_LABELS[exercise.attrezzatura] ?? exercise.attrezzatura}</Badge>
              <Badge variant="outline" className="text-[10px]">{DIFFICULTY_LABELS[exercise.difficolta] ?? exercise.difficolta}</Badge>
              {exercise.force_type && <Badge variant="outline" className="text-[10px]">{FORCE_TYPE_LABELS[exercise.force_type] ?? exercise.force_type}</Badge>}
              {exercise.lateral_pattern && <Badge variant="outline" className="text-[10px]">{LATERAL_PATTERN_LABELS[exercise.lateral_pattern] ?? exercise.lateral_pattern}</Badge>}
            </div>
          </div>

          {/* Muscles */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Muscoli primari</p>
            <div className="flex flex-wrap gap-1">
              {exercise.muscoli_primari.map((m) => (
                <span key={m} className={`text-[10px] font-semibold rounded-full px-2 py-0.5 ${MUSCLE_COLORS[m] ?? "bg-muted/40 text-muted-foreground/70"}`}>
                  {MUSCLE_LABELS[m] ?? m}
                </span>
              ))}
            </div>
            {exercise.muscoli_secondari && exercise.muscoli_secondari.length > 0 && (
              <>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mt-2 mb-1">Secondari</p>
                <div className="flex flex-wrap gap-1">
                  {exercise.muscoli_secondari.map((m) => (
                    <span key={m} className="text-[10px] rounded-full px-2 py-0.5 bg-muted/30 text-muted-foreground/60">
                      {MUSCLE_LABELS[m] ?? m}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Safety */}
          {safety && (
            <div className={`rounded-lg p-3 ${
              safety.severity === "avoid"
                ? "bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900"
                : safety.severity === "caution"
                  ? "bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900"
                  : "bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900"
            }`}>
              <p className={`text-[10px] font-bold uppercase tracking-wider mb-1.5 ${
                safety.severity === "avoid" ? "text-red-600 dark:text-red-400"
                  : safety.severity === "caution" ? "text-amber-600 dark:text-amber-400"
                    : "text-blue-600 dark:text-blue-400"
              }`}>
                {safety.severity === "avoid" ? "Controindicato" : safety.severity === "caution" ? "Cautela" : "Adattare"}
              </p>
              {safety.conditions.map((cond) => (
                <div key={cond.id} className="mb-1.5 last:mb-0">
                  <p className="text-xs font-medium">{cond.nome}</p>
                  {cond.nota && <p className="text-[11px] text-muted-foreground leading-relaxed">{cond.nota}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Safe alternatives */}
          <SafeAlternatives
            exerciseId={exercise.id}
            sourceExercise={exercise}
            safetyEntries={safetyEntries}
            exerciseMap={exerciseMap}
            onSelectById={onSelectById}
          />

          {/* Biomechanics detail */}
          <ExerciseDetailPanel
            exercise={exercise}
            exerciseId={exercise.id}
            safety={safety}
            safetyEntries={safetyEntries}
            exerciseMap={exerciseMap}
            schedaId={schedaId}
            onQuickReplace={onSelectById}
          />
        </div>
      </ScrollArea>

      {/* CTA pinned bottom */}
      <div className="p-4 border-t bg-background/95 backdrop-blur-sm shrink-0">
        <Button
          onClick={onSelect}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
        >
          <Dumbbell className="h-4 w-4 mr-2" />
          {isUsed ? "Aggiungi di nuovo" : "Seleziona esercizio"}
        </Button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SAFE ALTERNATIVES (from exercise relations)
// ════════════════════════════════════════════════════════════

function SafeAlternatives({
  exerciseId, sourceExercise, safetyEntries, exerciseMap, onSelectById,
}: {
  exerciseId: number;
  sourceExercise: Exercise;
  safetyEntries?: Record<number, ExerciseSafetyEntry>;
  exerciseMap: Map<number, Exercise>;
  onSelectById: (id: number) => void;
}) {
  const { data: relations } = useExerciseRelations(exerciseId);

  const alternatives = useMemo(() => {
    if (!relations) return [];
    return relations
      .filter((rel) => {
        if (!safetyEntries) return true;
        const entry = safetyEntries[rel.related_exercise_id];
        return !entry || entry.severity !== "avoid";
      })
      .map((rel) => {
        const entry = safetyEntries?.[rel.related_exercise_id];
        const hasCaution = entry?.severity === "caution";
        const candidate = exerciseMap.get(rel.related_exercise_id);
        return {
          id: rel.related_exercise_id,
          nome: rel.related_exercise_nome,
          tipo: rel.tipo_relazione,
          hasCaution,
          score: getReplacementScore(sourceExercise, candidate, rel.tipo_relazione, hasCaution),
          reason: getReplacementReason(sourceExercise, candidate, rel.tipo_relazione, hasCaution),
        };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);
  }, [relations, safetyEntries, sourceExercise, exerciseMap]);

  if (alternatives.length === 0) return null;

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <ArrowRightLeft className="h-3 w-3 text-primary" />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-primary">Alternative</span>
      </div>
      <div className="space-y-1">
        {alternatives.map((alt) => (
          <div key={`${alt.id}-${alt.tipo}`} className="flex items-center gap-2 text-[11px] rounded-md px-2 py-1.5 hover:bg-muted/30 transition-colors">
            <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
            <div className="min-w-0 flex-1">
              <span className="font-medium truncate block">{alt.nome}</span>
              <span className="text-[9px] text-muted-foreground">{RELATION_LABELS[alt.tipo] ?? alt.tipo} · {alt.reason}</span>
            </div>
            {alt.hasCaution && <span className="text-[9px] text-amber-500 shrink-0">Cautela</span>}
            <Button
              variant="ghost" size="sm"
              className="h-5 px-1.5 text-[10px] text-primary shrink-0"
              onClick={() => onSelectById(alt.id)}
            >
              <RefreshCw className="h-2.5 w-2.5 mr-0.5" />
              Usa
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
