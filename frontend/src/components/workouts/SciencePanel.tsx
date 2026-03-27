// src/components/workouts/SciencePanel.tsx
"use client";

/**
 * Pannello laterale scienza — visibile nel builder full-screen (ADR-008).
 *
 * Layout verticale a gerarchia visiva:
 * 1. Score ring hero (sempre visibile, punteggio 0-100 con anello)
 * 2. 4 sub-score barre compatte
 * 3. Safety alert (se il cliente ha condizioni)
 * 4. Mappa anatomica muscolare (sempre visibile)
 * 5. Equilibrio rapporti (compatto)
 * 6. Azioni prioritarie (conteggio + lista)
 */

import { useMemo, useEffect, useRef, useState } from "react";
import {
  Shield, Loader2, ChevronDown, Scale,
  AlertTriangle, CheckCircle2, XCircle, Pill,
  Zap, Dumbbell, HelpCircle,
} from "lucide-react";
import { useAnalyzePlan } from "@/hooks/useTrainingScience";
import { VALID_PATTERNS } from "@/lib/training-science-display";
import type {
  Exercise,
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
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { AnatomicalMuscleMap } from "./AnatomicalMuscleMap";
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
// COMPONENT
// ════════════════════════════════════════════════════════════

export function SciencePanel({
  sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana,
  safetyMap, safetyEntries, clientSesso, clientDataNascita,
}: SciencePanelProps) {
  const analyzeMutation = useAnalyzePlan();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const templatePiano = useMemo(
    () => buildPiano(sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana, clientSesso, clientDataNascita),
    [sessions, exerciseMap, livello, obiettivo, sessioniPerSettimana, clientSesso, clientDataNascita],
  );

  const fingerprint = useMemo(() => {
    if (!templatePiano) return "";
    const slotsKey = templatePiano.sessioni.map((s) =>
      s.slots.map((sl) => `${sl.pattern}:${sl.serie}:${sl.carico_kg ?? ""}`).join(","),
    ).join("|");
    return `${slotsKey}|${templatePiano.sesso ?? ""}|${templatePiano.eta ?? ""}`;
  }, [templatePiano]);

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
    <div className="hidden lg:flex lg:w-80 lg:flex-col lg:border-l bg-background overflow-hidden">
      {/* ── Header ── */}
      <div className="flex items-center gap-2 px-4 py-3 border-b">
        <Dumbbell className="h-4 w-4 text-primary" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Analisi Live</span>
        {analyzeMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground ml-auto" />}
      </div>

      {/* ── Scrollable content ── */}
      <div className="flex-1 overflow-y-auto">
        {!hasExercises ? (
          <div className="px-4 py-12 text-center">
            <Dumbbell className="h-8 w-8 mx-auto text-muted-foreground/30 mb-3" />
            <p className="text-xs text-muted-foreground">Aggiungi esercizi per<br />attivare l&apos;analisi.</p>
          </div>
        ) : (
          <div className="space-y-0">

            {/* ═══ 1. SCORE RING HERO ═══ */}
            {analysis && (
              <div className="px-4 py-5 border-b">
                <div className="flex items-center justify-center">
                  <ScoreRing score={analysis.score} size={100} strokeWidth={8} />
                </div>
                <div className="mt-4 space-y-2">
                  <ScoreBar label="Volume" value={computeSubScore(analysis, "volume")} icon="vol" />
                  <ScoreBar label="Equilibrio" value={computeSubScore(analysis, "balance")} icon="bal" />
                  <ScoreBar label="Frequenza" value={computeSubScore(analysis, "frequency")} icon="frq" />
                  <ScoreBar label="Recupero" value={computeSubScore(analysis, "recovery")} icon="rec" />
                </div>
              </div>
            )}

            {/* ═══ 2. SAFETY ALERT ═══ */}
            {safetyMap && safetyMap.condition_count > 0 && (
              <div className="border-b">
                <CollapsibleSection
                  title="Safety"
                  icon={<Shield className="h-3.5 w-3.5" />}
                  badge={avoidCount > 0 ? `${avoidCount} evitare` : `${safetyMap.condition_count}`}
                  badgeVariant={avoidCount > 0 ? "destructive" : "warning"}
                  defaultOpen={avoidCount > 0}
                >
                  <div className="space-y-1.5">
                    {safetyMap.condition_names.map((name) => (
                      <div key={name} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                        {name}
                      </div>
                    ))}
                    {avoidCount > 0 && (
                      <p className="text-[11px] font-medium text-red-600 dark:text-red-400 pt-1">
                        {avoidCount} {avoidCount === 1 ? "esercizio" : "esercizi"} da evitare
                      </p>
                    )}
                    {cautionCount > 0 && (
                      <p className="text-[11px] text-amber-600 dark:text-amber-400">
                        {cautionCount} con cautela
                      </p>
                    )}
                    {modifyCount > 0 && (
                      <p className="text-[11px] text-blue-600 dark:text-blue-400">
                        {modifyCount} da adattare
                      </p>
                    )}
                    {safetyMap.medication_flags.length > 0 && (
                      <div className="pt-1.5 mt-1.5 border-t border-dashed space-y-1">
                        {safetyMap.medication_flags.map((f) => (
                          <div key={f.flag} className="text-[11px] flex items-start gap-1.5 text-violet-600 dark:text-violet-400">
                            <Pill className="h-3 w-3 mt-0.5 shrink-0" />
                            {f.nota}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CollapsibleSection>
              </div>
            )}

            {/* ═══ 3. MAPPA ANATOMICA (sempre visibile) ═══ */}
            {analysis && (
              <div className="px-4 py-3 border-b">
                <div className="flex items-center gap-2 mb-2">
                  <Dumbbell className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Copertura muscolare
                  </span>
                  {analysis.volume.muscoli_sotto_mev.length > 0 && (
                    <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400">
                      {analysis.volume.muscoli_sotto_mev.length} deficit
                    </span>
                  )}
                </div>
                <AnatomicalMuscleMap dettaglioMuscoli={analysis.dettaglio_muscoli} />
              </div>
            )}

            {/* ═══ 4. EQUILIBRIO BIOMECCANICO ═══ */}
            {analysis && analysis.dettaglio_rapporti.length > 0 && (
              <div className="border-b">
                <CollapsibleSection
                  title="Equilibrio"
                  icon={<Scale className="h-3.5 w-3.5" />}
                  badge={`${analysis.dettaglio_rapporti.filter(r => !r.in_tolleranza).length}`}
                  badgeVariant={analysis.dettaglio_rapporti.some(r => !r.in_tolleranza) ? "warning" : "success"}
                  defaultOpen={analysis.dettaglio_rapporti.some(r => !r.in_tolleranza)}
                >
                  <div className="space-y-1.5">
                    {analysis.dettaglio_rapporti.map((r) => (
                      <RatioRow key={r.nome} ratio={r} />
                    ))}
                  </div>
                </CollapsibleSection>
              </div>
            )}

            {/* ═══ 5. AZIONI PRIORITARIE ═══ */}
            {analysis && (
              <div className="border-b">
                <CollapsibleSection
                  title="Azioni"
                  icon={<Zap className="h-3.5 w-3.5" />}
                  badge={`${analysis.warnings.length}`}
                  badgeVariant={analysis.warnings.length > 0 ? "warning" : "success"}
                  defaultOpen={analysis.warnings.length > 3}
                >
                  {analysis.warnings.length === 0 ? (
                    <div className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Piano bilanciato
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {analysis.warnings.map((w, i) => (
                        <div key={i} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                          <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0 text-amber-500" />
                          {w}
                        </div>
                      ))}
                    </div>
                  )}
                </CollapsibleSection>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SCORE RING — circular progress hero
// ════════════════════════════════════════════════════════════

function ScoreRing({ score, size, strokeWidth }: { score: number; size: number; strokeWidth: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const offset = circumference - (progress / 100) * circumference;

  const color = score >= 75
    ? "stroke-emerald-500"
    : score >= 50
      ? "stroke-amber-500"
      : "stroke-red-500";

  const bgColor = score >= 75
    ? "text-emerald-600 dark:text-emerald-400"
    : score >= 50
      ? "text-amber-600 dark:text-amber-400"
      : "text-red-600 dark:text-red-400";

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background ring */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          className="stroke-muted"
          strokeWidth={strokeWidth}
        />
        {/* Progress ring */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          className={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease-in-out" }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-2xl font-bold tabular-nums ${bgColor}`}>
          {Math.round(score)}
        </span>
        <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-medium">
          score
        </span>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SCORE BAR — compact sub-score indicator
// ════════════════════════════════════════════════════════════

const BAR_ICONS: Record<string, string> = { vol: "V", bal: "E", frq: "F", rec: "R" };

const SCORE_HINTS: Record<string, string> = {
  vol: "Set totali per muscolo vs target settimanale (MEV-MAV-MRV)",
  bal: "Rapporto push/pull, anteriore/posteriore e quad/hamstring",
  frq: "Frequenza allenamento per muscolo rispetto all'ottimale",
  rec: "Tempo di recupero stimato tra sessioni per gruppo muscolare",
};

function ScoreBar({ label, value, icon }: { label: string; value: number; icon: string }) {
  const pct = Math.min(100, Math.max(0, value));
  const color = pct >= 75
    ? "bg-emerald-500"
    : pct >= 50
      ? "bg-amber-500"
      : "bg-red-500";
  const textColor = pct >= 75
    ? "text-emerald-600 dark:text-emerald-400"
    : pct >= 50
      ? "text-amber-600 dark:text-amber-400"
      : "text-red-600 dark:text-red-400";

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-bold text-muted-foreground/50 w-3 shrink-0">{BAR_ICONS[icon]}</span>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="text-[11px] text-muted-foreground w-16 shrink-0 cursor-help">{label}</span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs text-xs">{SCORE_HINTS[icon] ?? label}</TooltipContent>
      </Tooltip>
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%`, transition: "width 0.6s ease-in-out" }}
        />
      </div>
      <span className={`text-[11px] font-semibold tabular-nums w-6 text-right ${textColor}`}>
        {Math.round(pct)}
      </span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// COLLAPSIBLE SECTION
// ════════════════════════════════════════════════════════════

function CollapsibleSection({
  title, icon, badge, badgeVariant, defaultOpen = false, children,
}: {
  title: string;
  icon: React.ReactNode;
  badge?: string;
  badgeVariant?: "destructive" | "warning" | "success";
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  const badgeColors: Record<string, string> = {
    destructive: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
    warning: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400",
    success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
  };

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-muted-foreground hover:bg-muted/30 transition-colors"
      >
        <span className="text-muted-foreground/60">{icon}</span>
        <span className="text-[11px] font-semibold uppercase tracking-wider">{title}</span>
        {badge && badgeVariant && (
          <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full ${badgeColors[badgeVariant]}`}>
            {badge}
          </span>
        )}
        <ChevronDown className={`h-3 w-3 transition-transform duration-200 ${open ? "rotate-180" : ""} ${badge ? "" : "ml-auto"}`} />
      </button>
      {open && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// RATIO ROW
// ════════════════════════════════════════════════════════════

function RatioRow({ ratio }: { ratio: TSDettaglioRapporto }) {
  const ok = ratio.in_tolleranza;
  return (
    <div className="flex items-center gap-2 text-[11px]">
      {ok ? (
        <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-500" />
      ) : (
        <XCircle className="h-3 w-3 shrink-0 text-amber-500" />
      )}
      <span className="flex-1 truncate text-muted-foreground">{ratio.nome}</span>
      <span className={`tabular-nums font-semibold ${ok ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}`}>
        {ratio.valore.toFixed(2)}
      </span>
      <span className="text-muted-foreground/40 text-[10px]">/{ratio.target.toFixed(2)}</span>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// SCORE DECOMPOSITION
// ════════════════════════════════════════════════════════════

function computeSubScore(analysis: TSAnalisiPiano, dimension: "volume" | "balance" | "frequency" | "recovery"): number {
  switch (dimension) {
    case "volume": {
      const muscles = analysis.dettaglio_muscoli;
      if (muscles.length === 0) return 0;
      const weights: Record<string, number> = { ottimale: 1, sopra_mav: 0.8, mev_mav: 0.5, sotto_mev: 0, sopra_mrv: 0 };
      const total = muscles.reduce((sum, m) => sum + (weights[m.stato] ?? 0), 0);
      return (total / muscles.length) * 100;
    }
    case "balance": {
      const ratios = analysis.dettaglio_rapporti;
      if (ratios.length === 0) return 100;
      const balanced = ratios.filter((r) => r.in_tolleranza).length;
      return (balanced / ratios.length) * 100;
    }
    case "frequency": {
      const freqWarnings = analysis.warnings.filter((w) => w.toLowerCase().includes("frequenza")).length;
      return Math.max(0, 100 - freqWarnings * 20);
    }
    case "recovery": {
      const overlaps = analysis.recovery_overlaps.length;
      return Math.max(0, 100 - overlaps * 33);
    }
  }
}
