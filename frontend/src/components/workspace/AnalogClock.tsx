"use client";

/**
 * SmartWatch — orologio digitale stile Apple Watch Ultra.
 *
 * Rounded-rect con ore:minuti dominante (colon pulsante),
 * giorno + data compatta sotto. Countdown prossima seduta.
 * Aggiorna ogni 10s.
 */

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const DAY_FMT = new Intl.DateTimeFormat("it-IT", { weekday: "short" });
const DATE_SHORT_FMT = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "short" });

function formatCountdown(ms: number): string {
  const totalMin = Math.max(0, Math.floor(ms / 60_000));
  if (totalMin < 1) return "ora";
  if (totalMin < 60) return `${totalMin}min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m > 0 ? `${h}h${m}m` : `${h}h`;
}

interface SmartWatchProps {
  nextSessionAt?: string | null;
  nextSessionName?: string | null;
  className?: string;
}

export function AnalogClock({ nextSessionAt, nextSessionName, className }: SmartWatchProps) {
  const [now, setNow] = useState(new Date(0));

  useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 10_000);
    return () => window.clearInterval(id);
  }, []);

  const hydrated = now.getTime() > 0;
  const hh = hydrated ? String(now.getHours()).padStart(2, "0") : "--";
  const mm = hydrated ? String(now.getMinutes()).padStart(2, "0") : "--";
  const dayStr = hydrated ? DAY_FMT.format(now).toUpperCase().replace(".", "") : "---";
  const dateStr = hydrated ? DATE_SHORT_FMT.format(now) : "";

  // Countdown
  const nextMs = nextSessionAt ? new Date(nextSessionAt).getTime() : null;
  const deltaMs = hydrated && nextMs && !Number.isNaN(nextMs) ? nextMs - now.getTime() : null;
  const showCountdown = deltaMs !== null && deltaMs > 0;

  return (
    <div
      className={cn(
        "oggi-smartwatch relative flex shrink-0 flex-col items-center justify-center transition-opacity duration-500",
        hydrated ? "opacity-100" : "opacity-0",
        className,
      )}
      role="img"
      aria-label={hydrated ? `Orologio: ${hh}:${mm}` : "Orologio"}
    >
      {/* Time — dominant, with pulsing colon */}
      <div className="flex items-baseline tabular-nums">
        <span className="oggi-smartwatch-time text-[2.1rem] font-black leading-none tracking-tight sm:text-[2.5rem]">
          {hh}
        </span>
        <span className="oggi-smartwatch-colon oggi-smartwatch-time mx-[1px] text-[1.8rem] font-black leading-none sm:text-[2.2rem]">
          :
        </span>
        <span className="oggi-smartwatch-time text-[2.1rem] font-black leading-none tracking-tight sm:text-[2.5rem]">
          {mm}
        </span>
      </div>

      {/* Countdown or Date */}
      {showCountdown ? (
        <span className="mt-1.5 flex items-center gap-1 text-[10px] font-bold tabular-nums text-primary/80 sm:text-[11px]">
          <span className="oggi-pulse-dot h-1.5 w-1.5 rounded-full bg-primary/60" />
          tra {formatCountdown(deltaMs)}
        </span>
      ) : (
        <span className="mt-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.12em] text-muted-foreground/65">
          <span className="text-primary/70">{dayStr}</span>
          <span className="h-[3px] w-[3px] rounded-full bg-primary/40" />
          <span>{dateStr}</span>
        </span>
      )}
    </div>
  );
}
