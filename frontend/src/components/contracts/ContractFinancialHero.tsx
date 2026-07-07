// src/components/contracts/ContractFinancialHero.tsx
"use client";

/**
 * Hero finanziaria del contratto — posizione sempre visibile, profondità dietro disclosure.
 *
 * F2 / D-DISCLOSURE (ratifica founder 2026-07-06, SPEC_G8.4 §F2 — lista VINCOLANTE):
 * - SEMPRE visibili (mai dietro toggle): Valore · Incassato netto con sub-label «lordo X · −Y»
 *   quando c'è rimborso (D-1 emendata, mai un netto nudo) · Rate Pagate · Residuo (+ conteggio
 *   rate scadute) · Da Rateizzare quando il piano NON è coperto (warning) · banner amber
 *   prenotate-non-erogate (unico segnale dell'azione recuperabile finché G8.5 non shippa).
 * - Collassabili dietro «Mostra dettaglio»: Acconto · Da Rateizzare se piano completo (informativa) ·
 *   riga Crediti Sedute (4 card).
 *
 * F6 / D-COLORE: il colore è SOLO valenza (emerald=positivo, amber=attenzione, red=critico);
 * i tint decorativi di categoria (violet/blue/indigo) sono neutralizzati a zinc — l'identità
 * della card la dà la label, non il colore.
 */

import { useState } from "react";
import {
  Wallet,
  TrendingUp,
  CircleDollarSign,
  Receipt,
  HandCoins,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Dumbbell,
  Clock,
  Target,
  CalendarCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { formatCurrency } from "@/lib/format";
import type { ContractWithRates } from "@/types/api";

// F6: token neutri per le card senza valenza (identità = label, mai colore)
const NEUTRAL_ICON = "text-zinc-600 dark:text-zinc-400";
const NEUTRAL_ICON_BG = "bg-zinc-100 dark:bg-zinc-800";

// ════════════════════════════════════════════════════════════
// Main Component
// ════════════════════════════════════════════════════════════

export function ContractFinancialHero({ contract }: { contract: ContractWithRates }) {
  const [showDetail, setShowDetail] = useState(false);

  const totale = contract.prezzo_totale ?? 0;
  const acconto = contract.acconto;
  const versato = contract.totale_versato;
  const rimborsato = contract.totale_rimborsato ?? 0;
  const netto = contract.netto_incassato;  // SSoT backend (G8.4 F1.a) — MAI ricalcolato client-side
  const haRimborso = rimborsato > 0.009;
  const residuo = contract.residuo;
  const nettoPct = totale > 0 ? Math.round((netto / totale) * 100) : 0;
  const ratePagate = contract.rate_pagate;
  const rateTotali = contract.rate_totali;
  const rateScadute = contract.rate_scadute;
  const daRateizzare = contract.importo_da_rateizzare;
  const pianoCoperto = contract.piano_allineato;
  const creditiTotali = contract.crediti_totali ?? 0;
  const programmate = contract.sedute_programmate;
  const completate = contract.sedute_completate;
  const creditiResidui = contract.crediti_residui;

  // Da Rateizzare è un WARNING quando il piano non copre il residuo → always-visible;
  // a piano completo è pura conferma informativa → dietro disclosure.
  const showDaRateizzare = !pianoCoperto || showDetail;

  return (
    <div data-guide="contratto-hero-finanziario" className="rounded-xl border bg-gradient-to-br from-zinc-50 to-zinc-100/50 p-5 dark:from-zinc-900 dark:to-zinc-800/50">
      <div className="space-y-3">
        {/* ── Card denaro: griglia unica che fluisce (collassata: Valore·Netto·Rate·Residuo) ── */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <KpiCard
            icon={<Wallet className={`h-4 w-4 ${NEUTRAL_ICON}`} />}
            iconBg={NEUTRAL_ICON_BG}
            label="Valore Contratto"
            value={formatCurrency(totale)}
          />
          {showDetail ? (
            <KpiCard
              icon={<HandCoins className={`h-4 w-4 ${NEUTRAL_ICON}`} />}
              iconBg={NEUTRAL_ICON_BG}
              label="Acconto"
              value={acconto > 0 ? formatCurrency(acconto) : "—"}
              valueClass={acconto > 0 ? undefined : "text-muted-foreground"}
            />
          ) : null}
          {showDaRateizzare ? (
            <KpiCard
              icon={pianoCoperto
                ? <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                : <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
              }
              iconBg={pianoCoperto
                ? "bg-emerald-100 dark:bg-emerald-900/30"
                : "bg-amber-100 dark:bg-amber-900/30"
              }
              label="Da Rateizzare"
              value={pianoCoperto ? "Piano completo" : formatCurrency(daRateizzare)}
              valueClass={pianoCoperto
                ? "text-emerald-700 dark:text-emerald-400 text-sm"
                : "text-amber-700 dark:text-amber-400"
              }
            />
          ) : null}

          {/* Incassato netto — card più alta con progress; mai un netto nudo (D-1/L2) */}
          <div className="flex flex-col gap-2 rounded-lg border bg-white p-3 shadow-sm dark:bg-zinc-900">
            <div className="flex items-start gap-2.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <TrendingUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="min-w-0">
                <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
                  {haRimborso ? "Incassato netto" : "Versato"}
                </p>
                <p className="text-base font-bold tabular-nums tracking-tight text-emerald-700 dark:text-emerald-400">
                  {formatCurrency(netto)}
                </p>
                {haRimborso ? (
                  <p className="text-[10px] tabular-nums text-muted-foreground">
                    lordo {formatCurrency(versato)} · −{formatCurrency(rimborsato)} rimborso
                  </p>
                ) : null}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Progress value={nettoPct} className="h-1.5 flex-1" />
              <span className="text-[10px] font-semibold tabular-nums text-muted-foreground">
                {nettoPct}%
              </span>
            </div>
          </div>

          <KpiCard
            icon={<Receipt className={`h-4 w-4 ${NEUTRAL_ICON}`} />}
            iconBg={NEUTRAL_ICON_BG}
            label="Rate Pagate"
            value={rateTotali > 0 ? `${ratePagate} / ${rateTotali}` : "—"}
            valueClass={ratePagate === rateTotali && rateTotali > 0
              ? "text-emerald-700 dark:text-emerald-400"
              : undefined
            }
            subtitle={rateTotali === 0 ? "Piano non generato" : undefined}
          />

          <KpiCard
            icon={<CircleDollarSign className={`h-4 w-4 ${
              rateScadute > 0
                ? "text-red-600 dark:text-red-400"
                : "text-emerald-600 dark:text-emerald-400"
            }`} />}
            iconBg={rateScadute > 0
              ? "bg-red-100 dark:bg-red-900/30"
              : "bg-emerald-100 dark:bg-emerald-900/30"
            }
            label="Residuo"
            value={formatCurrency(residuo)}
            valueClass={residuo > 0
              ? "text-amber-700 dark:text-amber-400"
              : "text-emerald-700 dark:text-emerald-400"
            }
            subtitle={rateScadute > 0
              ? `${rateScadute} scadut${rateScadute === 1 ? "a" : "e"}`
              : undefined
            }
            subtitleClass="text-red-600 dark:text-red-400"
          />
        </div>

        {/* ── Crediti Sedute (dettaglio, dietro disclosure) ── */}
        {showDetail && creditiTotali > 0 ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <KpiCard
              icon={<Dumbbell className={`h-4 w-4 ${NEUTRAL_ICON}`} />}
              iconBg={NEUTRAL_ICON_BG}
              label="Crediti Totali"
              value={`${creditiTotali}`}
            />
            <KpiCard
              icon={<Clock className={`h-4 w-4 ${NEUTRAL_ICON}`} />}
              iconBg={NEUTRAL_ICON_BG}
              label="Programmate"
              value={`${programmate}`}
            />
            <KpiCard
              icon={<CalendarCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />}
              iconBg="bg-emerald-100 dark:bg-emerald-900/30"
              label="Completate"
              value={`${completate}`}
              valueClass={completate > 0 ? "text-emerald-700 dark:text-emerald-400" : undefined}
            />
            <KpiCard
              icon={<Target className={`h-4 w-4 ${
                creditiResidui > 0
                  ? "text-amber-600 dark:text-amber-400"
                  : "text-emerald-600 dark:text-emerald-400"
              }`} />}
              iconBg={creditiResidui > 0
                ? "bg-amber-100 dark:bg-amber-900/30"
                : "bg-emerald-100 dark:bg-emerald-900/30"
              }
              label="Residui"
              value={`${creditiResidui}`}
              valueClass={creditiResidui > 0
                ? "text-amber-700 dark:text-amber-400"
                : "text-emerald-700 dark:text-emerald-400"
              }
              subtitle={creditiResidui === 0 ? "Crediti esauriti" : undefined}
            />
          </div>
        ) : null}

        {/* ── Riconciliazione recesso (R5/L1 + M4): SEGNALE, mai dietro toggle (F2/F4) ── */}
        {creditiTotali > 0 && contract.sedute_non_erogate_chiusura > 0 ? (
          <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-900/40 dark:bg-amber-900/20">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden="true" />
            <p className="text-xs text-amber-800 dark:text-amber-300">
              <strong>{contract.sedute_non_erogate_chiusura} sedute prenotate non erogate</strong> alla chiusura.
              Per rimborsare il non svolto: usa <strong>Riapri</strong> e poi <strong>Termina</strong> da questa scheda.
            </p>
          </div>
        ) : creditiTotali > 0 && completate < creditiTotali ? (
          <p className="px-1 text-[10px] leading-snug text-muted-foreground">
            Il rimborso da recesso si calcola sulle sole sedute <strong>Completate</strong> (erogate);
            le prenotate non riducono il rimborso.
          </p>
        ) : null}

        {/* ── Toggle disclosure (F2): rivela SOLO dettaglio informativo, mai segnali ── */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-7 w-full text-xs text-muted-foreground"
          onClick={() => setShowDetail((prev) => !prev)}
          aria-expanded={showDetail}
        >
          {showDetail ? (
            <>
              <ChevronUp className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
              Nascondi dettaglio
            </>
          ) : (
            <>
              <ChevronDown className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
              Mostra dettaglio
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// KPI Card compatta riusabile
// ════════════════════════════════════════════════════════════

function KpiCard({
  icon,
  iconBg,
  label,
  value,
  valueClass,
  subtitle,
  subtitleClass,
}: {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: string;
  valueClass?: string;
  subtitle?: string;
  subtitleClass?: string;
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border bg-white p-3 shadow-sm dark:bg-zinc-900">
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </p>
        <p className={`text-base font-bold tabular-nums tracking-tight ${valueClass ?? ""}`}>
          {value}
        </p>
        {subtitle && (
          <p className={`text-[10px] font-semibold ${subtitleClass ?? "text-muted-foreground"}`}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
