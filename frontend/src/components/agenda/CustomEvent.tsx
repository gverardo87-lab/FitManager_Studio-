// src/components/agenda/CustomEvent.tsx
"use client";

/**
 * Componente evento personalizzato per react-big-calendar.
 *
 * - Vista week/day: nome cliente per PT, titolo per altri, EventHoverCard su hover
 * - Vista month: dot colorato + orario compatto + nome troncato (no hover card per spazio)
 * - Promemoria: StickyNote icon + TodoHoverCard su click
 * - Cancellato: line-through + opacity ridotta
 *
 * Usa 2 context: QuickActionContext (stato evento), ViewContext (vista corrente).
 */

import { createContext, useContext, type ReactNode } from "react";
import { format } from "date-fns";
import { CheckCircle2, StickyNote } from "lucide-react";
import type { EventProps, View } from "react-big-calendar";
import type { CalendarEvent } from "./calendar-setup";
import { CATEGORY_BORDERS } from "./calendar-setup";
import { EventHoverCard } from "./EventHoverCard";
import { TodoHoverCard } from "./TodoHoverCard";

// ── Context: quick action (stato evento) ──

type QuickActionFn = (eventId: number, stato: string) => void;

const QuickActionContext = createContext<QuickActionFn | undefined>(undefined);

export function QuickActionProvider({
  onQuickAction,
  children,
}: {
  onQuickAction?: QuickActionFn;
  children: ReactNode;
}) {
  return (
    <QuickActionContext.Provider value={onQuickAction}>
      {children}
    </QuickActionContext.Provider>
  );
}

// ── Context: vista corrente (month/week/day) ──

const ViewContext = createContext<View>("week");

export function ViewProvider({
  view,
  children,
}: {
  view: View;
  children: ReactNode;
}) {
  return <ViewContext.Provider value={view}>{children}</ViewContext.Provider>;
}

// ── Custom Event ──

export function CustomEvent({ event }: EventProps<CalendarEvent>) {
  const onQuickAction = useContext(QuickActionContext);
  const currentView = useContext(ViewContext);
  const isMonth = currentView === "month";

  // ── Promemoria ──
  if (event._isTodo && event._todoData) {
    const isCompleted = event._todoData.completato;
    return (
      <TodoHoverCard todo={event._todoData}>
        <div className="flex items-center gap-1.5 truncate leading-tight">
          {isCompleted ? (
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-zinc-400" aria-hidden="true" />
          ) : (
            <StickyNote className="h-3.5 w-3.5 shrink-0 text-amber-700" aria-hidden="true" />
          )}
          <span className={isCompleted ? "line-through" : ""}>
            {event.title}
          </span>
        </div>
      </TodoHoverCard>
    );
  }

  // ── Evento standard ──
  const isCancelled = event.stato === "Cancellato";
  const label = event.cliente_nome
    ? `${event.cliente_nome} ${event.cliente_cognome ?? ""}`.trim()
    : event.title;

  // Month view: dot colorato + orario compatto + nome
  if (isMonth) {
    const dotColor = CATEGORY_BORDERS[event.categoria] ?? "#94a3b8";
    const timeStr = format(event.start, "H");
    return (
      <EventHoverCard event={event} onQuickAction={onQuickAction}>
        <div className="flex items-center gap-1 truncate leading-tight">
          <span
            className="inline-block h-[7px] w-[7px] shrink-0 rounded-full"
            style={{ backgroundColor: dotColor }}
            aria-hidden="true"
          />
          <span className="shrink-0 text-[10px] tabular-nums opacity-60">
            {timeStr}h
          </span>
          <span className={`truncate ${isCancelled ? "line-through opacity-50" : ""}`}>
            {label}
          </span>
        </div>
      </EventHoverCard>
    );
  }

  // Week/Day view: rendering standard
  return (
    <EventHoverCard event={event} onQuickAction={onQuickAction}>
      <div className="truncate text-xs leading-tight">
        <span
          className={`font-medium ${isCancelled ? "line-through opacity-60" : ""}`}
        >
          {label}
        </span>
      </div>
    </EventHoverCard>
  );
}
