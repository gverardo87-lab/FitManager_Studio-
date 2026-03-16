"use client";

import { Check, X, GripVertical, Undo2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ScheduleSlot } from "@/types/api";

const STATO_DOT: Record<string, string> = {
  pianificato: "bg-zinc-400",
  completato: "bg-emerald-500",
  saltato: "bg-red-500",
  parziale: "bg-amber-500",
};

const STATO_STYLE: Record<string, string> = {
  pianificato: "bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700",
  completato:
    "bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800",
  saltato:
    "bg-red-50/60 dark:bg-red-950/20 border-red-200 dark:border-red-800",
  parziale:
    "bg-amber-50/80 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800",
};

interface ScheduleSlotCardProps {
  slot: ScheduleSlot;
  isToday: boolean;
  isPast: boolean;
  onComplete: (slotId: number) => void;
  onSkip: (slotId: number) => void;
  onDelete: (slotId: number) => void;
  onReopen?: (slotId: number) => void;
  onClick: (slot: ScheduleSlot) => void;
}

export function ScheduleSlotCard({
  slot,
  isToday,
  isPast,
  onComplete,
  onSkip,
  onReopen,
  onClick,
}: ScheduleSlotCardProps) {
  const isPianificato = slot.stato === "pianificato";
  const canComplete = isPianificato && (isPast || isToday);
  const canSkip = isPianificato;
  const canReopen = slot.stato === "completato" || slot.stato === "saltato";

  return (
    <div
      draggable={isPianificato}
      onDragStart={(e) => {
        e.dataTransfer.setData("application/slot-id", String(slot.id));
        e.dataTransfer.effectAllowed = "move";
      }}
      onClick={() => onClick(slot)}
      className={`group flex items-center gap-1 rounded-md border px-1.5 py-1 cursor-pointer
        transition-all hover:shadow-sm
        ${STATO_STYLE[slot.stato] ?? STATO_STYLE.pianificato}
        ${isToday ? "ring-1 ring-teal-500/40" : ""}
        ${isPianificato ? "hover:border-zinc-400 dark:hover:border-zinc-500" : ""}`}
    >
      {/* Drag handle — only for pianificato */}
      {isPianificato ? (
        <GripVertical className="h-3 w-3 shrink-0 text-muted-foreground/30 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab" />
      ) : null}

      {/* Status dot */}
      <div
        className={`h-2 w-2 shrink-0 rounded-full ${STATO_DOT[slot.stato] ?? STATO_DOT.pianificato}`}
      />

      {/* Session name (truncated) */}
      <span
        className={`min-w-0 flex-1 truncate text-xs font-medium ${
          slot.stato === "saltato" ? "line-through decoration-red-400/60 text-muted-foreground" : ""
        }`}
      >
        {slot.sessione_nome}
      </span>

      {/* Quick actions: complete / skip (pianificato) or reopen (completato/saltato) */}
      {isPianificato ? (
        <div className="flex shrink-0 gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {canComplete ? (
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-900/40"
              onClick={(e) => {
                e.stopPropagation();
                onComplete(slot.id);
              }}
              title="Completata"
            >
              <Check className="h-3 w-3" />
            </Button>
          ) : null}
          {canSkip ? (
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/40"
              onClick={(e) => {
                e.stopPropagation();
                onSkip(slot.id);
              }}
              title="Saltata"
            >
              <X className="h-3 w-3" />
            </Button>
          ) : null}
        </div>
      ) : canReopen && onReopen ? (
        <div className="flex shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 text-muted-foreground hover:bg-muted"
            onClick={(e) => {
              e.stopPropagation();
              onReopen(slot.id);
            }}
            title="Riapri sessione"
          >
            <Undo2 className="h-3 w-3" />
          </Button>
        </div>
      ) : null}
    </div>
  );
}
