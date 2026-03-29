// training-intelligence/WorkoutDiffSection.tsx
"use client";

/**
 * Workout Diff — il "git diff" dell'allenamento.
 *
 * Per ogni sessione completata mostra il confronto esercizio-per-esercizio
 * tra il piano del trainer e l'esecuzione reale del cliente.
 * Il dato piu' importante per un PT.
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, GitCompareArrows, TrendingDown, TrendingUp, Minus, MessageSquare } from "lucide-react";
import { formatShortDate } from "@/lib/format";
import type { WorkoutDiffResponse, SessionDiff, ExerciseDiff, ComplianceSummary } from "@/types/api";

interface WorkoutDiffSectionProps {
  data: WorkoutDiffResponse;
}

export function WorkoutDiffSection({ data }: WorkoutDiffSectionProps) {
  if (data.sessioni.length === 0) return null;

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <GitCompareArrows className="h-4 w-4 text-teal-600" />
        <div>
          <h3 className="text-sm font-bold">Piano vs Esecuzione</h3>
          <p className="text-[11px] text-muted-foreground">
            Confronto sessione per sessione — cosa il cliente fa realmente
          </p>
        </div>
      </div>

      {/* Summary cards */}
      <ComplianceSummaryBar summary={data.summary} />

      {/* Session list */}
      <div className="space-y-2">
        {data.sessioni.map((s, i) => (
          <SessionDiffCard key={`${s.data}-${i}`} session={s} />
        ))}
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════

function ComplianceSummaryBar({ summary }: { summary: ComplianceSummary }) {
  const comp = summary.compliance_media_globale;
  const compColor = comp >= 90 ? "text-emerald-700" : comp >= 70 ? "text-amber-700" : "text-red-700";
  const compBg = comp >= 90 ? "bg-emerald-50 border-emerald-200" : comp >= 70 ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200";

  return (
    <div className="space-y-2">
      {/* Main compliance score */}
      <div className={`flex items-center justify-between rounded-lg border p-3 ${compBg}`}>
        <div>
          <p className="text-xs text-muted-foreground">Compliance media</p>
          <p className={`text-2xl font-bold tabular-nums ${compColor}`}>{comp}%</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <p className="text-lg font-bold tabular-nums text-emerald-600">{summary.esercizi_sopra_piano}</p>
            <p className="text-[9px] text-muted-foreground">Sopra piano</p>
          </div>
          <div>
            <p className="text-lg font-bold tabular-nums text-zinc-600">{summary.esercizi_in_linea}</p>
            <p className="text-[9px] text-muted-foreground">In linea</p>
          </div>
          <div>
            <p className="text-lg font-bold tabular-nums text-red-600">{summary.esercizi_sotto_piano}</p>
            <p className="text-[9px] text-muted-foreground">Sotto piano</p>
          </div>
        </div>
      </div>

      {/* Weak/strong points */}
      {(summary.punti_deboli.length > 0 || summary.punti_forti.length > 0) ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {summary.punti_deboli.length > 0 ? (
            <div className="bg-red-50/50 border border-red-100 rounded-lg p-2">
              <p className="text-[10px] font-semibold text-red-700 mb-1">Punti deboli</p>
              {summary.punti_deboli.map((p) => (
                <p key={p} className="text-[10px] text-red-600">{p}</p>
              ))}
            </div>
          ) : null}
          {summary.punti_forti.length > 0 ? (
            <div className="bg-emerald-50/50 border border-emerald-100 rounded-lg p-2">
              <p className="text-[10px] font-semibold text-emerald-700 mb-1">Punti forti</p>
              {summary.punti_forti.map((p) => (
                <p key={p} className="text-[10px] text-emerald-600">{p}</p>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════

function SessionDiffCard({ session }: { session: SessionDiff }) {
  const [expanded, setExpanded] = useState(false);
  const comp = session.compliance_media;
  const compColor = comp >= 90 ? "text-emerald-700" : comp >= 70 ? "text-amber-700" : "text-red-700";
  const barColor = comp >= 90 ? "bg-emerald-500" : comp >= 70 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header — always visible */}
      <button
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-muted/30 transition-colors text-left"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        )}
        <span className="text-xs text-muted-foreground tabular-nums w-[70px] shrink-0">
          {formatShortDate(session.data)}
        </span>
        <span className="text-xs font-semibold flex-1 truncate">{session.nome_sessione}</span>
        <span className="text-[10px] text-muted-foreground">
          {session.esercizi_completati}/{session.esercizi_totali} es.
        </span>
        {/* Mini compliance bar */}
        <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden shrink-0">
          <div className={`h-full rounded-full ${barColor}`} style={{ width: `${Math.min(comp, 100)}%` }} />
        </div>
        <span className={`text-xs font-bold tabular-nums w-10 text-right ${compColor}`}>
          {comp}%
        </span>
      </button>

      {/* Expanded: exercise diffs */}
      {expanded ? (
        <div className="border-t bg-muted/10">
          {/* Column headers */}
          <div className="grid grid-cols-[1fr_64px_64px_64px_48px] gap-1 px-3 py-1 text-[9px] font-semibold uppercase text-muted-foreground border-b">
            <span>Esercizio</span>
            <span className="text-center">Serie</span>
            <span className="text-center">Reps</span>
            <span className="text-center">Kg</span>
            <span className="text-center">RPE</span>
          </div>

          {session.esercizi.map((ex, i) => (
            <ExerciseDiffRow key={`${ex.id_esercizio}-${i}`} diff={ex} />
          ))}

          {session.durata_effettiva_min ? (
            <div className="px-3 py-1.5 text-[10px] text-muted-foreground border-t">
              Durata effettiva: {session.durata_effettiva_min} min
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════

function ExerciseDiffRow({ diff }: { diff: ExerciseDiff }) {
  const notDone = diff.serie_fatto === null;

  return (
    <div className={`grid grid-cols-[1fr_64px_64px_64px_48px] gap-1 px-3 py-1.5 text-xs items-center border-b last:border-b-0 ${notDone ? "opacity-40" : ""}`}>
      {/* Nome + note */}
      <div className="min-w-0">
        <p className="font-medium truncate text-[11px]">{diff.nome_esercizio}</p>
        {diff.note_cliente ? (
          <p className="flex items-center gap-1 text-[9px] text-muted-foreground truncate">
            <MessageSquare className="h-2.5 w-2.5 shrink-0" />
            {diff.note_cliente}
          </p>
        ) : null}
      </div>

      {/* Serie */}
      <DeltaCell piano={diff.serie_piano} fatto={diff.serie_fatto} delta={diff.delta_serie} unit="" />

      {/* Reps */}
      <DeltaCell piano={diff.reps_piano_avg} fatto={diff.reps_fatto_avg} delta={diff.delta_reps} unit="" decimals={1} />

      {/* Kg */}
      <DeltaCell piano={diff.kg_piano} fatto={diff.kg_fatto} delta={diff.delta_kg} unit="" />

      {/* RPE */}
      <div className="text-center">
        {diff.rpe != null ? (
          <span className={`text-[10px] font-semibold tabular-nums ${diff.rpe >= 9 ? "text-red-600" : diff.rpe >= 7 ? "text-amber-600" : "text-zinc-600"}`}>
            {diff.rpe}
          </span>
        ) : (
          <span className="text-[10px] text-muted-foreground">-</span>
        )}
      </div>
    </div>
  );
}

function DeltaCell({
  piano, fatto, delta, unit, decimals = 0,
}: {
  piano: number | null;
  fatto: number | null;
  delta: number | null;
  unit: string;
  decimals?: number;
}) {
  if (fatto === null || fatto === undefined) {
    return (
      <div className="text-center">
        <span className="text-[10px] text-muted-foreground">{piano != null ? formatNum(piano, decimals) : "-"}</span>
      </div>
    );
  }

  const showDelta = delta !== null && delta !== undefined && delta !== 0;
  const isPositive = delta != null && delta > 0;
  const isNegative = delta != null && delta < 0;

  return (
    <div className="text-center leading-tight">
      <span className="text-[10px] font-semibold tabular-nums">{formatNum(fatto, decimals)}{unit}</span>
      {showDelta ? (
        <span className={`flex items-center justify-center gap-0.5 text-[9px] font-semibold tabular-nums ${isPositive ? "text-emerald-600" : isNegative ? "text-red-600" : "text-zinc-400"}`}>
          {isPositive ? <TrendingUp className="h-2.5 w-2.5" /> : isNegative ? <TrendingDown className="h-2.5 w-2.5" /> : <Minus className="h-2.5 w-2.5" />}
          {isPositive ? "+" : ""}{formatNum(delta!, decimals)}
        </span>
      ) : (
        <span className="flex items-center justify-center text-[9px] text-zinc-400">
          <Minus className="h-2.5 w-2.5" />
        </span>
      )}
    </div>
  );
}

function formatNum(n: number, decimals: number): string {
  return decimals > 0 ? n.toFixed(decimals) : String(Math.round(n));
}
