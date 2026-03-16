"use client";

import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScheduleSlotCard } from "./ScheduleSlotCard";
import type { ScheduleSlot } from "@/types/api";

const GIORNO_LABELS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"] as const;

interface WeekData {
  weekNumber: number;
  monday: Date;
  days: { date: Date; dateStr: string; slots: ScheduleSlot[] }[];
}

function getMonday(d: Date): Date {
  const result = new Date(d);
  const day = result.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  result.setDate(result.getDate() + diff);
  result.setHours(0, 0, 0, 0);
  return result;
}

function formatDateNum(d: Date): string {
  return d.getDate().toString();
}

function dateToStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

interface ScheduleCalendarProps {
  slots: ScheduleSlot[];
  currentWeekOffset: number;
  onWeekChange: (offset: number) => void;
  onComplete: (slotId: number) => void;
  onSkip: (slotId: number) => void;
  onDelete: (slotId: number) => void;
  onSlotClick: (slot: ScheduleSlot) => void;
}

export function ScheduleCalendar({
  slots,
  currentWeekOffset,
  onWeekChange,
  onComplete,
  onSkip,
  onDelete,
  onSlotClick,
}: ScheduleCalendarProps) {
  const todayStr = useMemo(() => dateToStr(new Date()), []);

  // Compute the week to display based on offset from first slot
  const { week, weekLabel, totalWeeks, currentWeekIndex } = useMemo(() => {
    if (slots.length === 0) {
      return { week: null, weekLabel: "", totalWeeks: 0, currentWeekIndex: 0 };
    }

    // Group by week
    const slotsByDate = new Map<string, ScheduleSlot[]>();
    for (const s of slots) {
      const arr = slotsByDate.get(s.data_pianificata) ?? [];
      arr.push(s);
      slotsByDate.set(s.data_pianificata, arr);
    }

    // Find all unique weeks
    const weekMondays = new Set<string>();
    for (const s of slots) {
      const d = new Date(s.data_pianificata + "T00:00:00");
      weekMondays.add(dateToStr(getMonday(d)));
    }
    const sortedWeeks = [...weekMondays].sort();
    const total = sortedWeeks.length;

    // Find which week to show based on offset
    // Default (offset=0): find current week or first future week
    let targetIdx: number;
    const todayMonday = dateToStr(getMonday(new Date()));
    const todayWeekIdx = sortedWeeks.findIndex((m) => m >= todayMonday);
    const baseIdx = todayWeekIdx >= 0 ? todayWeekIdx : total - 1;
    targetIdx = Math.max(0, Math.min(total - 1, baseIdx + currentWeekOffset));

    const mondayStr = sortedWeeks[targetIdx];
    const monday = new Date(mondayStr + "T00:00:00");

    const days = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(monday);
      d.setDate(d.getDate() + i);
      const ds = dateToStr(d);
      return { date: d, dateStr: ds, slots: slotsByDate.get(ds) ?? [] };
    });

    const weekData: WeekData = { weekNumber: targetIdx + 1, monday, days };

    // Label
    const endDate = new Date(monday);
    endDate.setDate(endDate.getDate() + 6);
    const mesi = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"];
    const label = `${monday.getDate()} ${mesi[monday.getMonth()]} — ${endDate.getDate()} ${mesi[endDate.getMonth()]} ${endDate.getFullYear()}`;

    return {
      week: weekData,
      weekLabel: label,
      totalWeeks: total,
      currentWeekIndex: targetIdx,
    };
  }, [slots, currentWeekOffset, todayStr]);

  if (!week) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* Navigation bar */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onWeekChange(currentWeekOffset - 1)}
          disabled={currentWeekIndex === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          <span className="hidden sm:inline">Prec.</span>
        </Button>
        <div className="text-center">
          <p className="text-sm font-medium">
            Settimana {week.weekNumber} di {totalWeeks}
          </p>
          <p className="text-xs text-muted-foreground">{weekLabel}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onWeekChange(currentWeekOffset + 1)}
          disabled={currentWeekIndex === totalWeeks - 1}
        >
          <span className="hidden sm:inline">Succ.</span>
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {/* Grid 7 columns */}
      <div className="grid grid-cols-7 gap-1.5">
        {/* Day headers */}
        {week.days.map((day, i) => {
          const isToday = day.dateStr === todayStr;
          return (
            <div
              key={day.dateStr}
              className={`text-center py-1.5 rounded-t-md text-xs font-medium ${
                isToday
                  ? "bg-teal-600 text-white"
                  : "bg-muted/50 text-muted-foreground"
              }`}
            >
              <span className="hidden sm:inline">{GIORNO_LABELS[i]} </span>
              {formatDateNum(day.date)}
            </div>
          );
        })}

        {/* Slot cells */}
        {week.days.map((day) => {
          const isToday = day.dateStr === todayStr;
          const isPast = day.dateStr < todayStr;
          return (
            <div
              key={`cell-${day.dateStr}`}
              className={`min-h-[80px] sm:min-h-[100px] rounded-b-md border p-1 space-y-1 ${
                isToday
                  ? "border-teal-300 bg-teal-50/50 dark:bg-teal-950/20"
                  : isPast
                    ? "border-zinc-100 bg-zinc-50/50 dark:bg-zinc-900/50"
                    : "border-zinc-200 dark:border-zinc-800"
              }`}
            >
              {day.slots.map((slot) => (
                <ScheduleSlotCard
                  key={slot.id}
                  slot={slot}
                  isToday={isToday}
                  isPast={isPast}
                  onComplete={onComplete}
                  onSkip={onSkip}
                  onDelete={onDelete}
                  onClick={onSlotClick}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
