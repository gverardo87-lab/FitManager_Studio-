"use client";

import { useState, useMemo } from "react";
import { Check, X, Dumbbell, Clock, Target, Undo2, ClipboardEdit, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { formatShortDate } from "@/lib/format";
import type { ScheduleSlot, WorkoutPlan, WorkoutExerciseRow } from "@/types/api";
import type { ExerciseLogTrainerInput } from "@/hooks/useWorkoutSchedule";

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
  onCompleteWithData?: (slotId: number, exerciseData: ExerciseLogTrainerInput[]) => void;
  onSkip: (slotId: number) => void;
  onReopen?: (slotId: number) => void;
}

/** Collects all exercises from a session (straight + blocks) */
function collectAllExercises(session: WorkoutPlan["sessioni"][number]): WorkoutExerciseRow[] {
  const exercises: WorkoutExerciseRow[] = [];
  // Straight exercises
  for (const ex of session.esercizi) {
    exercises.push(ex);
  }
  // Block exercises
  for (const block of session.blocchi) {
    for (const ex of block.esercizi) {
      exercises.push(ex);
    }
  }
  return exercises;
}

interface ExerciseFormRow {
  id_esercizio_sessione: number;
  nome: string;
  serie: number;
  ripetizioni: string;
  carico_kg: number | null;
  // Editable values
  serie_effettive: string;
  ripetizioni_effettive: string;
  carico_effettivo_kg: string;
  rpe: string;
  note: string;
}

export function SlotDetailSheet({
  slot,
  plan,
  open,
  onOpenChange,
  onComplete,
  onCompleteWithData,
  onSkip,
  onReopen,
}: SlotDetailSheetProps) {
  const session = plan.sessioni.find((s) => s.id === slot.id_sessione);
  const statoConfig = STATO_LABELS[slot.stato] ?? STATO_LABELS.pianificato;
  const [showDataForm, setShowDataForm] = useState(false);

  const todayStr = useMemo(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }, []);
  const isFuture = slot.data_pianificata > todayStr;
  const canComplete = slot.stato === "pianificato" && !isFuture;
  const canSkip = slot.stato === "pianificato";
  const canReopen = slot.stato === "completato" || slot.stato === "saltato";

  // Build form rows from plan exercises
  const allExercises = useMemo(() => {
    if (!session) return [];
    return collectAllExercises(session);
  }, [session]);

  const [formRows, setFormRows] = useState<ExerciseFormRow[]>([]);

  // Initialize form when opening data entry mode
  const handleOpenDataForm = () => {
    setFormRows(
      allExercises.map((ex) => ({
        id_esercizio_sessione: ex.id,
        nome: ex.esercizio_nome,
        serie: ex.serie,
        ripetizioni: ex.ripetizioni,
        carico_kg: ex.carico_kg,
        serie_effettive: String(ex.serie),
        ripetizioni_effettive: ex.ripetizioni,
        carico_effettivo_kg: ex.carico_kg != null ? String(ex.carico_kg) : "",
        rpe: "",
        note: "",
      })),
    );
    setShowDataForm(true);
  };

  const updateFormRow = (index: number, field: keyof ExerciseFormRow, value: string) => {
    setFormRows((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const handleSubmitData = () => {
    if (!onCompleteWithData) return;
    const exerciseData: ExerciseLogTrainerInput[] = formRows.map((row) => ({
      id_esercizio_sessione: row.id_esercizio_sessione,
      serie_effettive: row.serie_effettive ? parseInt(row.serie_effettive, 10) || null : null,
      ripetizioni_effettive: row.ripetizioni_effettive || null,
      carico_effettivo_kg: row.carico_effettivo_kg ? parseFloat(row.carico_effettivo_kg) || null : null,
      rpe: row.rpe ? parseFloat(row.rpe) || null : null,
      note_cliente: row.note || null,
    }));
    onCompleteWithData(slot.id, exerciseData);
    setShowDataForm(false);
    onOpenChange(false);
  };

  const handleCompleteAsPlanned = () => {
    onComplete(slot.id);
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={(o) => {
      if (!o) setShowDataForm(false);
      onOpenChange(o);
    }}>
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
          {canSkip && !showDataForm && (
            <div className="space-y-2">
              <div className="flex gap-2">
                {canComplete ? (
                  <Button
                    className="flex-1"
                    onClick={handleCompleteAsPlanned}
                  >
                    <CheckCheck className="h-4 w-4 mr-2" />
                    Completata come da piano
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
              {canComplete && onCompleteWithData && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleOpenDataForm}
                >
                  <ClipboardEdit className="h-4 w-4 mr-2" />
                  Inserisci dati effettivi
                </Button>
              )}
            </div>
          )}

          {/* Data entry form */}
          {showDataForm && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Dati effettivi</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDataForm(false)}
                >
                  Annulla
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Pre-compilati dal piano. Modifica solo quello che e' cambiato.
              </p>

              {formRows.map((row, idx) => (
                <div key={row.id_esercizio_sessione} className="rounded-md border p-3 space-y-2">
                  <p className="text-sm font-medium truncate">{row.nome}</p>
                  <div className="grid grid-cols-4 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground uppercase">Serie</label>
                      <Input
                        className="h-8 text-xs text-center"
                        value={row.serie_effettive}
                        onChange={(e) => updateFormRow(idx, "serie_effettive", e.target.value)}
                        aria-label={`Serie ${row.nome}`}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground uppercase">Rep</label>
                      <Input
                        className="h-8 text-xs text-center"
                        value={row.ripetizioni_effettive}
                        onChange={(e) => updateFormRow(idx, "ripetizioni_effettive", e.target.value)}
                        aria-label={`Ripetizioni ${row.nome}`}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground uppercase">Kg</label>
                      <Input
                        className="h-8 text-xs text-center"
                        value={row.carico_effettivo_kg}
                        onChange={(e) => updateFormRow(idx, "carico_effettivo_kg", e.target.value)}
                        placeholder="BW"
                        aria-label={`Carico ${row.nome}`}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground uppercase">RPE</label>
                      <Input
                        className="h-8 text-xs text-center"
                        value={row.rpe}
                        onChange={(e) => updateFormRow(idx, "rpe", e.target.value)}
                        placeholder="—"
                        aria-label={`RPE ${row.nome}`}
                      />
                    </div>
                  </div>
                  <Input
                    className="h-8 text-xs"
                    value={row.note}
                    onChange={(e) => updateFormRow(idx, "note", e.target.value)}
                    placeholder="Note..."
                    aria-label={`Note ${row.nome}`}
                  />
                </div>
              ))}

              <Button className="w-full" onClick={handleSubmitData}>
                <Check className="h-4 w-4 mr-2" />
                Conferma e completa
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

          {!showDataForm && (
            <>
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
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
