// src/components/agenda/SlotChoiceDialog.tsx
"use client";

/**
 * Dialog di scelta quando si clicca uno slot vuoto in agenda.
 * Due opzioni: creare un Evento o un Promemoria.
 */

import { format } from "date-fns";
import { it } from "date-fns/locale";
import { CalendarDays, StickyNote } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface SlotChoiceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onChooseEvent: () => void;
  onChoosePromemoria: () => void;
  slotDate: Date | undefined;
}

export function SlotChoiceDialog({
  open,
  onOpenChange,
  onChooseEvent,
  onChoosePromemoria,
  slotDate,
}: SlotChoiceDialogProps) {
  const dateLabel = slotDate
    ? format(slotDate, "EEEE d MMMM, HH:mm", { locale: it })
    : "";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Cosa vuoi creare?</DialogTitle>
          {dateLabel && (
            <DialogDescription className="capitalize">
              {dateLabel}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3 pt-2">
          {/* Evento */}
          <button
            type="button"
            onClick={onChooseEvent}
            className="group flex flex-col items-center gap-3 rounded-xl border-2 border-transparent bg-blue-50 p-5 transition-all hover:border-blue-400 hover:shadow-md dark:bg-blue-950/30 dark:hover:border-blue-500"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 transition-transform group-hover:scale-110 dark:bg-blue-900/50">
              <CalendarDays className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                Evento
              </p>
              <p className="mt-0.5 text-[11px] text-blue-600/70 dark:text-blue-400/60">
                Sessione, colloquio, corso
              </p>
            </div>
          </button>

          {/* Promemoria */}
          <button
            type="button"
            onClick={onChoosePromemoria}
            className="group flex flex-col items-center gap-3 rounded-xl border-2 border-transparent bg-amber-50 p-5 transition-all hover:border-amber-400 hover:shadow-md dark:bg-amber-950/30 dark:hover:border-amber-500"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-100 transition-transform group-hover:scale-110 dark:bg-amber-900/50">
              <StickyNote className="h-6 w-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                Promemoria
              </p>
              <p className="mt-0.5 text-[11px] text-amber-600/70 dark:text-amber-400/60">
                Nota, scadenza, to-do
              </p>
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
