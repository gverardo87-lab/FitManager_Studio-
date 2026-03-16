"use client";

import { useMemo } from "react";
import { Check, X, Dumbbell, Clock, Target, Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { formatShortDate } from "@/lib/format";
import type { ScheduleSlot, WorkoutPlan } from "@/types/api";

const STATO_LABELS: Record<string, { label: string; color: string }> = {
  pianificato: { label: "Pianificato", color: "bg-zinc-100 text-zinc-700" },
  completato: { label: "Completato", color: "bg-emerald-100 text-emerald-700" },
  saltato: { label: "Saltato", color: "bg-red-100 text-red-700" },
  parziale: { label: "Parziale", color: "bg-amber-100 text-amber-700" },
};

interface SlotDetailSheetProps {
  slot: ScheduleSlot;
  plan: WorkoutPlan;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: (slotId: number) => void;
  onSkip: (slotId: number) => void;
  onReopen?: (slotId: number) => void;
}

export function SlotDetailSheet({
  slot,
  plan,
  open,
  onOpenChange,
  onComplete,
  onSkip,
  onReopen,
}: SlotDetailSheetProps) {
  const session = plan.sessioni.find((s) => s.id === slot.id_sessione);
  const statoConfig = STATO_LABELS[slot.stato] ?? STATO_LABELS.pianificato;

  const todayStr = useMemo(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }, []);
  const isFuture = slot.data_pianificata > todayStr;
  const canComplete = slot.stato === "pianificato" && !isFuture;
  const canSkip = slot.stato === "pianificato";
  const canReopen = slot.stato === "completato" || slot.stato === "saltato";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Dumbbell className="h-5 w-5 text-teal-600" />
            {slot.sessione_nome}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-4 space-y-4">
          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge className={statoConfig.color}>{statoConfig.label}</Badge>
            <span className="text-sm text-muted-foreground">
              {formatShortDate(slot.data_pianificata)}
            </span>
            {slot.focus_muscolare && (
              <Badge variant="outline" className="text-xs">
                <Target className="mr-1 h-3 w-3" />
                {slot.focus_muscolare}
              </Badge>
            )}
          </div>

          {/* Actions — pianificato */}
          {canSkip && (
            <div className="flex gap-2">
              {canComplete ? (
                <Button
                  className="flex-1"
                  onClick={() => {
                    onComplete(slot.id);
                    onOpenChange(false);
                  }}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Completata
                </Button>
              ) : (
                <Button className="flex-1" disabled title="Non puoi completare una sessione futura">
                  <Check className="h-4 w-4 mr-2" />
                  Completata
                </Button>
              )}
              <Button
                variant="outline"
                className="text-red-600 hover:bg-red-50"
                onClick={() => {
                  onSkip(slot.id);
                  onOpenChange(false);
                }}
              >
                <X className="h-4 w-4 mr-2" />
                Saltata
              </Button>
            </div>
          )}

          {/* Actions — reopen */}
          {canReopen && onReopen ? (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                onReopen(slot.id);
                onOpenChange(false);
              }}
            >
              <Undo2 className="h-4 w-4 mr-2" />
              Riapri sessione
            </Button>
          ) : null}

          <Separator />

          {/* Exercise list */}
          {session ? (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">
                Esercizi ({session.esercizi.length})
              </h4>
              {session.esercizi.map((ex, idx) => (
                <div
                  key={ex.id}
                  className="flex items-start gap-3 rounded-md border p-2.5"
                >
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                    {idx + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">
                      {ex.esercizio_nome}
                    </p>
                    <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                      <span>{ex.serie} × {ex.ripetizioni}</span>
                      {ex.carico_kg != null && ex.carico_kg > 0 && (
                        <span>{ex.carico_kg} kg</span>
                      )}
                      <span>
                        <Clock className="inline h-3 w-3 mr-0.5" />
                        {ex.tempo_riposo_sec}s
                      </span>
                    </div>
                  </div>
                </div>
              ))}

              {/* Blocks */}
              {session.blocchi.map((block) => (
                <div key={block.id} className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs uppercase">
                      {block.tipo_blocco}
                    </Badge>
                    {block.nome && (
                      <span className="text-xs text-muted-foreground">{block.nome}</span>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {block.giri} round
                    </span>
                  </div>
                  {block.esercizi.map((ex, idx) => (
                    <div
                      key={ex.id}
                      className="flex items-start gap-3 rounded-md border border-dashed p-2 ml-3"
                    >
                      <span className="mt-0.5 text-xs text-muted-foreground">
                        {String.fromCharCode(65 + idx)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm truncate">{ex.esercizio_nome}</p>
                        <p className="text-xs text-muted-foreground">
                          {ex.serie} × {ex.ripetizioni}
                          {ex.carico_kg != null && ex.carico_kg > 0 && ` · ${ex.carico_kg}kg`}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Sessione non trovata nella scheda
            </p>
          )}

          {/* Notes */}
          {slot.note && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Note</h4>
                <p className="text-sm">{slot.note}</p>
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
