"use client";

import { useState, useMemo } from "react";
import { CalendarDays } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGenerateSchedule } from "@/hooks/useWorkoutSchedule";
import { toISOLocal } from "@/lib/format";
import type { WorkoutPlan } from "@/types/api";

const GIORNI_SETTIMANA = [
  { value: 0, label: "Lun" },
  { value: 1, label: "Mar" },
  { value: 2, label: "Mer" },
  { value: 3, label: "Gio" },
  { value: 4, label: "Ven" },
  { value: 5, label: "Sab" },
  { value: 6, label: "Dom" },
] as const;

interface ScheduleSetupDialogProps {
  plan: WorkoutPlan;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerated?: () => void;
  /** session_id → derived name (overrides template names in preview) */
  sessionNameMap?: Map<number, string>;
}

export function ScheduleSetupDialog({
  plan,
  open,
  onOpenChange,
  onGenerated,
  sessionNameMap,
}: ScheduleSetupDialogProps) {
  const [selectedDays, setSelectedDays] = useState<number[]>([0, 2, 4]); // L/M/V default
  const [dataInizio, setDataInizio] = useState(
    toISOLocal(new Date()).slice(0, 10),
  );
  const [settimane, setSettimane] = useState(plan.durata_settimane || 4);

  const generateMutation = useGenerateSchedule(plan.id);

  const toggleDay = (day: number) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort(),
    );
  };

  const preview = useMemo(() => {
    if (selectedDays.length === 0 || !plan.sessioni.length) return [];
    const sorted = [...selectedDays].sort((a, b) => a - b);
    const sessions = plan.sessioni;
    const rows: { settimana: number; slots: { giorno: string; sessione: string }[] }[] = [];
    let sIdx = 0;
    for (let w = 0; w < Math.min(settimane, 3); w++) {
      const slots: { giorno: string; sessione: string }[] = [];
      for (const day of sorted) {
        const s = sessions[sIdx % sessions.length];
        slots.push({
          giorno: GIORNI_SETTIMANA[day].label,
          sessione: sessionNameMap?.get(s.id) ?? s.nome_sessione,
        });
        sIdx++;
      }
      rows.push({ settimana: w + 1, slots });
    }
    return rows;
  }, [selectedDays, plan.sessioni, settimane]);

  const totalSlots = selectedDays.length * settimane;

  const handleGenerate = () => {
    generateMutation.mutate(
      {
        pattern_giorni: selectedDays,
        data_inizio: dataInizio,
        settimane,
      },
      {
        onSuccess: () => {
          onOpenChange(false);
          onGenerated?.();
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-teal-600" />
            Pianifica Calendario
          </DialogTitle>
          <DialogDescription>
            Scegli i giorni e la durata per &quot;{plan.nome}&quot;
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          {/* Giorni della settimana */}
          <div className="space-y-2">
            <Label>Quando si allena?</Label>
            <div className="flex gap-1.5">
              {GIORNI_SETTIMANA.map((g) => (
                <button
                  key={g.value}
                  type="button"
                  onClick={() => toggleDay(g.value)}
                  className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                    selectedDays.includes(g.value)
                      ? "bg-teal-600 text-white"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  {g.label}
                </button>
              ))}
            </div>
            {selectedDays.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {selectedDays.length} sessioni/settimana — distribuzione:{" "}
                {selectedDays.map((d) => GIORNI_SETTIMANA[d].label).join("/")}
              </p>
            )}
          </div>

          {/* Data inizio + Settimane */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="data-inizio">Data inizio</Label>
              <Input
                id="data-inizio"
                type="date"
                value={dataInizio}
                onChange={(e) => setDataInizio(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="settimane">Settimane</Label>
              <Input
                id="settimane"
                type="number"
                min={1}
                max={52}
                value={settimane}
                onChange={(e) => setSettimane(Number(e.target.value))}
              />
            </div>
          </div>

          {/* Anteprima */}
          {preview.length > 0 && (
            <div className="space-y-2">
              <Label>Anteprima</Label>
              <div className="rounded-lg border bg-muted/30 p-3 text-sm space-y-1">
                {preview.map((row) => (
                  <div key={row.settimana} className="flex gap-2">
                    <span className="w-14 shrink-0 text-muted-foreground">
                      Sett {row.settimana}:
                    </span>
                    <span>
                      {row.slots.map((s, i) => (
                        <span key={i}>
                          {i > 0 && " · "}
                          <span className="text-muted-foreground">{s.giorno}=</span>
                          <span className="font-medium">{s.sessione}</span>
                        </span>
                      ))}
                    </span>
                  </div>
                ))}
                {settimane > 3 && (
                  <p className="text-muted-foreground">
                    ...e altre {settimane - 3} settimane
                  </p>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Totale: {totalSlots} sessioni in {settimane} settimane
              </p>
            </div>
          )}

          {/* Azioni */}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={
                selectedDays.length === 0 ||
                !dataInizio ||
                settimane < 1 ||
                generateMutation.isPending
              }
            >
              {generateMutation.isPending ? "Generazione..." : `Genera ${totalSlots} sessioni`}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
