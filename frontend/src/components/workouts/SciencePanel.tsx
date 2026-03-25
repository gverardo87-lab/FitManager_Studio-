// src/components/workouts/SciencePanel.tsx
"use client";

/**
 * Pannello laterale scienza — visibile nel builder full-screen (ADR-008).
 *
 * Mostra in tempo reale (debounce 1s su modifiche sessioni):
 * 1. Safety: condizioni, farmaci, count severity
 * 2. Score: punteggio 0-100 con 4 barre (volume, balance, frequenza, recovery)
 * 3. Copertura muscolare: lista muscoli con stato
 * 4. Equilibrio: 5 rapporti biomeccanici
 * 5. Azioni: prioritizzate per urgenza
 *
 * Consuma lo stesso backend della ScientificAnalysisTab (POST /training-science/analyze).
 */

import { useMemo, useEffect, useRef, useState } from "react";
import {
  Shield, Activity, Loader2, ChevronDown,
  AlertTriangle, CheckCircle2, XCircle, Pill,
} from "lucide-react";
import { useAnalyzePlan } from "@/hooks/useTrainingScience";
import { VALID_PATTERNS } from "@/lib/training-science-display";
import type {
  Exercise,
  ExerciseSafetyEntry,
  SafetyMapResponse,
  SafetyConditionDetail,
  TSTemplatePiano,
  TSAnalisiPiano,
  TSObjective,
  TSLevel,
  TSPattern,
  TSDettaglioMuscolo,
  TSDettaglioRapporto,
} from "@/types/api";
import type { SessionCardData } from "./SessionCard";

// ════════════════════════════════════════════════════════════
// PROPS
// ════════════════════════════════════════════════════════════

interface SciencePanelProps {
  sessions: SessionCardData[];
  exerciseMap: Map<number, Exercise>;
  livello: string;
  obiettivo: string;
  sessioniPerSettimana: number;
  safetyMap: SafetyMapResponse | undefined;
  safetyEntries: Record<string, { severity: string; conditions: SafetyConditionDetail[] }> | undefined;
  clientSesso?: string | null;
  clientDataNascita?: string | null;
}

// ════════════════════════════════════════════════════════════
// BRIDGE (shared with ScientificAnalysisTab)
// ════════════════════════════════════════════════════════════

const LIVELLO_MAP: Record<string, TSLevel> = {
  beginner: "principiante", principiante: "principiante",
  intermedio: "intermedio", avanzato: "avanzato",
};

const VALID_OBIETTIVI = new Set<TSObjective>([
  "forza", "ipertrofia", "resistenza", "dimagrimento", "tonificazione",
]);

function computeAge(d: string | null | undefined): number | null {
  if (!d) return null;
  const birth = new Date(d);
  if (isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age >= 10 && age <= 100 ? age : null;
}

function buildPiano(
  sessions: SessionCardData[],
  exerciseMap: Map<number, Exercise>,
  livello: string, obiettivo: string, freq: number,
  sesso?: string | null, dataNascita?: string | null,
): TSTemplatePiano | null {
  const sessioni = sessions.map((s) => {
    const allEx = [...s.esercizi, ...s.blocchi.flatMap((b) => b.esercizi)];
    const slots = allEx
      .map((e) => {
        const ex = exerciseMap.get(e.id_esercizio);
        if (!ex) return null;
        const pattern = ex.pattern_movimento as TSPattern;
        if (!VALID_PATTERNS.has(pattern)) return null;
        return {
          pattern, priorita: 2 as const, serie: e.serie,
          rep_min: 8, rep_max: 12, riposo_sec: 90,
          muscolo_target: null, note: "", carico_kg: e.carico_kg ?? null,
        };
      })
      .filter((s): s is NonNullable<typeof s> => s !== null);
    return { nome: s.nome_sessione, ruolo: "full_body" as const, focus: "", slots };
  });

  if (!sessioni.some((s) => s.slots.length > 0)) return null;

  return {
    frequenza: Math.max(2, Math.min(6, freq)),
    obiettivo: VALID_OBIETTIVI.has(obiettivo as TSObjective) ? (obiettivo as TSObjective) : "ipertrofia",
    livello: LIVELLO_MAP[livello] ?? "intermedio",
    tipo_split: "full_body", sessioni,
    note_generazione: [], sesso: sesso || null, eta: computeAge(dataNascita),
  };
}

// ════════════════════════════════════════════════════════════
// MUSCLE DISPLAY NAME
// ════════════════════════════════════════════════════════════

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto", dorsali: "Dorsali", delt_ant: "Delt. Ant.",
  delt_lat: "Delt. Lat.", delt_post: "Delt. Post.",
  bicipiti: "Bicipiti", tricipiti: "Tricipiti",
  quadricipiti: "Quadricipiti", femorali: "Femorali",
  glutei: "Glutei", polpacci: "Polpacci", trapezio: "Trapezio",
  core: "Core", avambracci: "Avambracci", adduttori: "Adduttori",
};

// ════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════

export function SciencePanel({
  sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana,
  safetyMap, safetyEntries, clientSesso, clientDataNascita,
}: SciencePanelProps) {
  const analyzeMutation = useAnalyzePlan();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Bridge sessions → backend format
  const templatePiano = useMemo(
    () => buildPiano(sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana, clientSesso, clientDataNascita),
    [sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana, clientSesso, clientDataNascita],
  );

  // Fingerprint for debounce
  const fingerprint = useMemo(() => {
    if (!templatePiano) return "";
    const slotsKey = templatePiano.sessioni.map((s) =>
      s.slots.map((sl) => `${sl.pattern}:${sl.serie}:${sl.carico_kg ?? ""}`).join(","),
    ).join("|");
    return `${slotsKey}|${templatePiano.sesso ?? ""}|${templatePiano.eta ?? ""}`;
  }, [templatePiano]);

  // Auto-analyze with debounce
  useEffect(() => {
    if (!templatePiano || !fingerprint) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      analyzeMutation.mutate(templatePiano);
    }, 1000);
    return () => clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fingerprint]);

  const analysis = analyzeMutation.data ?? null;

  // Safety stats
  const { avoidCount, cautionCount, modifyCount } = useMemo(() => {
    if (!safetyEntries) return { avoidCount: 0, cautionCount: 0, modifyCount: 0 };
    const planExIds = new Set<number>();
    for (const s of sessions) {
      for (const e of s.esercizi) planExIds.add(e.id_esercizio);
      for (const b of s.blocchi) for (const e of b.esercizi) planExIds.add(e.id_esercizio);
    }
    let avoid = 0, caution = 0, modify = 0;
    for (const [exId, entry] of Object.entries(safetyEntries)) {
      if (!planExIds.has(Number(exId))) continue;
      if (entry.severity === "avoid") avoid++;
      else if (entry.severity === "caution") caution++;
      else modify++;
    }
    return { avoidCount: avoid, cautionCount: caution, modifyCount: modify };
  }, [safetyEntries, sessions]);

  const hasExercises = sessions.some(s => s.esercizi.length > 0 || s.blocchi.some(b => b.esercizi.length > 0));

  return (
    <div className="hidden lg:flex lg:w-80 lg:flex-col lg:border-l lg:bg-muted/20 dark:lg:bg-muted/10 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b bg-background/80">
        <Activity className="h-4 w-4 text-primary" />
        <span className="text-sm font-semibold">Analisi Live</span>
        {analysis && <ScorePill score={analysis.score} />}
        {analyzeMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground ml-auto" />}
      </div>

      <div className="flex-1 overflow-y-auto">
        {!hasExercises ? (
          <div className="px-4 py-8 text-center text-xs text-muted-foreground">
            Aggiungi esercizi per attivare l&apos;analisi.
          </div>
        ) : (
          <div className="divide-y">
            {/* 1. SAFETY */}
            {safetyMap && safetyMap.condition_count > 0 && (
              <PanelSection title="Safety" icon={Shield} defaultOpen={avoidCount > 0}
                badge={avoidCount > 0 ? `${avoidCount} evitare` : `${safetyMap.condition_count} cond.`}
                badgeColor={avoidCount > 0 ? "red" : "amber"}>
                <div className="space-y-2">
                  {safetyMap.condition_names.map((name) => (
                    <div key={name} className="text-xs text-muted-foreground flex items-start gap-1.5">
                      <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                      {name}
                    </div>
                  ))}
                  {avoidCount > 0 && (
                    <div className="text-xs font-medium text-red-600 dark:text-red-400 mt-1">
                      {avoidCount} esercizi da evitare nella scheda
                    </div>
                  )}
                  {cautionCount > 0 && (
                    <div className="text-xs text-amber-600 dark:text-amber-400">
                      {cautionCount} con cautela
                    </div>
                  )}
                  {modifyCount > 0 && (
                    <div className="text-xs text-blue-600 dark:text-blue-400">
                      {modifyCount} da adattare
                    </div>
                  )}
                  {safetyMap.medication_flags.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {safetyMap.medication_flags.map((f) => (
                        <div key={f.flag} className="text-xs flex items-start gap-1.5 text-violet-600 dark:text-violet-400">
                          <Pill className="h-3 w-3 mt-0.5 shrink-0" />
                          {f.nota}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </PanelSection>
            )}

            {/* 2. SCORE */}
            {analysis && (
              <PanelSection title="Score" icon={Activity} defaultOpen badge={`${Math.round(analysis.score)}/100`}
                badgeColor={analysis.score >= 75 ? "green" : analysis.score >= 50 ? "amber" : "red"}>
                <div className="space-y-2.5">
                  <ScoreBar label="Volume" value={computeSubScore(analysis, "volume")} />
                  <ScoreBar label="Equilibrio" value={computeSubScore(analysis, "balance")} />
                  <ScoreBar label="Frequenza" value={computeSubScore(analysis, "frequency")} />
                  <ScoreBar label="Recupero" value={computeSubScore(analysis, "recovery")} />
                </div>
              </PanelSection>
            )}

            {/* 3. COPERTURA MUSCOLARE */}
            {analysis && (
              <PanelSection title="Muscoli" icon={Activity} defaultOpen={false}
                badge={`${analysis.volume.muscoli_sotto_mev.length} deficit`}
                badgeColor={analysis.volume.muscoli_sotto_mev.length > 0 ? "amber" : "green"}>
                <div className="space-y-1">
                  {analysis.dettaglio_muscoli.map((m) => (
                    <MuscleRow key={m.muscolo} muscle={m} />
                  ))}
                </div>
              </PanelSection>
            )}

            {/* 4. EQUILIBRIO BIOMECCANICO */}
            {analysis && analysis.dettaglio_rapporti.length > 0 && (
              <PanelSection title="Equilibrio" icon={Activity} defaultOpen={false}
                badge={`${analysis.dettaglio_rapporti.filter(r => !r.in_tolleranza).length} squilibri`}
                badgeColor={analysis.dettaglio_rapporti.some(r => !r.in_tolleranza) ? "amber" : "green"}>
                <div className="space-y-1.5">
                  {analysis.dettaglio_rapporti.map((r) => (
                    <RatioRow key={r.nome} ratio={r} />
                  ))}
                </div>
              </PanelSection>
            )}

            {/* 5. AZIONI */}
            {analysis && (
              <PanelSection title="Azioni" icon={AlertTriangle} defaultOpen={analysis.warnings.length > 0}
                badge={analysis.warnings.length > 0 ? `${analysis.warnings.length}` : "0"}
                badgeColor={analysis.warnings.length > 0 ? "amber" : "green"}>
                {analysis.warnings.length === 0 ? (
                  <div className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Nessuna azione necessaria
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {analysis.warnings.map((w, i) => (
                      <div key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                        <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0 text-amber-500" />
                        {w}
                      </div>
                    ))}
                  </div>
                )}
              </PanelSection>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ════════════════════════════════════════════════════════════

function PanelSection({
  title, icon: Icon, defaultOpen = false, badge, badgeColor, children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  defaultOpen?: boolean;
  badge?: string;
  badgeColor?: "green" | "amber" | "red";
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const colorMap = {
    green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
    amber: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400",
    red: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
  };

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:bg-muted/40 transition-colors"
      >
        <Icon className="h-3.5 w-3.5" />
        {title}
        {badge && badgeColor && (
          <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full ${colorMap[badgeColor]}`}>
            {badge}
          </span>
        )}
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""} ${badge ? "" : "ml-auto"}`} />
      </button>
      {open && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}

function ScorePill({ score }: { score: number }) {
  const color = score >= 75
    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400"
    : score >= 50
      ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400"
      : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400";
  return (
    <span className={`ml-auto text-[11px] font-bold px-2 py-0.5 rounded-full tabular-nums ${color}`}>
      {Math.round(score)}
    </span>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  const color = pct >= 75 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] mb-0.5">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold tabular-nums">{Math.round(pct)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

const STATO_ICON: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string }> = {
  ottimale: { icon: CheckCircle2, color: "text-emerald-500" },
  sopra_mav: { icon: AlertTriangle, color: "text-amber-500" },
  mev_mav: { icon: Activity, color: "text-blue-500" },
  sotto_mev: { icon: XCircle, color: "text-red-500" },
  sopra_mrv: { icon: XCircle, color: "text-red-600" },
};

function MuscleRow({ muscle }: { muscle: TSDettaglioMuscolo }) {
  const s = STATO_ICON[muscle.stato] ?? STATO_ICON.sotto_mev;
  const StatusIcon = s.icon;
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <StatusIcon className={`h-3 w-3 shrink-0 ${s.color}`} />
      <span className="flex-1 truncate">{MUSCLE_LABELS[muscle.muscolo] ?? muscle.muscolo}</span>
      <span className="tabular-nums text-muted-foreground">{muscle.serie_effettive.toFixed(1)}</span>
    </div>
  );
}

function RatioRow({ ratio }: { ratio: TSDettaglioRapporto }) {
  const ok = ratio.in_tolleranza;
  return (
    <div className="flex items-center gap-2 text-[11px]">
      {ok ? (
        <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
      ) : (
        <AlertTriangle className="h-3 w-3 shrink-0 text-amber-500" />
      )}
      <span className="flex-1 truncate">{ratio.nome}</span>
      <span className={`tabular-nums font-medium ${ok ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}`}>
        {ratio.valore.toFixed(2)}
      </span>
      <span className="text-muted-foreground/60">/ {ratio.target.toFixed(2)}</span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SCORE DECOMPOSITION
// ════════════════════════════════════════════════════════════

/**
 * Estimate sub-scores from analysis data.
 * The backend computes a composite score but doesn't expose sub-scores directly.
 * We approximate from the data we have.
 */
function computeSubScore(analysis: TSAnalisiPiano, dimension: "volume" | "balance" | "frequency" | "recovery"): number {
  switch (dimension) {
    case "volume": {
      // Max 40pts. Based on muscle coverage status.
      const muscles = analysis.dettaglio_muscoli;
      if (muscles.length === 0) return 0;
      const weights: Record<string, number> = { ottimale: 1, sopra_mav: 0.8, mev_mav: 0.5, sotto_mev: 0, sopra_mrv: 0 };
      const total = muscles.reduce((sum, m) => sum + (weights[m.stato] ?? 0), 0);
      return (total / muscles.length) * 100;
    }
    case "balance": {
      // Max 25pts. Based on ratios in tolerance.
      const ratios = analysis.dettaglio_rapporti;
      if (ratios.length === 0) return 100;
      const balanced = ratios.filter((r) => r.in_tolleranza).length;
      return (balanced / ratios.length) * 100;
    }
    case "frequency": {
      // Max 20pts. Penalize for freq warnings.
      const freqWarnings = analysis.warnings.filter((w) => w.toLowerCase().includes("frequenza")).length;
      return Math.max(0, 100 - freqWarnings * 20);
    }
    case "recovery": {
      // Max 15pts. Penalize for recovery overlaps.
      const overlaps = analysis.recovery_overlaps.length;
      return Math.max(0, 100 - overlaps * 33);
    }
  }
}
