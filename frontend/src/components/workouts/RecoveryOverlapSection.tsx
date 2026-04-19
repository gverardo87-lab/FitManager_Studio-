// src/components/workouts/RecoveryOverlapSection.tsx
"use client";

/**
 * Recupero Muscolare — Drill-down sovrapposizione tra sessioni.
 *
 * Mostra quali muscoli si sovrappongono tra sessioni consecutive,
 * con dettaglio serie per sessione e indicatore severita'.
 *
 * Dati: TSAnalisiPiano.recovery_overlaps (TSDettaglioRecovery[]).
 */

import { useState } from "react";
import {
  RefreshCw,
  CheckCircle2,
  ChevronDown,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { TSDettaglioRecovery } from "@/types/api";

// ════════════════════════════════════════════════════════════
// LABEL MUSCOLI
// ════════════════════════════════════════════════════════════

const MUSCLE_LABELS: Record<string, string> = {
  petto: "Petto",
  dorsali: "Dorsali",
  deltoide_anteriore: "Deltoide ant.",
  deltoide_laterale: "Deltoide lat.",
  deltoide_posteriore: "Deltoide post.",
  bicipiti: "Bicipiti",
  tricipiti: "Tricipiti",
  quadricipiti: "Quadricipiti",
  femorali: "Femorali",
  glutei: "Glutei",
  polpacci: "Polpacci",
  trapezio: "Trapezio",
  core: "Core",
  avambracci: "Avambracci",
  adduttori: "Adduttori",
};

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

interface RecoveryOverlapSectionProps {
  overlaps: TSDettaglioRecovery[];
}

export function RecoveryOverlapSection({ overlaps }: RecoveryOverlapSectionProps) {
  const [isOpen, setIsOpen] = useState(overlaps.length > 0);
  const count = overlaps.length;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4 border-l-orange-500/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 text-orange-600" />
                <CardTitle className="text-sm font-semibold">Recupero Muscolare</CardTitle>
                {count > 0 ? (
                  <Badge className="text-xs tabular-nums bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300">
                    {count} sovrapposizion{count === 1 ? "e" : "i"}
                  </Badge>
                ) : (
                  <Badge className="text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    OK
                  </Badge>
                )}
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 px-4 pb-4 space-y-2">
            {count === 0 ? (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-md bg-emerald-50 dark:bg-emerald-950/30">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <p className="text-xs text-emerald-700 dark:text-emerald-300">
                  Nessun rischio — recupero muscolare adeguato tra le sessioni.
                </p>
              </div>
            ) : (
              <>
                {overlaps.map((overlap, idx) => (
                  <OverlapCard key={idx} overlap={overlap} />
                ))}
                <p className="text-[10px] text-muted-foreground pt-1">
                  I muscoli hanno bisogno di 48-72h per il recupero completo (NSCA 2016).
                  Sessioni consecutive con alto volume sugli stessi muscoli riducono l&apos;adattamento.
                </p>
              </>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

// ════════════════════════════════════════════════════════════
// OVERLAP CARD — Espandibile per coppia di sessioni
// ════════════════════════════════════════════════════════════

function OverlapCard({ overlap }: { overlap: TSDettaglioRecovery }) {
  const [expanded, setExpanded] = useState(false);
  const muscleCount = overlap.muscoli_overlap.length;

  return (
    <div className={`rounded-md border transition-colors ${expanded ? "bg-muted/20" : "hover:bg-muted/10"}`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-3 py-2 flex items-center gap-2"
      >
        <AlertTriangle className="h-3.5 w-3.5 text-orange-500 shrink-0" />
        <span className="text-xs font-medium flex-1">
          {overlap.sessione_a} ↔ {overlap.sessione_b}
        </span>
        <span className="text-[10px] text-muted-foreground">
          {muscleCount} muscol{muscleCount === 1 ? "o" : "i"}
        </span>
        <ChevronDown
          className={`h-3 w-3 text-muted-foreground transition-transform shrink-0 ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {expanded && (
        <div className="px-3 pb-2.5">
          <div className="rounded border overflow-hidden">
            {/* Header tabella */}
            <div className="grid grid-cols-[1fr_60px_60px_24px] gap-1 px-2 py-1 bg-muted/40 text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">
              <span>Muscolo</span>
              <span className="text-center">Sess. A</span>
              <span className="text-center">Sess. B</span>
              <span />
            </div>
            {/* Righe muscolo */}
            {overlap.muscoli_overlap.map((muscolo) => {
              const label = MUSCLE_LABELS[muscolo] ?? muscolo;
              const serieA = overlap.serie_overlap_a[muscolo] ?? 0;
              const serieB = overlap.serie_overlap_b[muscolo] ?? 0;
              const isHigh = serieA > 4 && serieB > 4;
              return (
                <div
                  key={muscolo}
                  className="grid grid-cols-[1fr_60px_60px_24px] gap-1 px-2 py-1 border-t text-[11px] items-center"
                >
                  <span className="text-muted-foreground truncate">{label}</span>
                  <span className="text-center font-mono tabular-nums">{serieA}s</span>
                  <span className="text-center font-mono tabular-nums">{serieB}s</span>
                  <span
                    className={`h-2 w-2 rounded-full mx-auto ${
                      isHigh ? "bg-red-500" : "bg-amber-400"
                    }`}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
