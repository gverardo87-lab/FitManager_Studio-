// src/app/(dashboard)/monitoraggio/page.tsx
"use client";

/**
 * Monitoraggio — Salute Clienti.
 *
 * Readiness clinica e onboarding dei clienti del trainer.
 */

import { HeartPulse } from "lucide-react";
import { usePageReveal } from "@/lib/page-reveal";

import { SaluteClientiTab } from "@/components/monitoraggio/SaluteClientiTab";

export default function MonitoraggioPage() {
  const { revealClass, revealStyle } = usePageReveal();

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div
        className={revealClass(0, "flex items-center gap-3")}
        style={revealStyle(0)}
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-rose-100 to-rose-50 dark:from-rose-900/40 dark:to-rose-800/30">
          <HeartPulse className="h-5 w-5 text-rose-600 dark:text-rose-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Salute Clienti</h1>
          <p className="text-sm text-muted-foreground">
            Readiness clinica e onboarding
          </p>
        </div>
      </div>

      {/* Content */}
      <div
        className={revealClass(50, "rounded-xl border bg-white dark:bg-zinc-900 overflow-hidden")}
        style={revealStyle(50)}
      >
        <div className="p-4">
          <SaluteClientiTab />
        </div>
      </div>
    </div>
  );
}
