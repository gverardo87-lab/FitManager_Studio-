// src/app/public/scheda/[token]/page.tsx
"use client";

/**
 * Portale Scheda Allenamento Interattiva — Client Self-Tracking (ADR-009).
 *
 * Replica la stessa struttura visiva del PDF clinico esportabile:
 * - Header scheda (nome, trainer, obiettivo)
 * - 3 sezioni: AVVIAMENTO / BLOCCO SERIE×RIPETIZIONI / STRETCHING
 * - Ogni esercizio principale: card con foto start/end + metriche
 * - Layer interattivo: campi compilabili per dati effettivi
 *
 * Mobile-first. API: fetch() relativo (/api/...) — Next.js proxy → backend.
 */

import { use, useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Dumbbell,
  Loader2,
  Save,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { LogoIcon } from "@/components/ui/logo";
import { formatShortDate } from "@/lib/format";
import type {
  ExerciseLogInput,
  SessionFeedback,
  WorkoutExerciseItem,
  WorkoutExercisesResponse,
  WorkoutLogResponse,
  WorkoutSessionsResponse,
  WorkoutSlotItem,
  WorkoutValidateResponse,
} from "@/types/api";

// ── API helpers ──────────────────────────────────────────────────────────────

function extractDetail(data: Record<string, unknown>, fallback: string): string {
  const d = data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e: { msg?: string }) => e.msg ?? "errore").join("; ");
  return fallback;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function apiGet<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(extractDetail(data, "Errore di connessione"), res.status);
  }
  return res.json();
}

async function apiPost<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(extractDetail(data, "Errore durante il salvataggio"), res.status);
  }
  return res.json();
}

// ── Section helpers (same logic as PDF export) ──────────────────────────────

type Section = "avviamento" | "principale" | "stretching";

const AVVIAMENTO_CATS = new Set(["avviamento"]);
const STRETCHING_CATS = new Set(["stretching", "mobilita"]);

function getSection(categoria: string | null): Section {
  if (categoria && AVVIAMENTO_CATS.has(categoria)) return "avviamento";
  if (categoria && STRETCHING_CATS.has(categoria)) return "stretching";
  return "principale";
}

const SECTION_META: Record<Section, { title: string; color: string; bg: string }> = {
  avviamento: { title: "AVVIAMENTO", color: "text-amber-700", bg: "bg-amber-50" },
  principale: { title: "BLOCCO SERIE × RIPETIZIONI", color: "text-teal-700", bg: "bg-teal-50" },
  stretching: { title: "STRETCHING & MOBILITA", color: "text-cyan-700", bg: "bg-cyan-50" },
};

const SECTION_ORDER: Section[] = ["avviamento", "principale", "stretching"];

// ── Date helpers ─────────────────────────────────────────────────────────────

function formatWeekday(dateStr: string): string {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("it-IT", { weekday: "long" });
}

function isPast(dateStr: string): boolean {
  return dateStr <= new Date().toISOString().slice(0, 10);
}

// ── Page component ───────────────────────────────────────────────────────────

type Phase = "loading" | "main" | "session" | "error";

export default function PublicWorkoutPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);

  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState("");
  const [info, setInfo] = useState<WorkoutValidateResponse | null>(null);
  const [slots, setSlots] = useState<WorkoutSlotItem[]>([]);

  // Session detail
  const [activeSlot, setActiveSlot] = useState<WorkoutSlotItem | null>(null);
  const [exercises, setExercises] = useState<WorkoutExerciseItem[]>([]);
  const [formData, setFormData] = useState<Record<number, ExerciseLogInput>>({});
  const [noteSessione, setNoteSessione] = useState("");
  const [feedback, setFeedback] = useState<SessionFeedback>({});
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<WorkoutLogResponse | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);

  // ── Load ───────────────────────────────────────────────────────────────

  const [rateLimited, setRateLimited] = useState(false);

  const loadData = useCallback(async () => {
    setRateLimited(false);
    try {
      const [infoRes, sessionsRes] = await Promise.all([
        apiGet<WorkoutValidateResponse>(`/api/public/workout/validate?token=${encodeURIComponent(token)}`),
        apiGet<WorkoutSessionsResponse>(`/api/public/workout/sessions?token=${encodeURIComponent(token)}`),
      ]);
      setInfo(infoRes);
      setSlots(sessionsRes.slots);
      setPhase("main");
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setRateLimited(true);
        setPhase("error");
        setErrorMsg("Troppe richieste. Riprova tra qualche minuto.");
      } else {
        setErrorMsg(err instanceof Error ? err.message : "Link non valido");
        setPhase("error");
      }
    }
  }, [token]);

  useEffect(() => { loadData(); }, [loadData]);

  // ── Open session ───────────────────────────────────────────────────────

  const openSession = useCallback(async (slot: WorkoutSlotItem) => {
    try {
      const res = await apiGet<WorkoutExercisesResponse>(
        `/api/public/workout/session/${slot.id}/exercises?token=${encodeURIComponent(token)}`
      );
      setActiveSlot(slot);
      setExercises(res.exercises);
      setSaveResult(null);
      setNoteSessione("");
      setFeedback({});
      const fd: Record<number, ExerciseLogInput> = {};
      for (const ex of res.exercises) {
        fd[ex.id] = {
          id_esercizio_sessione: ex.id,
          serie_effettive: ex.log?.serie_effettive ?? ex.serie,
          ripetizioni_effettive: ex.log?.ripetizioni_effettive ?? ex.ripetizioni,
          carico_effettivo_kg: ex.log?.carico_effettivo_kg ?? ex.carico_kg,
          rpe: ex.log?.rpe ?? null,
          note_cliente: ex.log?.note_cliente ?? null,
        };
      }
      setFormData(fd);
      setPhase("session");
      window.scrollTo(0, 0);
    } catch {
      setErrorMsg("Impossibile caricare gli esercizi");
      setPhase("error");
    }
  }, [token]);

  // ── Save ───────────────────────────────────────────────────────────────

  const saveSession = useCallback(async () => {
    if (!activeSlot) return;
    setSaving(true);
    try {
      const result = await apiPost<WorkoutLogResponse>(
        `/api/public/workout/session/${activeSlot.id}/log`,
        {
          token,
          exercises: Object.values(formData),
          note_sessione: noteSessione || null,
          feedback: Object.values(feedback).some((v) => v != null) ? feedback : null,
        }
      );
      setSaveResult(result);
      setSlots((prev) => prev.map((s) =>
        s.id === activeSlot.id ? { ...s, stato: "completato" as const, has_log: true } : s
      ));
      if (info) {
        setInfo({ ...info, completed_slots: info.completed_slots + (activeSlot.stato === "completato" ? 0 : 1) });
      }
    } catch (err) {
      setSaveResult({ success: false, message: err instanceof Error ? err.message : "Errore", completion_pct: 0 });
    } finally {
      setSaving(false);
    }
  }, [activeSlot, formData, noteSessione, feedback, token, info]);

  const updateField = useCallback(
    (exId: number, field: keyof ExerciseLogInput, value: string | number | null) => {
      setFormData((prev) => ({ ...prev, [exId]: { ...prev[exId], [field]: value } }));
    }, []
  );

  // ── Computed ───────────────────────────────────────────────────────────

  const completionPct = info && info.total_slots > 0
    ? Math.round((info.completed_slots / info.total_slots) * 100) : 0;

  const todaySlots = slots.filter((s) => isPast(s.data_pianificata) && s.stato === "pianificato");
  const upcomingSlots = slots.filter((s) => !isPast(s.data_pianificata) && s.stato === "pianificato");
  const completedSlots = slots.filter((s) => s.stato === "completato" || s.stato === "parziale");

  // Group exercises by section
  const grouped: Record<Section, WorkoutExerciseItem[]> = { avviamento: [], principale: [], stretching: [] };
  for (const ex of exercises) grouped[getSection(ex.categoria)].push(ex);

  // ── RENDER: Loading ────────────────────────────────────────────────────

  if (phase === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-teal-50 to-white text-gray-900" style={{ colorScheme: "light" }}>
        <div className="text-center space-y-4">
          <LogoIcon className="h-12 w-12 mx-auto text-teal-600 animate-pulse" />
          <p className="text-gray-500">Caricamento scheda...</p>
        </div>
      </div>
    );
  }

  // ── RENDER: Error ──────────────────────────────────────────────────────

  if (phase === "error") {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gradient-to-b ${rateLimited ? "from-amber-50" : "from-red-50"} to-white px-4 text-gray-900`} style={{ colorScheme: "light" }}>
        <div className="max-w-sm w-full bg-white rounded-xl shadow-sm border p-6 text-center space-y-4">
          {rateLimited ? (
            <>
              <Loader2 className="h-12 w-12 mx-auto text-amber-500" />
              <h2 className="text-lg font-semibold text-gray-900">Attendi un momento</h2>
              <p className="text-sm text-gray-600">{errorMsg}</p>
              <Button variant="outline" size="sm" onClick={() => { setPhase("loading"); loadData(); }}>
                Riprova
              </Button>
            </>
          ) : (
            <>
              <XCircle className="h-12 w-12 mx-auto text-red-400" />
              <h2 className="text-lg font-semibold text-gray-900">Link non valido</h2>
              <p className="text-sm text-gray-500">{errorMsg}</p>
              <p className="text-xs text-gray-500">Contatta il tuo trainer per ricevere un nuovo link.</p>
            </>
          )}
        </div>
      </div>
    );
  }

  // ── RENDER: Session detail (LA SCHEDA VERA) ────────────────────────────

  if (phase === "session" && activeSlot) {
    return (
      <div className="min-h-screen bg-[#f3f4f6] text-gray-900" style={{ colorScheme: "light" }}>
        {/* Session header — stile PDF */}
        <header className="bg-white border-b shadow-sm">
          <div className="max-w-2xl mx-auto px-4 py-3">
            <button
              className="flex items-center gap-1.5 text-sm text-teal-700 hover:text-teal-900 mb-2"
              onClick={() => { setPhase("main"); setActiveSlot(null); }}
            >
              <ArrowLeft className="h-4 w-4" /> Torna alla scheda
            </button>
            <h2 className="text-base font-bold text-[#00695c]">{info?.workout_name}</h2>
            <p className="text-xs text-gray-500">
              {info?.client_name} &middot; {info?.trainer_name}
            </p>
          </div>
          {/* Session title bar — like PDF */}
          <div className="bg-[#eef2f7] border-t border-l-[3px] border-l-[#009688]">
            <div className="max-w-2xl mx-auto px-4 py-2 flex justify-between items-center">
              <span className="font-semibold text-sm text-gray-900">{activeSlot.sessione_nome}</span>
              <span className="text-xs text-gray-500">
                {formatWeekday(activeSlot.data_pianificata)} {formatShortDate(activeSlot.data_pianificata)}
              </span>
            </div>
          </div>
        </header>

        {/* Save result */}
        {saveResult ? (
          <div className="max-w-2xl mx-auto px-4 pt-4">
            <div className={`rounded-lg p-5 text-center space-y-2 ${saveResult.success ? "bg-emerald-50 border border-emerald-200" : "bg-red-50 border border-red-200"}`}>
              {saveResult.success
                ? <><CheckCircle2 className="h-10 w-10 mx-auto text-emerald-500" /><p className="font-bold text-emerald-700">Sessione salvata!</p><p className="text-sm text-emerald-600">Aderenza: {saveResult.completion_pct}%</p></>
                : <><XCircle className="h-10 w-10 mx-auto text-red-500" /><p className="font-bold text-red-700">{saveResult.message}</p></>}
              <Button variant="outline" size="sm" className="mt-3" onClick={() => { setPhase("main"); setActiveSlot(null); }}>
                Torna alla scheda
              </Button>
            </div>
          </div>
        ) : (
          <main className="max-w-2xl mx-auto px-4 py-4 space-y-4">
            {/* Sections — same order as PDF */}
            {SECTION_ORDER.map((section) => {
              const items = grouped[section];
              if (items.length === 0) return null;
              const meta = SECTION_META[section];
              const isPrincipale = section === "principale";

              return (
                <section key={section}>
                  {/* Section header — like PDF */}
                  <h3 className={`text-xs font-bold tracking-wide px-3 py-2 mb-2 rounded ${meta.color} ${meta.bg}`}>
                    {meta.title}
                  </h3>

                  {isPrincipale ? (
                    /* Principal exercises — full card like PDF */
                    <div className="space-y-3">
                      {items.map((ex, idx) => (
                        <PrincipalExerciseCard
                          key={ex.id}
                          ex={ex}
                          idx={idx}
                          fd={formData[ex.id]}
                          onUpdate={updateField}
                        />
                      ))}
                    </div>
                  ) : (
                    /* Avviamento/Stretching — compact table like PDF */
                    <CompactSectionTable
                      exercises={items}
                      formData={formData}
                      onUpdate={updateField}
                    />
                  )}
                </section>
              );
            })}

            {/* Session note */}
            <div className="bg-white rounded-lg border p-3">
              <label className="text-xs font-medium text-gray-500">Note sessione</label>
              <Textarea
                placeholder="Come e' andata la sessione?"
                className="mt-1 !text-base md:!text-sm"
                rows={2}
                value={noteSessione}
                onChange={(e) => setNoteSessione(e.target.value)}
              />
            </div>

            {/* Feedback sessione — 5 quick-tap */}
            <div className="bg-white rounded-lg border p-3 space-y-3">
              <p className="text-xs font-bold text-teal-700 tracking-wider">COME E' ANDATA?</p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <RatingRow label="Energia prima" value={feedback.energia_pre} onChange={(v) => setFeedback((p) => ({ ...p, energia_pre: v }))} emoji={["😴", "😕", "😐", "😊", "⚡"]} />
                <RatingRow label="Energia dopo" value={feedback.energia_post} onChange={(v) => setFeedback((p) => ({ ...p, energia_post: v }))} emoji={["😵", "😕", "😐", "💪", "🔥"]} />
                <RatingRow label="Soddisfazione" value={feedback.soddisfazione} onChange={(v) => setFeedback((p) => ({ ...p, soddisfazione: v }))} emoji={["😞", "😕", "😐", "😊", "🤩"]} />
                <RatingRow label="Difficolta'" value={feedback.difficolta_percepita} onChange={(v) => setFeedback((p) => ({ ...p, difficolta_percepita: v }))} emoji={["😴", "🙂", "😤", "😰", "🥵"]} />
              </div>

              <div>
                <label className="text-xs uppercase text-gray-600 font-medium">Durata effettiva (minuti)</label>
                <Input
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={300}
                  className="h-10 !text-base md:!text-sm text-center font-semibold mt-1 w-full max-w-[140px]"
                  placeholder="es. 55"
                  value={feedback.durata_effettiva_min ?? ""}
                  onChange={(e) => setFeedback((p) => ({ ...p, durata_effettiva_min: e.target.value ? Number(e.target.value) : null }))}
                />
              </div>
            </div>

            {/* Save */}
            <Button className="w-full h-12 text-base bg-[#009688] hover:bg-[#00796b]" onClick={saveSession} disabled={saving}>
              {saving ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Save className="h-5 w-5 mr-2" />}
              Salva sessione
            </Button>
          </main>
        )}

        <footer className="text-center py-4">
          <p className="text-[11px] text-gray-500">Powered by FitManager</p>
        </footer>
      </div>
    );
  }

  // ── RENDER: Main view (session list) ───────────────────────────────────

  return (
    <div className="min-h-screen bg-[#f3f4f6] text-gray-900" style={{ colorScheme: "light" }}>
      {/* Cover — like PDF cover page */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-5 text-center space-y-3">
          <p className="text-[#00796b] font-bold text-lg tracking-wide">FitManager Studio+</p>
          <h1 className="text-xl font-bold text-[#004d40]">{info?.workout_name}</h1>
          <p className="text-xs text-gray-500 tracking-widest uppercase">Scheda di Allenamento</p>
          <div className="max-w-sm mx-auto text-sm space-y-1 pt-2">
            <div className="grid grid-cols-[auto_1fr] gap-x-3 border-b border-gray-100 py-1.5">
              <span className="text-gray-500 text-left">Cliente</span>
              <strong className="text-right truncate text-gray-900">{info?.client_name}</strong>
            </div>
            <div className="grid grid-cols-[auto_1fr] gap-x-3 border-b border-gray-100 py-1.5">
              <span className="text-gray-500 text-left">Trainer</span>
              <strong className="text-right truncate text-gray-900">{info?.trainer_name}</strong>
            </div>
            {info?.data_inizio && info?.data_fine ? (
              <div className="grid grid-cols-[auto_1fr] gap-x-3 border-b border-gray-100 py-1.5">
                <span className="text-gray-500 text-left">Periodo</span>
                <strong className="text-right text-gray-900">{formatShortDate(info.data_inizio)} — {formatShortDate(info.data_fine)}</strong>
              </div>
            ) : null}
            <div className="grid grid-cols-[auto_1fr] gap-x-3 py-1.5">
              <span className="text-gray-500 text-left">Frequenza</span>
              <strong className="text-right text-gray-900">{info?.sessioni_per_settimana}x / settimana</strong>
            </div>
          </div>

          {/* Progress bar */}
          <div className="max-w-sm mx-auto pt-2 space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Aderenza</span>
              <span className="font-semibold tabular-nums text-gray-900">{info?.completed_slots ?? 0}/{info?.total_slots ?? 0} ({completionPct}%)</span>
            </div>
            <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-[#009688] rounded-full transition-all duration-500" style={{ width: `${completionPct}%` }} />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-4 space-y-5">
        {/* Da completare */}
        {todaySlots.length > 0 ? (
          <section>
            <h2 className="text-sm font-bold mb-2 flex items-center gap-1.5 text-[#00695c]">
              <Dumbbell className="h-4 w-4" /> Da completare
            </h2>
            <div className="space-y-2">
              {todaySlots.map((slot) => (
                <SlotButton key={slot.id} slot={slot} accent onClick={() => openSession(slot)} />
              ))}
            </div>
          </section>
        ) : null}

        {/* Prossime */}
        {upcomingSlots.length > 0 ? (
          <section>
            <h2 className="text-sm font-semibold mb-2 text-gray-500">Prossime sessioni</h2>
            <div className="space-y-1.5">
              {upcomingSlots.map((slot) => (
                <SlotButton key={slot.id} slot={slot} onClick={() => openSession(slot)} />
              ))}
            </div>
          </section>
        ) : null}

        {/* Completate */}
        {completedSlots.length > 0 ? (
          <section>
            <button className="flex items-center gap-2 text-sm font-semibold text-gray-500 mb-2" onClick={() => setShowCompleted((p) => !p)}>
              Completate ({completedSlots.length})
              {showCompleted ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            {showCompleted ? (
              <div className="space-y-1.5">
                {completedSlots.map((slot) => (
                  <SlotButton key={slot.id} slot={slot} completed onClick={() => openSession(slot)} />
                ))}
              </div>
            ) : null}
          </section>
        ) : null}

        {/* All done */}
        {todaySlots.length === 0 && upcomingSlots.length === 0 && completedSlots.length > 0 ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6 text-center space-y-2">
            <CheckCircle2 className="h-10 w-10 mx-auto text-emerald-500" />
            <p className="font-bold text-emerald-700">Scheda completata!</p>
            <p className="text-sm text-emerald-600">Hai completato tutte le {completedSlots.length} sessioni. Ottimo lavoro!</p>
          </div>
        ) : null}

        <footer className="text-center py-4">
          <p className="text-[11px] text-gray-500">Powered by FitManager</p>
        </footer>
      </main>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ═════════════════════════════════════════════════════════════════════════════

/** Slot button in session list */
function SlotButton({ slot, accent, completed, onClick }: {
  slot: WorkoutSlotItem;
  accent?: boolean;
  completed?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`w-full text-left rounded-lg border p-3 transition-colors flex items-center gap-3 ${
        accent
          ? "bg-white border-2 border-teal-300 hover:border-teal-500 shadow-sm"
          : completed
            ? "bg-white hover:bg-gray-100"
            : "bg-white hover:bg-gray-100"
      }`}
      onClick={onClick}
    >
      {completed
        ? <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
        : <Dumbbell className="h-4 w-4 text-teal-600 shrink-0" />}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{slot.sessione_nome}</p>
        <p className="text-xs text-gray-500">
          {formatWeekday(slot.data_pianificata)} {formatShortDate(slot.data_pianificata, false)}
          {slot.focus_muscolare ? ` · ${slot.focus_muscolare}` : ""}
        </p>
      </div>
      <span className={`text-xs font-medium ${accent ? "text-teal-600" : "text-gray-500"}`}>
        {accent ? "Compila" : completed ? "Dettagli" : "Apri"}
      </span>
    </button>
  );
}

/** Principal exercise card — foto grandi hero + metriche + accordion info + input */
function PrincipalExerciseCard({ ex, idx, fd, onUpdate }: {
  ex: WorkoutExerciseItem;
  idx: number;
  fd: ExerciseLogInput | undefined;
  onUpdate: (exId: number, field: keyof ExerciseLogInput, value: string | number | null) => void;
}) {
  const [showInfo, setShowInfo] = useState(false);
  const hasInfo = ex.setup || ex.esecuzione || ex.respirazione || ex.coaching_cues || ex.errori_comuni;
  const hasPhotos = ex.foto_start || ex.foto_end;

  return (
    <article className="bg-white rounded-xl border overflow-hidden shadow-sm">
      {/* Header teal */}
      <div className="bg-[#009688] text-white flex items-center gap-2 px-3 py-2.5">
        <span className="bg-white/20 rounded-full w-7 h-7 flex items-center justify-center font-bold text-sm shrink-0">{idx + 1}</span>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-bold leading-snug">{ex.nome_esercizio}</h4>
          {ex.gruppo_muscolare ? (
            <p className="text-[11px] text-white/70 leading-tight">{ex.gruppo_muscolare}</p>
          ) : null}
        </div>
      </div>

      {/* FOTO GRANDI — hero, primo contenuto visibile */}
      {hasPhotos ? (
        <div className="grid grid-cols-2 gap-0 border-b">
          <div className="relative aspect-[4/3] bg-gray-100">
            {ex.foto_start ? (
              <img src={ex.foto_start} alt={`${ex.nome_esercizio} — posizione iniziale`} className="w-full h-full object-cover" />
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-gray-500">Start</div>
            )}
            <span className="absolute bottom-1 left-1 bg-black/60 text-white text-[9px] px-1.5 py-0.5 rounded">START</span>
          </div>
          <div className="relative aspect-[4/3] bg-gray-100 border-l">
            {ex.foto_end ? (
              <img src={ex.foto_end} alt={`${ex.nome_esercizio} — posizione finale`} className="w-full h-full object-cover" />
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-gray-500">End</div>
            )}
            <span className="absolute bottom-1 left-1 bg-black/60 text-white text-[9px] px-1.5 py-0.5 rounded">END</span>
          </div>
        </div>
      ) : null}

      <div className="p-3 space-y-3">
        {/* Metriche pianificate dal trainer */}
        <div>
          <p className="text-xs font-bold text-gray-500 tracking-wider mb-1.5">PIANO TRAINER</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            <MetricBox label="Serie" value={String(ex.serie)} />
            <MetricBox label="Rip" value={ex.ripetizioni} />
            <MetricBox label="Kg" value={ex.carico_kg != null ? String(ex.carico_kg) : "—"} />
            <MetricBox label="Riposo" value={`${ex.tempo_riposo_sec}s`} />
            {ex.tempo_esecuzione ? <MetricBox label="Tempo" value={ex.tempo_esecuzione} span2 /> : null}
            {ex.note_trainer ? <MetricBox label="Note PT" value={ex.note_trainer} span2 /> : null}
          </div>
        </div>

        {/* Blocco badge */}
        {ex.blocco_nome ? (
          <span className="inline-block text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded font-medium">
            {ex.blocco_tipo ? ex.blocco_tipo.toUpperCase() : "BLOCCO"}: {ex.blocco_nome}
          </span>
        ) : null}

        {/* Accordion: COME ESEGUIRLO (con foto in testa se non ci sono hero) */}
        {hasInfo ? (
          <div className="border rounded-lg overflow-hidden">
            <button
              className="w-full text-left text-xs font-bold text-blue-700 bg-blue-50 flex items-center justify-between px-3 py-2.5"
              onClick={() => setShowInfo((p) => !p)}
            >
              <span className="flex items-center gap-1.5">
                <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" /></svg>
                COME ESEGUIRLO
              </span>
              {showInfo ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            {showInfo ? (
              <div className="px-3 py-2.5 space-y-2 text-sm bg-white">
                {/* Foto anche qui dentro se non c'erano in hero */}
                {!hasPhotos && (ex.foto_start || ex.foto_end) ? (
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    {ex.foto_start ? <img src={ex.foto_start} alt="Start" className="rounded border w-full aspect-[4/3] object-cover" /> : null}
                    {ex.foto_end ? <img src={ex.foto_end} alt="End" className="rounded border w-full aspect-[4/3] object-cover" /> : null}
                  </div>
                ) : null}
                {ex.setup ? <InfoBlock title="Setup" text={ex.setup} color="amber" /> : null}
                {ex.esecuzione ? <InfoBlock title="Esecuzione" text={ex.esecuzione} color="teal" /> : null}
                {ex.respirazione ? <InfoBlock title="Respirazione" text={ex.respirazione} color="cyan" /> : null}
                {ex.coaching_cues ? <InfoBlock title="Coaching Cues" text={ex.coaching_cues} color="violet" /> : null}
                {ex.errori_comuni ? <InfoBlock title="Errori da evitare" text={ex.errori_comuni} color="red" /> : null}
              </div>
            ) : null}
          </div>
        ) : null}

        {/* I TUOI DATI — sempre visibili */}
        <div className="border-t pt-3">
          <p className="text-xs font-bold text-teal-700 tracking-wider mb-2">I TUOI DATI</p>
          <div className="grid grid-cols-3 gap-2">
            <InputField label="Serie" type="number" inputMode="numeric" value={fd?.serie_effettive} onChange={(v) => onUpdate(ex.id, "serie_effettive", v ? Number(v) : null)} />
            <InputField label="Reps" type="text" inputMode="text" placeholder="10,10,8" value={fd?.ripetizioni_effettive} onChange={(v) => onUpdate(ex.id, "ripetizioni_effettive", v || null)} />
            <InputField label="Kg" type="number" inputMode="decimal" step="0.5" value={fd?.carico_effettivo_kg} onChange={(v) => onUpdate(ex.id, "carico_effettivo_kg", v ? Number(v) : null)} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
            <InputField label="RPE (1-10)" type="number" inputMode="decimal" min={0} max={10} step={0.5} value={fd?.rpe} onChange={(v) => onUpdate(ex.id, "rpe", v ? Number(v) : null)} />
            <div>
              <label className="text-xs uppercase text-gray-600 font-medium">Note</label>
              <Textarea
                placeholder="Come ti sei sentito?"
                className="!text-base md:!text-sm min-h-[44px] resize-none mt-1"
                rows={1}
                value={fd?.note_cliente ?? ""}
                onChange={(e) => onUpdate(ex.id, "note_cliente", e.target.value || null)}
              />
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

/** Info block — colore per tipo */
const INFO_COLORS: Record<string, string> = {
  amber: "bg-amber-50 text-amber-900",
  teal: "bg-teal-50 text-teal-900",
  cyan: "bg-cyan-50 text-cyan-900",
  violet: "bg-violet-50 text-violet-900",
  red: "bg-red-50 text-red-900",
};

function InfoBlock({ title, text, color }: { title: string; text: string; color: string }) {
  return (
    <div className={`rounded-md px-3 py-2.5 ${INFO_COLORS[color] ?? "bg-gray-50 text-gray-900"}`}>
      <p className="font-bold text-xs mb-0.5 text-inherit">{title}</p>
      <p className="text-sm leading-relaxed text-inherit">{text}</p>
    </div>
  );
}

/** Compact card for avviamento/stretching — input always visible, mobile-first */
function CompactSectionTable({ exercises, formData, onUpdate }: {
  exercises: WorkoutExerciseItem[];
  formData: Record<number, ExerciseLogInput>;
  onUpdate: (exId: number, field: keyof ExerciseLogInput, value: string | number | null) => void;
}) {
  return (
    <div className="space-y-2.5">
      {exercises.map((ex, idx) => {
        const fd = formData[ex.id];
        return (
          <div key={ex.id} className="bg-white rounded-lg border shadow-sm">
            {/* Header */}
            <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border-b">
              <span className="bg-gray-300 text-gray-700 rounded-full w-6 h-6 flex items-center justify-center font-bold text-xs shrink-0">{idx + 1}</span>
              <span className="text-sm font-semibold flex-1 min-w-0 text-gray-900">{ex.nome_esercizio}</span>
            </div>
            {/* Metriche trainer + input */}
            <div className="px-3 py-3 space-y-2.5">
              <div className="flex gap-2 text-xs">
                <span className="text-gray-500 font-medium">Piano:</span>
                <span className="font-semibold text-gray-900">{ex.serie} × {ex.ripetizioni}</span>
                {ex.note_trainer ? <span className="text-gray-500 truncate">· {ex.note_trainer}</span> : null}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <InputField label="Serie" type="number" inputMode="numeric" value={fd?.serie_effettive} onChange={(v) => onUpdate(ex.id, "serie_effettive", v ? Number(v) : null)} />
                <InputField label="Reps" type="text" inputMode="text" value={fd?.ripetizioni_effettive} onChange={(v) => onUpdate(ex.id, "ripetizioni_effettive", v || null)} />
                <InputField label="Note" type="text" inputMode="text" value={fd?.note_cliente} onChange={(v) => onUpdate(ex.id, "note_cliente", v || null)} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Metric box — like PDF metrics cell */
function MetricBox({ label, value, span2 }: { label: string; value: string; span2?: boolean }) {
  return (
    <div className={`border rounded px-2.5 py-2 bg-gray-50 ${span2 ? "col-span-2" : ""}`}>
      <span className="text-[11px] text-gray-500 block leading-tight">{label}</span>
      <strong className="text-sm text-gray-900">{value}</strong>
    </div>
  );
}

/** Input field for actual data — highlighted when pre-filled.
 *  Mobile-first: min 16px font (prevents iOS auto-zoom), generous padding,
 *  explicit colors (no reliance on theme variables for visibility). */
function InputField({ label, type, inputMode, value, onChange, placeholder, step, min, max }: {
  label: string;
  type: string;
  inputMode?: "text" | "numeric" | "decimal";
  value: string | number | null | undefined;
  onChange: (v: string) => void;
  placeholder?: string;
  step?: number | string;
  min?: number;
  max?: number;
}) {
  const hasValue = value != null && value !== "";
  return (
    <div>
      <label className="text-xs uppercase text-gray-600 font-medium">{label}</label>
      <Input
        type={type}
        inputMode={inputMode}
        step={step}
        min={min}
        max={max}
        className={`!text-base md:!text-sm h-11 px-2.5 text-center font-semibold mt-1 ${
          hasValue
            ? "border-teal-400 bg-teal-50 text-teal-900"
            : "text-gray-900"
        }`}
        placeholder={placeholder}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

/** Rating row — 5 emoji tap per feedback */
function RatingRow({ label, value, onChange, emoji }: {
  label: string;
  value: number | null | undefined;
  onChange: (v: number | null) => void;
  emoji: string[];
}) {
  return (
    <div>
      <label className="text-xs uppercase text-gray-600 font-medium block mb-1.5">{label}</label>
      <div className="flex gap-2">
        {emoji.map((e, i) => {
          const rating = i + 1;
          const isSelected = value === rating;
          return (
            <button
              key={rating}
              type="button"
              className={`w-11 h-11 rounded-lg text-xl flex items-center justify-center transition-all ${
                isSelected
                  ? "bg-teal-100 ring-2 ring-teal-500 scale-110"
                  : "bg-gray-100 hover:bg-gray-200"
              }`}
              onClick={() => onChange(isSelected ? null : rating)}
              aria-label={`${label} ${rating} di 5`}
            >
              {e}
            </button>
          );
        })}
      </div>
    </div>
  );
}
