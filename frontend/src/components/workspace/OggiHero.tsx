"use client";

import type { PreFlightStatus } from "@/components/workspace/OggiTimeline";
import {
  surfaceRoleClassName,
  type SurfaceTone,
} from "@/components/ui/surface-role";
import { cn } from "@/lib/utils";
import { getGreeting } from "@/lib/dashboard-helpers";
import { AnalogClock } from "@/components/workspace/AnalogClock";
import type { SessionPrepItem, SessionPrepResponse } from "@/types/api";

const TIME_FMT = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });
const DATE_FMT = new Intl.DateTimeFormat("it-IT", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

function getReferenceDate(value: string | number | Date | null | undefined): Date {
  const nextDate = value ? new Date(value) : new Date();
  return Number.isNaN(nextDate.getTime()) ? new Date() : nextDate;
}

function getSessionTimeLabel(startsAt: string): string {
  return TIME_FMT.format(getReferenceDate(startsAt));
}

function getFocusBrief({
  prep,
  focusSession,
  focusStatus,
}: {
  prep: SessionPrepResponse;
  focusSession: SessionPrepItem | null;
  focusStatus: PreFlightStatus | null;
}): { tone: SurfaceTone; lead: string; detail: string | null } {
  if (!focusSession) {
    if (prep.total_sessions > 0) {
      return {
        tone: "neutral",
        lead: "Seleziona una seduta per aprire il focus operativo",
        detail: "La timeline resta il punto di ingresso per preparazione e verifiche pre-seduta.",
      };
    }
    if (prep.non_client_events.length > 0) {
      return {
        tone: "neutral",
        lead: "Nessuna seduta PT da preparare oggi",
        detail:
          prep.non_client_events.length === 1
            ? "Resta un solo slot interno in agenda."
            : `Restano ${prep.non_client_events.length} slot interni in agenda.`,
      };
    }
    return {
      tone: "neutral",
      lead: "Nessuna seduta PT in agenda oggi",
      detail: "Il workspace resta libero per pianificazione, follow-up o attivita' interne.",
    };
  }

  const timeLabel = getSessionTimeLabel(focusSession.starts_at);

  if (!focusSession.client_id) {
    return {
      tone: "neutral",
      lead: `Focus interno alle ${timeLabel}`,
      detail:
        focusSession.event_title ??
        focusSession.event_notes?.trim() ??
        "Impegno interno in agenda.",
    };
  }

  const name = focusSession.client_name ?? "Seduta cliente";

  if (focusStatus === "blocked") {
    return {
      tone: "red",
      lead: `${name} alle ${timeLabel}: sblocco contrattuale richiesto`,
      detail: "I crediti risultano esauriti: chiarisci il contratto prima della seduta.",
    };
  }

  if (focusStatus === "risk") {
    return {
      tone: "red",
      lead: `${name} alle ${timeLabel}: verifica clinica prima della seduta`,
      detail:
        focusSession.clinical_alerts.length === 1
          ? "E' presente un alert clinico da controllare."
          : `Sono presenti ${focusSession.clinical_alerts.length} alert clinici da controllare.`,
    };
  }

  if (focusStatus === "incomplete") {
    const pendingChecks = focusSession.health_checks.filter((check) => check.status !== "ok").length;
    return {
      tone: "amber",
      lead: `${name} alle ${timeLabel}: check pre-seduta da completare`,
      detail:
        pendingChecks === 1
          ? "Resta un controllo aperto prima della seduta."
          : `Restano ${pendingChecks} controlli aperti prima della seduta.`,
    };
  }

  if (focusStatus === "ready") {
    return {
      tone: "teal",
      lead: `${name} alle ${timeLabel} e' pronto`,
      detail: focusSession.active_plan_name
        ? `Scheda attiva: ${focusSession.active_plan_name}.`
        : "Nessun blocco immediato rilevato per la seduta.",
    };
  }

  return {
    tone: "neutral",
    lead: `${name} alle ${timeLabel}`,
    detail: "Focus aperto sulla seduta selezionata.",
  };
}

export interface OggiHeroProps {
  prep: SessionPrepResponse;
  attentionCount: number;
  readyCount: number;
  internalCount: number;
  focusSession: SessionPrepItem | null;
  focusStatus: PreFlightStatus | null;
  lastUpdatedAt?: number | null;
  isRefreshing?: boolean;
  className?: string;
}

export function OggiHero({
  prep,
  attentionCount,
  readyCount,
  internalCount: _internalCount,
  focusSession,
  focusStatus,
  lastUpdatedAt: _lastUpdatedAt,
  isRefreshing: _isRefreshing = false,
  className,
}: OggiHeroProps) {
  const now = getReferenceDate(prep.current_time);
  const nowMs = now.getTime();
  const { lead, detail } = getFocusBrief({
    prep,
    focusSession,
    focusStatus,
  });

  // Prossima seduta futura per countdown
  const nextSession = [...prep.sessions, ...prep.non_client_events]
    .filter((s) => new Date(s.starts_at).getTime() > nowMs)
    .sort((a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime())[0] ?? null;


  return (
    <section aria-label="Preparazione sedute di oggi" className={cn("oggi-hero-mesh", className)}>
      <div
        className={surfaceRoleClassName(
          { role: "page", tone: "neutral" },
          "oggi-command-bar px-6 py-8 sm:px-10 sm:py-10",
        )}
      >
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 flex-1">
            {/* Heading — semantically correct h1 for the page */}
            <h1 className="oggi-section-label flex items-center gap-2 text-[11px] font-bold uppercase text-muted-foreground/60">
              <span>Oggi</span>
              <span className="text-primary/40" aria-hidden="true">|</span>
              <span className="text-primary/70">Preparazione sedute</span>
            </h1>

            {/* Row 1: Clock + Greeting + Date */}
            <div className="mt-5 flex items-center gap-6 sm:mt-6">
              <AnalogClock
                nextSessionAt={nextSession?.starts_at}
                nextSessionName={nextSession?.client_name ?? nextSession?.event_title}
              />
              <div className="min-w-0">
                <p className="oggi-title-gradient pb-1 text-[1.9rem] font-black leading-[1.25] tracking-tight sm:text-[2.3rem]" aria-hidden="true">
                  {getGreeting()}
                </p>
                <p className="mt-1.5 text-base font-medium capitalize text-foreground/50 sm:text-lg">
                  {DATE_FMT.format(now)}
                </p>
              </div>
            </div>

            {/* Row 2: Briefing lead — operational action with breathing room */}
            <div className="oggi-hero-divider mt-6" aria-hidden="true" />
            <p className="mt-5 max-w-xl text-base font-bold leading-relaxed text-foreground sm:text-lg">
              {lead}
            </p>
            {detail ? (
              <p className="mt-1.5 max-w-lg text-[13px] leading-relaxed text-muted-foreground/70">
                {detail}
              </p>
            ) : null}
          </div>

          {/* KPI stat block — enterprise gradient numbers */}
          <div className="flex shrink-0 items-center gap-6 sm:flex-col sm:items-end sm:gap-6">
            {/* Total sessions */}
            <div className="text-right">
              <p className={cn("text-[2rem] font-black tabular-nums leading-none tracking-tight sm:text-[2.4rem]", "oggi-kpi-value")}>
                {prep.total_sessions}
              </p>
              <p className="mt-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground/60">
                {prep.total_sessions === 1 ? "seduta" : "sedute"}
              </p>
            </div>

            {/* Attention / Ready — conditional KPI, quiet foreground */}
            {attentionCount > 0 ? (
              <div className="text-right">
                <p className="oggi-kpi-value text-[2rem] font-black tabular-nums leading-none tracking-tight sm:text-[2.4rem]">
                  {attentionCount}
                </p>
                <p className="mt-1.5 flex items-center justify-end gap-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground/60">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500" aria-hidden="true" />
                  da verificare
                </p>
              </div>
            ) : readyCount > 0 ? (
              <div className="text-right">
                <p className="oggi-kpi-value text-[2rem] font-black tabular-nums leading-none tracking-tight sm:text-[2.4rem]">
                  {readyCount}
                </p>
                <p className="mt-1.5 flex items-center justify-end gap-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-muted-foreground/60">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
                  {readyCount === 1 ? "pronta" : "pronte"}
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

export function OggiHeroSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={surfaceRoleClassName(
        { role: "page", tone: "neutral" },
        cn("oggi-command-bar px-6 py-8 sm:px-10 sm:py-10", className),
      )}
    >
      <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1 space-y-4">
          <div className="h-3 w-40 rounded bg-muted/40" />
          <div className="flex items-center gap-6">
            <div className="h-[101px] w-[101px] rounded-[25px] bg-muted/20 sm:h-[116px] sm:w-[116px] sm:rounded-[29px]" />
            <div className="space-y-2.5">
              <div className="h-7 w-52 rounded-lg bg-muted/30" />
              <div className="h-4 w-36 rounded bg-muted/20" />
            </div>
          </div>
          <div className="h-[1.5px] w-12 rounded bg-muted/30" />
          <div className="space-y-2">
            <div className="h-5 w-80 rounded bg-muted/30" />
            <div className="h-3.5 w-64 rounded bg-muted/20" />
          </div>
        </div>
        <div className="flex items-center gap-6 sm:flex-col sm:items-end sm:gap-6">
          <div className="space-y-1.5 text-right">
            <div className="ml-auto h-8 w-12 rounded-lg bg-muted/30" />
            <div className="ml-auto h-2.5 w-14 rounded bg-muted/20" />
          </div>
          <div className="space-y-1.5 text-right">
            <div className="ml-auto h-8 w-8 rounded-lg bg-muted/25" />
            <div className="ml-auto h-2.5 w-16 rounded bg-muted/20" />
          </div>
        </div>
      </div>
    </div>
  );
}
