// src/components/clients/profile/AllenamentoTab.tsx
"use client";

/**
 * Tab "Allenamento" nel profilo cliente — centro di comando atletico.
 *
 * 5 sezioni scroll verticale:
 *   1. Aderenza — barra % + streak + stats
 *   2. Progressione — grafici carico per esercizio nel tempo
 *   3. Personal Records — PR con 1RM stimato
 *   4. Feedback — soddisfazione/energia/difficolta trend
 *   5. Volume — volume per sessione nel tempo
 */

import { useState } from "react";
import {
  Award,
  BarChart3,
  Dumbbell,
  Flame,
  Heart,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatShortDate } from "@/lib/format";
import { useWorkoutAnalytics } from "@/hooks/useWorkouts";
import { EmptyTab, TabSkeleton } from "@/components/clients/profile/ProfileShared";
import type {
  AderenzaStats,
  ExerciseProgression,
  FeedbackPoint,
  PersonalRecord,
  RPEPoint,
  VolumePoint,
} from "@/types/api";

interface AllenamentoTabProps {
  clientId: number;
}

const PERIOD_OPTIONS = [
  { label: "3 mesi", value: 3 },
  { label: "6 mesi", value: 6 },
  { label: "12 mesi", value: 12 },
] as const;

export function AllenamentoTab({ clientId }: AllenamentoTabProps) {
  const [mesi, setMesi] = useState(3);
  const { data, isLoading } = useWorkoutAnalytics(clientId, mesi);

  if (isLoading) return <TabSkeleton />;

  if (!data || (data.aderenza.totale_pianificate === 0 && data.personal_records.length === 0)) {
    return (
      <EmptyTab
        icon={Dumbbell}
        message="Nessun dato di allenamento"
        hint="I dati appariranno quando il cliente iniziera' a compilare la scheda interattiva"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Period selector */}
      <div className="flex items-center gap-2">
        {PERIOD_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
              mesi === opt.value
                ? "bg-teal-100 text-teal-800 font-semibold"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
            onClick={() => setMesi(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* 1. Aderenza */}
      <AderenzaSection stats={data.aderenza} />

      {/* 2. Volume */}
      {data.volume.length > 0 ? <VolumeSection points={data.volume} /> : null}

      {/* 3. Progressione */}
      {data.progressione.length > 0 ? <ProgressioneSection exercises={data.progressione} /> : null}

      {/* 4. Personal Records */}
      {data.personal_records.length > 0 ? <PRSection records={data.personal_records} /> : null}

      {/* 5. Feedback + RPE */}
      {data.feedback_trend.length > 0 || data.rpe_trend.length > 0 ? (
        <FeedbackSection feedback={data.feedback_trend} rpe={data.rpe_trend} />
      ) : null}
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTIONS
// ═════════════════════════════════════════════════════════════════════════════

function AderenzaSection({ stats }: { stats: AderenzaStats }) {
  const pct = stats.percentuale;
  const barColor = pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";

  return (
    <section className="space-y-3">
      <SectionHeader icon={Target} title="Aderenza" />

      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Sessioni completate</span>
          <span className="font-bold tabular-nums">
            {stats.totale_completate + stats.totale_parziali}/{stats.totale_pianificate} ({pct}%)
          </span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <StatCard icon={<Dumbbell className="h-4 w-4 text-emerald-600" />} label="Completate" value={stats.totale_completate} />
        <StatCard icon={<BarChart3 className="h-4 w-4 text-amber-600" />} label="Parziali" value={stats.totale_parziali} />
        <StatCard icon={<Flame className="h-4 w-4 text-orange-500" />} label="Streak corrente" value={stats.streak_corrente} suffix="sessioni" />
        <StatCard icon={<Award className="h-4 w-4 text-violet-600" />} label="Streak record" value={stats.streak_massimo} suffix="sessioni" />
      </div>
    </section>
  );
}

function VolumeSection({ points }: { points: VolumePoint[] }) {
  const chartData = points.map((p) => ({
    data: formatShortDate(p.data, false),
    volume: Math.round(p.volume_kg),
    nome: p.sessione_nome ?? "",
  }));

  return (
    <section className="space-y-3">
      <SectionHeader icon={BarChart3} title="Volume per sessione" subtitle="Serie x Reps x Kg" />
      <div className="h-[200px] sm:h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#009688" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#009688" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="data" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} width={45} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
              formatter={(value: number) => [`${value.toLocaleString("it-IT")} kg`, "Volume"]}
              labelFormatter={(label) => label}
            />
            <Area type="monotone" dataKey="volume" stroke="#009688" fill="url(#volGrad)" strokeWidth={2} dot={{ r: 3 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function ProgressioneSection({ exercises }: { exercises: ExerciseProgression[] }) {
  // Mostra top 6 esercizi per numero di data points
  const top = exercises
    .filter((e) => e.punti.length >= 2)
    .sort((a, b) => b.punti.length - a.punti.length)
    .slice(0, 6);

  if (top.length === 0) return null;

  const COLORS = ["#009688", "#e91e63", "#ff9800", "#3f51b5", "#4caf50", "#9c27b0"];

  return (
    <section className="space-y-3">
      <SectionHeader icon={TrendingUp} title="Progressione carico" subtitle="Evoluzione kg per esercizio" />
      <div className="h-[220px] sm:h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="data"
              type="category"
              allowDuplicatedCategory={false}
              tick={{ fontSize: 10 }}
            />
            <YAxis tick={{ fontSize: 10 }} width={40} unit=" kg" />
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
            {top.map((ex, i) => (
              <Line
                key={ex.id_esercizio}
                data={ex.punti.map((p) => ({ data: formatShortDate(p.data, false), [ex.nome_esercizio]: p.carico_kg }))}
                dataKey={ex.nome_esercizio}
                name={ex.nome_esercizio}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {top.map((ex, i) => (
          <span key={ex.id_esercizio} className="flex items-center gap-1.5 text-xs">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
            {ex.nome_esercizio}
          </span>
        ))}
      </div>
    </section>
  );
}

function PRSection({ records }: { records: PersonalRecord[] }) {
  const sorted = [...records].sort((a, b) => b.max_carico_kg - a.max_carico_kg);

  return (
    <section className="space-y-3">
      <SectionHeader icon={Award} title="Personal Records" subtitle="Massimi raggiunti" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {sorted.map((pr) => (
          <div key={pr.id_esercizio} className="flex items-center gap-3 bg-gradient-to-r from-amber-50 to-white border border-amber-200 rounded-lg p-3">
            <div className="bg-amber-100 rounded-full p-2 shrink-0">
              <Award className="h-4 w-4 text-amber-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">{pr.nome_esercizio}</p>
              <p className="text-xs text-muted-foreground">{formatShortDate(pr.data_pr)}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-lg font-bold tabular-nums text-amber-700">{pr.max_carico_kg} kg</p>
              {pr.estimated_1rm ? (
                <p className="text-[10px] text-muted-foreground">1RM ~{pr.estimated_1rm} kg</p>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function FeedbackSection({ feedback, rpe }: { feedback: FeedbackPoint[]; rpe: RPEPoint[] }) {
  const feedbackData = feedback.map((f) => ({
    data: formatShortDate(f.data, false),
    soddisfazione: f.soddisfazione,
    energia_pre: f.energia_pre,
    energia_post: f.energia_post,
    difficolta: f.difficolta_percepita,
  }));

  const rpeData = rpe.map((r) => ({
    data: formatShortDate(r.data, false),
    rpe: r.rpe_medio,
  }));

  return (
    <section className="space-y-3">
      <SectionHeader icon={Heart} title="Feedback & RPE" subtitle="Percezione del cliente nel tempo" />

      {feedbackData.length > 0 ? (
        <div className="h-[180px] sm:h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={feedbackData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="data" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 10 }} width={25} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Line type="monotone" dataKey="soddisfazione" name="Soddisfazione" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} connectNulls />
              <Line type="monotone" dataKey="energia_post" name="Energia post" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} connectNulls />
              <Line type="monotone" dataKey="difficolta" name="Difficolta'" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      {rpeData.length > 0 ? (
        <>
          <p className="text-xs font-semibold text-muted-foreground">RPE medio per sessione</p>
          <div className="h-[140px] sm:h-[180px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rpeData}>
                <defs>
                  <linearGradient id="rpeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="data" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 10]} tick={{ fontSize: 10 }} width={25} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Area type="monotone" dataKey="rpe" name="RPE" stroke="#ef4444" fill="url(#rpeGrad)" strokeWidth={2} dot={{ r: 3 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : null}
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SHARED
// ═════════════════════════════════════════════════════════════════════════════

function SectionHeader({ icon: Icon, title, subtitle }: { icon: React.ComponentType<{ className?: string }>; title: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-4 w-4 text-teal-600" />
      <div>
        <h3 className="text-sm font-bold">{title}</h3>
        {subtitle ? <p className="text-[11px] text-muted-foreground">{subtitle}</p> : null}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, suffix }: { icon: React.ReactNode; label: string; value: number; suffix?: string }) {
  return (
    <div className="flex items-center gap-2.5 bg-white border rounded-lg p-2.5">
      {icon}
      <div>
        <p className="text-lg font-bold tabular-nums leading-none">{value}</p>
        <p className="text-[10px] text-muted-foreground">{label}{suffix ? ` (${suffix})` : ""}</p>
      </div>
    </div>
  );
}
