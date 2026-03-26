// src/components/agenda/AgendaCalendar.tsx
"use client";

/**
 * Wrapper react-big-calendar con:
 * - Drag & Drop (withDragAndDrop HOC)
 * - Controlled state (date + view)
 * - Custom Toolbar (shadcn/ui)
 * - Custom Event (nome cliente per PT + hover card)
 * - Vista settimanale default, slot 30 min, 06:00-22:00
 */

import { useState, useCallback, useMemo } from "react";
import { format } from "date-fns";
import { Calendar, Views, type View, type SlotInfo } from "react-big-calendar";
import withDragAndDrop from "react-big-calendar/lib/addons/dragAndDrop";

import {
  localizer,
  italianMessages,
  getEventStyle,
  toCalendarEvent,
  todoToCalendarEvent,
  type CalendarEvent,
} from "./calendar-setup";
import { CustomToolbar } from "./CustomToolbar";
import { CustomEvent, QuickActionProvider, ViewProvider } from "./CustomEvent";
import type { EventHydrated } from "@/hooks/useAgenda";
import type { Todo } from "@/types/api";

// HOC: abilita drag & drop + resize sugli eventi
const DnDCalendar = withDragAndDrop<CalendarEvent>(Calendar);

interface AgendaCalendarProps {
  events: EventHydrated[];
  todos?: Todo[];
  onSelectSlot: (slotInfo: SlotInfo) => void;
  onSelectEvent: (event: CalendarEvent) => void;
  onRangeChange: (range: { start: Date; end: Date }) => void;
  onEventDrop: (args: { event: CalendarEvent; start: Date; end: Date }) => void;
  onEventResize: (args: { event: CalendarEvent; start: Date; end: Date }) => void;
  onQuickAction?: (eventId: number, stato: string) => void;
}

export function AgendaCalendar({
  events,
  todos,
  onSelectSlot,
  onSelectEvent,
  onRangeChange,
  onEventDrop,
  onEventResize,
  onQuickAction,
}: AgendaCalendarProps) {
  // ── Controlled state: data corrente + vista attiva ──
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentView, setCurrentView] = useState<View>(Views.WEEK);

  const calendarEvents = useMemo(() => {
    const eventItems = events.map(toCalendarEvent);
    const todoItems = (todos ?? []).map(todoToCalendarEvent);
    return [...eventItems, ...todoItems];
  }, [events, todos]);

  const eventPropGetter = useCallback(
    (event: CalendarEvent) => ({ style: getEventStyle(event) }),
    []
  );

  // ── Density heatmap: conta eventi per giorno → classe CSS ──
  const dayDensityMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const ev of calendarEvents) {
      if (ev._isTodo) continue; // solo eventi reali per density
      const key = format(ev.start, "yyyy-MM-dd");
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return map;
  }, [calendarEvents]);

  const dayPropGetter = useCallback(
    (date: Date) => {
      if (currentView !== "month") return {};
      const key = format(date, "yyyy-MM-dd");
      const count = dayDensityMap.get(key) ?? 0;
      if (count === 0) return {};
      const level = count <= 2 ? 1 : count <= 4 ? 2 : count <= 6 ? 3 : 4;
      return { className: `density-${level}` };
    },
    [currentView, dayDensityMap]
  );

  /**
   * onRangeChange riceve formati diversi a seconda della vista:
   * - Month/Week: { start: Date, end: Date }
   * - Day: Date[]
   * Normalizziamo sempre a { start, end }.
   */
  const handleRangeChange = useCallback(
    (range: Date[] | { start: Date; end: Date }) => {
      if (Array.isArray(range)) {
        onRangeChange({ start: range[0], end: range[range.length - 1] });
      } else {
        onRangeChange(range);
      }
    },
    [onRangeChange]
  );

  /** D&D: evento trascinato in un nuovo slot */
  const handleEventDrop = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: string | Date; end: string | Date }) => {
      onEventDrop({
        event,
        start: new Date(start),
        end: new Date(end),
      });
    },
    [onEventDrop]
  );

  /** D&D: evento ridimensionato (resize bordo inferiore) */
  const handleEventResize = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: string | Date; end: string | Date }) => {
      onEventResize({
        event,
        start: new Date(start),
        end: new Date(end),
      });
    },
    [onEventResize]
  );

  return (
    <ViewProvider view={currentView}>
    <QuickActionProvider onQuickAction={onQuickAction}>
      <DnDCalendar
        localizer={localizer}
        events={calendarEvents}
        date={currentDate}
        view={currentView}
        onNavigate={setCurrentDate}
        onView={setCurrentView}
        views={[Views.MONTH, Views.WEEK, Views.DAY]}
        selectable
        resizable
        draggableAccessor={(event: CalendarEvent) => !event._isTodo}
        resizableAccessor={(event: CalendarEvent) => !event._isTodo}
        onSelectSlot={onSelectSlot}
        onSelectEvent={onSelectEvent}
        onRangeChange={handleRangeChange}
        onEventDrop={handleEventDrop}
        onEventResize={handleEventResize}
        eventPropGetter={eventPropGetter}
        dayPropGetter={dayPropGetter}
        tooltipAccessor={() => ""}
        messages={italianMessages}
        components={{
          toolbar: CustomToolbar,
          event: CustomEvent,
        }}
        step={30}
        timeslots={2}
        min={new Date(0, 0, 0, 6, 0)}
        max={new Date(0, 0, 0, 22, 0)}
        scrollToTime={new Date(0, 0, 0, 7, 0)}
        popup
        style={{ minHeight: "calc(100vh - 280px)" }}
      />
    </QuickActionProvider>
    </ViewProvider>
  );
}
