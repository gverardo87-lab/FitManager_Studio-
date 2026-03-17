"use client";

/**
 * SmartWatch — orologio digitale stile Apple Watch Ultra.
 *
 * Rounded-rect con ore:minuti dominante (colon pulsante),
 * giorno + data compatta sotto. Aggiorna ogni 10s.
 */

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const DAY_FMT = new Intl.DateTimeFormat("it-IT", { weekday: "short" });
const DATE_SHORT_FMT = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "short" });

interface SmartWatchProps {
  className?: string;
}

export function AnalogClock({ className }: SmartWatchProps) {
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

      {/* Date — compact below */}
      <span className="mt-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.12em] text-muted-foreground/65 sm:text-[12px]">
        <span className="text-primary/70">{dayStr}</span>
        <span className="h-[3px] w-[3px] rounded-full bg-primary/40" />
        <span>{dateStr}</span>
      </span>
    </div>
  );
}
