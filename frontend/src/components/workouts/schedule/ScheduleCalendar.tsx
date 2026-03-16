"use client";

import { useMemo, useRef, useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { ScheduleSlotCard } from "./ScheduleSlotCard";
import type { ScheduleSlot } from "@/types/api";

const GIORNO_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] as const;
const MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"] as const;
const DRAG_MIME = "application/slot-id";

interface WeekRow {
  weekNumber: number;
  monday: Date;
  label: string;
  days: { date: Date; dateStr: string; slots: ScheduleSlot[] }[];
  isCurrent: boolean;
  isPast: boolean;
}

function getMonday(d: Date): Date {
  const result = new Date(d);
  const day = result.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  result.setDate(result.getDate() + diff);
  result.setHours(0, 0, 0, 0);
  return result;
}

function dateToStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

interface ScheduleCalendarProps {
  slots: ScheduleSlot[];
  onComplete: (slotId: number) => void;
  onSkip: (slotId: number) => void;
  onDelete: (slotId: number) => void;
  onSlotClick: (slot: ScheduleSlot) => void;
  onMove?: (slotId: number, newDate: string) => void;
  onReopen?: (slotId: number) => void;
}

export function ScheduleCalendar({
  slots,
  onComplete,
  onSkip,
  onDelete,
  onSlotClick,
  onMove,
  onReopen,
}: ScheduleCalendarProps) {
  const todayStr = useMemo(() => dateToStr(new Date()), []);
  // 0=Mon..6=Sun for today column highlight
  const todayDayIndex = useMemo(() => {
    const d = new Date().getDay();
    return d === 0 ? 6 : d - 1;
  }, []);
  const scrollTargetRef = useRef<HTMLTableRowElement>(null);
  const [dragOverDate, setDragOverDate] = useState<string | null>(null);

  // Build a slotId→date lookup for preventing no-op drops
  const slotDateMap = useMemo(() => {
    const map = new Map<number, string>();
    for (const s of slots) map.set(s.id, s.data_pianificata);
    return map;
  }, [slots]);

  const handleDragOver = useCallback(
    (e: React.DragEvent, dateStr: string) => {
      if (!e.dataTransfer.types.includes(DRAG_MIME)) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverDate(dateStr);
    },
    [],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent, dateStr: string) => {
      e.preventDefault();
      setDragOverDate(null);
      const slotId = Number(e.dataTransfer.getData(DRAG_MIME));
      if (!slotId || !onMove) return;

      // Don't move to same date
      if (slotDateMap.get(slotId) === dateStr) return;

      onMove(slotId, dateStr);
      toast.success("Sessione spostata");
    },
    [onMove, slotDateMap],
  );

  const handleDragLeave = useCallback(
    (e: React.DragEvent) => {
      // Only clear if leaving the cell (not entering a child element)
      const related = e.relatedTarget as Node | null;
      if (related && (e.currentTarget as Node).contains(related)) return;
      setDragOverDate(null);
    },
    [],
  );

  const weeks: WeekRow[] = useMemo(() => {
    if (slots.length === 0) return [];

    // Group slots by date
    const slotsByDate = new Map<string, ScheduleSlot[]>();
    for (const s of slots) {
      const arr = slotsByDate.get(s.data_pianificata) ?? [];
      arr.push(s);
      slotsByDate.set(s.data_pianificata, arr);
    }

    // Collect unique week mondays
    const weekMondaySet = new Set<string>();
    for (const s of slots) {
      const d = new Date(s.data_pianificata + "T00:00:00");
      weekMondaySet.add(dateToStr(getMonday(d)));
    }
    const sortedMondays = [...weekMondaySet].sort();

    const rows = sortedMondays.map((mondayStr, idx): WeekRow => {
      const monday = new Date(mondayStr + "T00:00:00");
      const sunday = new Date(monday);
      sunday.setDate(sunday.getDate() + 6);
      const sundayStr = dateToStr(sunday);

      // Week label: "10–16 mar" or "28 feb – 6 mar"
      const startMonth = MESI[monday.getMonth()];
      const endMonth = MESI[sunday.getMonth()];
      const label =
        startMonth === endMonth
          ? `${monday.getDate()}–${sunday.getDate()} ${endMonth}`
          : `${monday.getDate()} ${startMonth} – ${sunday.getDate()} ${endMonth}`;

      const days = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(monday);
        d.setDate(d.getDate() + i);
        const ds = dateToStr(d);
        return { date: d, dateStr: ds, slots: slotsByDate.get(ds) ?? [] };
      });

      return {
        weekNumber: idx + 1,
        monday,
        label,
        days,
        isCurrent: mondayStr <= todayStr && todayStr <= sundayStr,
        isPast: sundayStr < todayStr,
      };
    });

    // Fallback: if no week contains today, mark the first future week
    if (!rows.some((w) => w.isCurrent)) {
      const firstFuture = rows.find((w) => !w.isPast);
      if (firstFuture) firstFuture.isCurrent = true;
    }

    return rows;
  }, [slots, todayStr]);

  // Auto-scroll to current/target week on mount
  useEffect(() => {
    const el = scrollTargetRef.current;
    if (el) {
      requestAnimationFrame(() => {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    }
  }, [weeks.length]);

  if (weeks.length === 0) return null;

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full border-collapse text-sm">
        {/* Sticky header */}
        <thead className="sticky top-0 z-10">
          <tr>
            <th className="w-[100px] min-w-[100px] border-b border-r bg-muted/50 px-2 py-2.5 text-left text-xs font-medium text-muted-foreground">
              Settimana
            </th>
            {GIORNO_LABELS.map((g, i) => (
              <th
                key={g}
                className={`min-w-[110px] border-b px-1 py-2.5 text-center text-xs font-medium ${
                  i === todayDayIndex
                    ? "bg-teal-100/60 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400"
                    : "bg-muted/50 text-muted-foreground"
                }`}
              >
                {g}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {weeks.map((week) => (
            <tr
              key={week.weekNumber}
              ref={week.isCurrent ? scrollTargetRef : undefined}
              className={
                week.isCurrent
                  ? "bg-teal-50/60 dark:bg-teal-950/20"
                  : week.isPast
                    ? "bg-muted/15"
                    : ""
              }
            >
              {/* Week label cell */}
              <td
                className={`border-b border-r px-2 py-1.5 align-top ${
                  week.isCurrent ? "border-l-[3px] border-l-teal-500" : ""
                }`}
              >
                <div className="flex flex-col gap-0.5">
                  <span
                    className={`text-xs font-semibold ${
                      week.isCurrent
                        ? "text-teal-700 dark:text-teal-400"
                        : week.isPast
                          ? "text-muted-foreground"
                          : "text-foreground"
                    }`}
                  >
                    S. {week.weekNumber}
                  </span>
                  <span className="text-[10px] leading-tight text-muted-foreground">
                    {week.label}
                  </span>
                </div>
              </td>

              {/* Day cells — droppable */}
              {week.days.map((day, dayIdx) => {
                const isToday = day.dateStr === todayStr;
                const isPastDay = day.dateStr < todayStr;
                const isTodayColumn = dayIdx === todayDayIndex && !isToday;
                const hasSlots = day.slots.length > 0;
                const isDragOver = dragOverDate === day.dateStr;

                return (
                  <td
                    key={day.dateStr}
                    onDragOver={(e) => handleDragOver(e, day.dateStr)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, day.dateStr)}
                    className={`border-b px-1 py-1 align-top transition-colors ${
                      isDragOver
                        ? "bg-teal-100/70 dark:bg-teal-900/40 ring-2 ring-inset ring-teal-400"
                        : isToday
                          ? "bg-teal-100/50 dark:bg-teal-900/30"
                          : isTodayColumn
                            ? "bg-teal-50/30 dark:bg-teal-950/10"
                            : ""
                    }`}
                  >
                    {/* Day number */}
                    <div
                      className={`mb-0.5 text-right text-[10px] ${
                        isToday
                          ? "font-bold text-teal-700 dark:text-teal-400"
                          : hasSlots
                            ? "text-muted-foreground"
                            : "text-muted-foreground/40"
                      }`}
                    >
                      {day.date.getDate()}
                    </div>

                    {/* Slot cards or rest indicator */}
                    {hasSlots ? (
                      <div className="space-y-1">
                        {day.slots.map((slot) => (
                          <ScheduleSlotCard
                            key={slot.id}
                            slot={slot}
                            isToday={isToday}
                            isPast={isPastDay}
                            onComplete={onComplete}
                            onSkip={onSkip}
                            onDelete={onDelete}
                            onReopen={onReopen}
                            onClick={onSlotClick}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center py-1">
                        <span className="text-[10px] text-muted-foreground/25">—</span>
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
