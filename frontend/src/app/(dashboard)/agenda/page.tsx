// src/app/(dashboard)/agenda/page.tsx
"use client";

/**
 * Pagina Agenda — calendario interattivo con react-big-calendar.
 *
 * Il PT vive in questa schermata:
 * - Vista settimanale default, slot da 30 min (06:00-22:00)
 * - Click slot vuoto -> scelta Evento o Promemoria
 * - Click evento -> modifica via Sheet
 * - Promemoria overlay come all-day events
 * - Color coding per categoria (PT=blu, SALA=grigio, ecc.)
 */

import { useState, useCallback, useMemo, useEffect } from "react";
import { usePageReveal } from "@/lib/page-reveal";
import { format, startOfWeek, endOfWeek, endOfDay, startOfMonth, endOfMonth, subMonths, addMonths } from "date-fns";
import { it } from "date-fns/locale";
import { Plus, CalendarDays, AlertTriangle, Loader2, StickyNote } from "lucide-react";
import type { SlotInfo } from "react-big-calendar";

import { Button } from "@/components/ui/button";
import { AgendaCalendar } from "@/components/agenda/AgendaCalendar";
import { EventSheet } from "@/components/agenda/EventSheet";
import { DeleteEventDialog } from "@/components/agenda/DeleteEventDialog";
import { SlotChoiceDialog } from "@/components/agenda/SlotChoiceDialog";
import { TodoQuickCreateDialog } from "@/components/agenda/TodoQuickCreateDialog";
import { FilterBar } from "@/components/agenda/FilterBar";
import { RangeStatsBar } from "@/components/agenda/RangeStatsBar";
import { CalendarSkeleton } from "@/components/agenda/CalendarSkeleton";
import { useEvents, useUpdateEvent } from "@/hooks/useAgenda";
import { useTodos } from "@/hooks/useTodos";
import type { CalendarEvent } from "@/components/agenda/calendar-setup";
import { EVENT_CATEGORIES, EVENT_STATUSES } from "@/types/api";
import { toISOLocal } from "@/lib/format";
import { PageVideoGuide } from "@/components/guide/PageVideoGuide";

/** Range iniziale: mese corrente +/- 1 mese di buffer. */
function getInitialRange() {
  const now = new Date();
  return {
    start: startOfMonth(subMonths(now, 1)),
    end: endOfMonth(addMonths(now, 1)),
  };
}

/** Legge deep-link iniziale una sola volta per evitare setState in useEffect. */
function getInitialDeepLinkState() {
  if (typeof window === "undefined") {
    return { openFromDeepLink: false, defaultClientId: undefined as number | undefined };
  }
  const params = new URLSearchParams(window.location.search);
  if (params.get("newEvent") !== "1") {
    return { openFromDeepLink: false, defaultClientId: undefined as number | undefined };
  }
  const rawClientId = params.get("clientId");
  const parsedClientId = rawClientId ? Number(rawClientId) : undefined;
  return {
    openFromDeepLink: true,
    defaultClientId: Number.isFinite(parsedClientId) ? parsedClientId : undefined,
  };
}

export default function AgendaPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const [initialDeepLink] = useState(getInitialDeepLinkState);
  const [dateRange, setDateRange] = useState(getInitialRange);
  const [sheetOpen, setSheetOpen] = useState(() => initialDeepLink.openFromDeepLink);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [slotStart, setSlotStart] = useState<Date | undefined>();
  const [slotEnd, setSlotEnd] = useState<Date | undefined>();
  const [defaultClientId] = useState<number | undefined>(() => initialDeepLink.defaultClientId);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [choiceOpen, setChoiceOpen] = useState(false);
  const [todoCreateOpen, setTodoCreateOpen] = useState(false);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(() => new Set(EVENT_CATEGORIES));
  const [activeStatuses, setActiveStatuses] = useState<Set<string>>(() => new Set(EVENT_STATUSES));
  const [visibleRange, setVisibleRange] = useState<{ start: Date; end: Date }>(() => {
    const now = new Date();
    return { start: startOfWeek(now, { locale: it }), end: endOfWeek(now, { locale: it }) };
  });

  // Deep-link cleanup
  useEffect(() => {
    if (!initialDeepLink.openFromDeepLink) return;
    window.history.replaceState(window.history.state, "", window.location.pathname);
  }, [initialDeepLink.openFromDeepLink]);

  // ── Query: eventi nel range ──
  const queryParams = useMemo(
    () => ({ start: format(dateRange.start, "yyyy-MM-dd"), end: format(dateRange.end, "yyyy-MM-dd") }),
    [dateRange]
  );
  const { data: eventsData, isLoading, isError, isFetching, refetch } = useEvents(queryParams);
  const events = useMemo(() => eventsData?.items ?? [], [eventsData]);

  // ── Query: todos con data (per overlay calendario + badge header) ──
  const { data: todosData } = useTodos();
  const allTodos = useMemo(() => todosData?.items ?? [], [todosData]);

  const visibleTodos = useMemo(() => {
    const startStr = format(visibleRange.start, "yyyy-MM-dd");
    const endStr = format(visibleRange.end, "yyyy-MM-dd");
    return allTodos.filter(
      (t) => t.data_scadenza && t.data_scadenza >= startStr && t.data_scadenza <= endStr
    );
  }, [allTodos, visibleRange]);

  // ── KPI promemoria per badge header (azione 5) ──
  const todoStats = useMemo(() => {
    const today = format(new Date(), "yyyy-MM-dd");
    let overdue = 0;
    let dueToday = 0;
    for (const t of allTodos) {
      if (t.completato || !t.data_scadenza) continue;
      if (t.data_scadenza < today) overdue++;
      else if (t.data_scadenza === today) dueToday++;
    }
    return { overdue, dueToday };
  }, [allTodos]);

  // ── Filtering pipeline ──
  const calendarEvents = useMemo(
    () => events.filter((e) => activeCategories.has(e.categoria) && activeStatuses.has(e.stato)),
    [events, activeCategories, activeStatuses]
  );

  const visibleEvents = useMemo(
    () => events.filter(
      (e) => e.data_inizio >= visibleRange.start && e.data_inizio <= visibleRange.end
        && activeCategories.has(e.categoria) && activeStatuses.has(e.stato)
    ),
    [events, visibleRange, activeCategories, activeStatuses]
  );

  const handleToggleCategory = useCallback((cat: string) => {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  }, []);

  const handleToggleStatus = useCallback((stato: string) => {
    setActiveStatuses((prev) => {
      const next = new Set(prev);
      next.has(stato) ? next.delete(stato) : next.add(stato);
      return next;
    });
  }, []);

  // ── KPI ──
  const rangeStats = useMemo(() => {
    const completed = visibleEvents.filter((e) => e.stato === "Completato").length;
    const scheduled = visibleEvents.filter((e) => e.stato === "Programmato").length;
    const cancelled = visibleEvents.filter((e) => e.stato === "Cancellato").length;
    const denominator = completed + cancelled + scheduled;
    const rate = denominator > 0 ? Math.round((completed / denominator) * 100) : 0;
    return { total: visibleEvents.length, completed, scheduled, rate };
  }, [visibleEvents]);

  const rangeLabel = useMemo(() => {
    const ms = visibleRange.end.getTime() - visibleRange.start.getTime();
    const days = Math.round(ms / (1000 * 60 * 60 * 24));
    if (days <= 1) return format(visibleRange.start, "EEEE d MMMM", { locale: it });
    if (days <= 7) {
      const sameMonth = visibleRange.start.getMonth() === visibleRange.end.getMonth();
      return sameMonth
        ? `${format(visibleRange.start, "d", { locale: it })}-${format(visibleRange.end, "d MMM", { locale: it })}`
        : `${format(visibleRange.start, "d MMM", { locale: it })} - ${format(visibleRange.end, "d MMM", { locale: it })}`;
    }
    const mid = new Date(visibleRange.start.getTime() + ms / 2);
    return format(mid, "MMMM yyyy", { locale: it });
  }, [visibleRange]);

  // ── Mutations ──
  const updateEvent = useUpdateEvent();

  const handleQuickAction = useCallback(
    (eventId: number, stato: string) => { updateEvent.mutate({ id: eventId, stato }); },
    [updateEvent]
  );

  // ── Handlers ──
  const handleNewEvent = () => {
    setSelectedEvent(null);
    setSlotStart(undefined);
    setSlotEnd(undefined);
    setSheetOpen(true);
  };

  const handleSelectSlot = useCallback((slotInfo: SlotInfo) => {
    setSelectedEvent(null);
    setSlotStart(slotInfo.start);
    setSlotEnd(new Date(slotInfo.start.getTime() + 60 * 60 * 1000));
    setChoiceOpen(true);
  }, []);

  const handleChooseEvent = useCallback(() => { setChoiceOpen(false); setSheetOpen(true); }, []);
  const handleChoosePromemoria = useCallback(() => { setChoiceOpen(false); setTodoCreateOpen(true); }, []);

  const handleSelectEvent = useCallback((event: CalendarEvent) => {
    if (event._isTodo) return;
    setSelectedEvent(event);
    setSlotStart(undefined);
    setSlotEnd(undefined);
    setSheetOpen(true);
  }, []);

  const handleDeleteRequest = () => { setSheetOpen(false); setDeleteOpen(true); };

  const handleRangeChange = useCallback((range: { start: Date; end: Date }) => {
    const adjustedEnd = endOfDay(range.end);
    setVisibleRange({ start: range.start, end: adjustedEnd });
    setDateRange((prev) => {
      if (range.start >= prev.start && range.end <= prev.end) return prev;
      return {
        start: startOfMonth(subMonths(range.start, 1)),
        end: endOfMonth(addMonths(range.end, 1)),
      };
    });
  }, []);

  const handleEventDrop = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: Date; end: Date }) => {
      updateEvent.mutate({ id: event.id, data_inizio: toISOLocal(start), data_fine: toISOLocal(end) });
    },
    [updateEvent]
  );

  const handleEventResize = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: Date; end: Date }) => {
      updateEvent.mutate({ id: event.id, data_inizio: toISOLocal(start), data_fine: toISOLocal(end) });
    },
    [updateEvent]
  );

  const hasFilters = activeCategories.size < EVENT_CATEGORIES.length || activeStatuses.size < EVENT_STATUSES.length;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div data-guide="agenda-header" className={revealClass(0, "flex items-center justify-between")} style={revealStyle(0)}>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/40 dark:to-blue-800/30">
            <CalendarDays className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">Agenda</h1>
              {/* Badge promemoria urgenti */}
              {todoStats.overdue > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-semibold text-red-700 dark:bg-red-900/40 dark:text-red-300">
                  <StickyNote className="h-3 w-3" aria-hidden="true" />
                  {todoStats.overdue} scadut{todoStats.overdue === 1 ? "o" : "i"}
                </span>
              )}
              {todoStats.dueToday > 0 && (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                  <StickyNote className="h-3 w-3" aria-hidden="true" />
                  {todoStats.dueToday} oggi
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {visibleEvents.length} event{visibleEvents.length !== 1 ? "i" : "o"} · {rangeLabel}
              {hasFilters ? <span className="text-muted-foreground/60"> (filtro attivo)</span> : null}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <PageVideoGuide />
          <Button
            data-guide="agenda-new-button"
            onClick={handleNewEvent}
            className="bg-blue-600 text-white shadow-sm hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            Nuovo Evento
          </Button>
        </div>
      </div>

      {/* ── Filtri ── */}
      <div className={revealClass(50)} style={revealStyle(50)}>
        <FilterBar
          activeCategories={activeCategories}
          onToggleCategory={handleToggleCategory}
          activeStatuses={activeStatuses}
          onToggleStatus={handleToggleStatus}
        />
      </div>

      {/* ── KPI ── */}
      {!isLoading && (
        <div className={revealClass(100)} style={revealStyle(100)}>
          <RangeStatsBar stats={rangeStats} label={rangeLabel} />
        </div>
      )}

      {/* ── Calendario ── */}
      {/* NO transform-gpu: breaks DnD getBoundingClientRect in production */}
      <div>
        {isLoading && <CalendarSkeleton />}

        {isError && (
          <div className="flex items-center justify-between rounded-xl border border-destructive/50 bg-destructive/5 p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <p className="text-sm text-destructive">Errore nel caricamento degli eventi.</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>Riprova</Button>
          </div>
        )}

        {!isLoading && !isError && (
          <div className="relative">
            {isFetching && (
              <div className="absolute inset-x-0 top-0 z-10 flex justify-center">
                <div className="rounded-b-lg bg-blue-50 px-3 py-1 shadow-sm dark:bg-blue-950/40">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500" />
                </div>
              </div>
            )}
            {calendarEvents.length === 0 && !isFetching && (
              <div className="pointer-events-none absolute inset-0 z-[5] flex items-center justify-center">
                <div className="pointer-events-auto rounded-xl border border-dashed border-blue-200 bg-white/90 px-6 py-8 text-center shadow-sm backdrop-blur-sm dark:border-blue-800/50 dark:bg-zinc-900/90">
                  <CalendarDays className="mx-auto mb-3 h-10 w-10 text-blue-400/60" />
                  <p className="text-sm font-medium text-muted-foreground">Nessun evento in questo periodo</p>
                  <p className="mt-1 text-xs text-muted-foreground/70">
                    Clicca su uno slot vuoto o premi &quot;Nuovo Evento&quot; per creare una sessione
                  </p>
                </div>
              </div>
            )}
            <AgendaCalendar
              events={calendarEvents}
              todos={visibleTodos}
              onSelectSlot={handleSelectSlot}
              onSelectEvent={handleSelectEvent}
              onRangeChange={handleRangeChange}
              onEventDrop={handleEventDrop}
              onEventResize={handleEventResize}
              onQuickAction={handleQuickAction}
            />
          </div>
        )}
      </div>

      {/* ── Dialogs & Sheets ── */}
      <EventSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        event={selectedEvent}
        defaultStart={slotStart}
        defaultEnd={slotEnd}
        defaultClientId={defaultClientId}
        onDeleteRequest={handleDeleteRequest}
      />
      <DeleteEventDialog open={deleteOpen} onOpenChange={setDeleteOpen} event={selectedEvent} />
      <SlotChoiceDialog
        open={choiceOpen}
        onOpenChange={setChoiceOpen}
        onChooseEvent={handleChooseEvent}
        onChoosePromemoria={handleChoosePromemoria}
        slotDate={slotStart}
      />
      <TodoQuickCreateDialog
        open={todoCreateOpen}
        onOpenChange={setTodoCreateOpen}
        defaultDate={slotStart}
      />
    </div>
  );
}
