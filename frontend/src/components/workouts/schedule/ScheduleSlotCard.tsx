"use client";

import { Check, X, Clock, MoreHorizontal, GripVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ScheduleSlot } from "@/types/api";

const STATO_CONFIG = {
  pianificato: {
    bg: "bg-white dark:bg-zinc-900",
    border: "border-zinc-200 dark:border-zinc-700",
    dot: "bg-zinc-300",
    label: "Pianificato",
  },
  completato: {
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-emerald-300 dark:border-emerald-700",
    dot: "bg-emerald-500",
    label: "Completato",
  },
  saltato: {
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-300 dark:border-red-700",
    dot: "bg-red-500",
    label: "Saltato",
  },
  parziale: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-300 dark:border-amber-700",
    dot: "bg-amber-500",
    label: "Parziale",
  },
} as const;

interface ScheduleSlotCardProps {
  slot: ScheduleSlot;
  isToday: boolean;
  isPast: boolean;
  onComplete: (slotId: number) => void;
  onSkip: (slotId: number) => void;
  onDelete: (slotId: number) => void;
  onClick: (slot: ScheduleSlot) => void;
}

export function ScheduleSlotCard({
  slot,
  isToday,
  isPast,
  onComplete,
  onSkip,
  onDelete,
  onClick,
}: ScheduleSlotCardProps) {
  const config = STATO_CONFIG[slot.stato];
  const canAct = slot.stato === "pianificato";

  return (
    <div
      onClick={() => onClick(slot)}
      className={`group relative rounded-lg border p-2.5 cursor-pointer transition-all hover:shadow-sm ${config.bg} ${config.border} ${
        isToday ? "ring-2 ring-teal-500/50" : ""
      }`}
    >
      {/* Header: dot + nome */}
      <div className="flex items-start gap-2">
        <div className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${config.dot}`} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate">{slot.sessione_nome}</p>
          {slot.focus_muscolare && (
            <p className="text-xs text-muted-foreground truncate">
              {slot.focus_muscolare}
            </p>
          )}
        </div>

        {/* Quick actions */}
        {canAct && (
          <div className="flex shrink-0 gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-emerald-600 hover:bg-emerald-100"
              onClick={(e) => {
                e.stopPropagation();
                onComplete(slot.id);
              }}
              title="Completata"
            >
              <Check className="h-3.5 w-3.5" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreHorizontal className="h-3.5 w-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onSkip(slot.id)}>
                  <X className="mr-2 h-4 w-4 text-red-500" />
                  Segna come saltata
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => onDelete(slot.id)}
                  className="text-red-600"
                >
                  Rimuovi dal calendario
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Status icon for completed/skipped */}
      {slot.stato === "completato" && (
        <div className="absolute -top-1.5 -right-1.5 rounded-full bg-emerald-500 p-0.5">
          <Check className="h-3 w-3 text-white" />
        </div>
      )}
      {slot.stato === "saltato" && (
        <div className="absolute -top-1.5 -right-1.5 rounded-full bg-red-500 p-0.5">
          <X className="h-3 w-3 text-white" />
        </div>
      )}
    </div>
  );
}
