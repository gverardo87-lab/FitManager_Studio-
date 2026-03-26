// src/components/movements/GradientKpiCard.tsx

/**
 * Gradient KPI Card — shell visuale condiviso per card KPI della sezione Cassa.
 *
 * Usato da: cassa/page.tsx (KpiCards), AgingReport, ForecastTab.
 * Il consumer controlla valore e icona (ReactNode), il componente controlla il layout.
 */

interface GradientKpiCardProps {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  /** ReactNode per supportare AnimatedNumber o testo formattato */
  value: React.ReactNode;
  sub?: string;
  borderColor: string;
  gradient: string;
}

export function GradientKpiCard({
  icon,
  iconBg,
  label,
  value,
  sub,
  borderColor,
  gradient,
}: GradientKpiCardProps) {
  return (
    <div className={`flex items-start gap-3 rounded-xl border border-l-4 ${borderColor} bg-gradient-to-br ${gradient} p-4 shadow-sm transition-shadow hover:shadow-md`}>
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </p>
        <div>{value}</div>
        {sub != null && (
          <p className="text-[10px] text-muted-foreground/70">{sub}</p>
        )}
      </div>
    </div>
  );
}

/** Colori condizionali per card margine (positivo = blu, negativo = rosso). */
export function resolveMarginColors(isPositive: boolean) {
  return isPositive
    ? {
        borderColor: "border-l-blue-500",
        gradient: "from-blue-50/80 to-white dark:from-blue-950/40 dark:to-zinc-900",
        iconBg: "bg-blue-100 dark:bg-blue-900/30",
        iconColor: "text-blue-600 dark:text-blue-400",
        valueColor: "text-blue-700 dark:text-blue-400",
      }
    : {
        borderColor: "border-l-red-500",
        gradient: "from-red-50/80 to-white dark:from-red-950/40 dark:to-zinc-900",
        iconBg: "bg-red-100 dark:bg-red-900/30",
        iconColor: "text-red-600 dark:text-red-400",
        valueColor: "text-red-700 dark:text-red-400",
      };
}
