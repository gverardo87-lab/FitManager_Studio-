// src/components/agenda/TodoQuickCreateDialog.tsx
"use client";

/**
 * Dialog compatto per creare un promemoria direttamente dall'agenda.
 * Data auto-compilata dal giorno cliccato. Solo titolo + nota opzionale.
 */

import { useState, useCallback } from "react";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import { StickyNote, CalendarDays } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useCreateTodo } from "@/hooks/useTodos";

interface TodoQuickCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultDate: Date | undefined;
}

export function TodoQuickCreateDialog({
  open,
  onOpenChange,
  defaultDate,
}: TodoQuickCreateDialogProps) {
  const [titolo, setTitolo] = useState("");
  const [descrizione, setDescrizione] = useState("");
  const createTodo = useCreateTodo();

  const dateLabel = defaultDate
    ? format(defaultDate, "EEEE d MMMM yyyy", { locale: it })
    : "";

  const dateValue = defaultDate
    ? format(defaultDate, "yyyy-MM-dd")
    : undefined;

  const resetAndClose = useCallback(() => {
    setTitolo("");
    setDescrizione("");
    onOpenChange(false);
  }, [onOpenChange]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = titolo.trim();
      if (!trimmed) return;

      createTodo.mutate(
        {
          titolo: trimmed,
          descrizione: descrizione.trim() || undefined,
          data_scadenza: dateValue,
        },
        { onSuccess: resetAndClose }
      );
    },
    [titolo, descrizione, dateValue, createTodo, resetAndClose]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e as unknown as React.FormEvent);
      }
    },
    [handleSubmit]
  );

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) resetAndClose(); else onOpenChange(v); }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <StickyNote className="h-4 w-4 text-amber-500" />
            Nuovo Promemoria
          </DialogTitle>
          {dateLabel && (
            <DialogDescription className="flex items-center gap-1.5 capitalize">
              <CalendarDays className="h-3.5 w-3.5" />
              {dateLabel}
            </DialogDescription>
          )}
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 pt-1">
          <Input
            autoFocus
            placeholder="Cosa devi ricordare?"
            value={titolo}
            onChange={(e) => setTitolo(e.target.value)}
            maxLength={200}
            onKeyDown={handleKeyDown}
          />

          <Textarea
            placeholder="Note aggiuntive (opzionale)"
            value={descrizione}
            onChange={(e) => setDescrizione(e.target.value)}
            rows={2}
            className="resize-none"
          />

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={resetAndClose}
            >
              Annulla
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={!titolo.trim() || createTodo.isPending}
              className="bg-amber-600 text-white hover:bg-amber-700"
            >
              {createTodo.isPending ? "Creazione..." : "Crea Promemoria"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
