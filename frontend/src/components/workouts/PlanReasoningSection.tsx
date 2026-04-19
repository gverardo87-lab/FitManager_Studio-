// src/components/workouts/PlanReasoningSection.tsx
"use client";

/**
 * Ragionamento Scientifico — Warning strutturati con icone e contesto.
 *
 * Categorizza i warning del motore scientifico per tipo (volume, frequenza,
 * recupero, equilibrio) con icone e colori semantici. Permette al trainer
 * di capire PERCHE' il motore ha segnalato un problema.
 *
 * Dati: TSAnalisiPiano.warnings (string[] gia' in italiano leggibile).
 */

import { useState } from "react";
import {
  BookOpen,
  Dumbbell,
  Clock,
  RefreshCw,
  Scale,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

// ════════════════════════════════════════════════════════════
// CATEGORIZZAZIONE WARNING
// ════════════════════════════════════════════════════════════

interface WarningCategory {
  icon: React.ComponentType<{ className?: string }>;
  colorClass: string;
  bgClass: string;
}

const CATEGORY_VOLUME: WarningCategory = {
  icon: Dumbbell,
  colorClass: "text-amber-600 dark:text-amber-400",
  bgClass: "bg-amber-50 dark:bg-amber-950/30",
};

const CATEGORY_FREQUENCY: WarningCategory = {
  icon: Clock,
  colorClass: "text-amber-600 dark:text-amber-400",
  bgClass: "bg-amber-50 dark:bg-amber-950/30",
};

const CATEGORY_RECOVERY: WarningCategory = {
  icon: RefreshCw,
  colorClass: "text-red-600 dark:text-red-400",
  bgClass: "bg-red-50 dark:bg-red-950/30",
};

const CATEGORY_BALANCE: WarningCategory = {
  icon: Scale,
  colorClass: "text-amber-600 dark:text-amber-400",
  bgClass: "bg-amber-50 dark:bg-amber-950/30",
};

const CATEGORY_DEFAULT: WarningCategory = {
  icon: AlertTriangle,
  colorClass: "text-zinc-600 dark:text-zinc-400",
  bgClass: "bg-zinc-50 dark:bg-zinc-950/30",
};

function categorizeWarning(w: string): WarningCategory {
  const lower = w.toLowerCase();
  if (lower.includes("volume insufficiente") || lower.includes("sotto mev") || lower.includes("serie/sett")) {
    return CATEGORY_VOLUME;
  }
  if (lower.includes("frequenza")) {
    return CATEGORY_FREQUENCY;
  }
  if (lower.includes("recupero") || lower.includes("recovery") || lower.includes("sovrapposizione")) {
    return CATEGORY_RECOVERY;
  }
  if (lower.includes("squilibrio") || lower.includes("push") || lower.includes("pull") ||
      lower.includes("quad") || lower.includes("ham") || lower.includes("anteriore") ||
      lower.includes("posteriore") || lower.includes("target") || lower.includes("troppo")) {
    return CATEGORY_BALANCE;
  }
  return CATEGORY_DEFAULT;
}

// ════════════════════════════════════════════════════════════
// COMPONENTE
// ════════════════════════════════════════════════════════════

interface PlanReasoningSectionProps {
  warnings: string[];
}

export function PlanReasoningSection({ warnings }: PlanReasoningSectionProps) {
  const [isOpen, setIsOpen] = useState(true);
  const count = warnings.length;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4 border-l-violet-500/50">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-violet-600" />
                <CardTitle className="text-sm font-semibold">Ragionamento Scientifico</CardTitle>
                {count > 0 ? (
                  <Badge className="text-xs tabular-nums bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                    {count}
                  </Badge>
                ) : (
                  <Badge className="text-xs bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    OK
                  </Badge>
                )}
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 px-4 pb-4">
            {count === 0 ? (
              <div className="flex items-center gap-2 px-3 py-2.5 rounded-md bg-emerald-50 dark:bg-emerald-950/30">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <p className="text-xs text-emerald-700 dark:text-emerald-300">
                  Piano scientificamente bilanciato — nessuna segnalazione.
                </p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {warnings.map((w, i) => {
                  const cat = categorizeWarning(w);
                  const Icon = cat.icon;
                  return (
                    <div
                      key={i}
                      className={`flex items-start gap-2.5 px-3 py-2 rounded-md ${cat.bgClass}`}
                    >
                      <Icon className={`h-3.5 w-3.5 mt-0.5 shrink-0 ${cat.colorClass}`} />
                      <span className="text-xs text-foreground leading-relaxed">{w}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
