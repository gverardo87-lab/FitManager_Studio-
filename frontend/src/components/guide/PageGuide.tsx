// src/components/guide/PageGuide.tsx
/**
 * PageGuide — Bussola contestuale adattiva al livello trainer.
 *
 * Sostituisce HelpBot (1225 LOC) con un Popover leggero (~130 LOC).
 * Mostra tips filtrati per maturity level, FAQ e link video.
 * FAB fisso in basso a destra. Self-contained: zero props.
 */

"use client";

import { useState, useMemo } from "react";
import { usePathname } from "next/navigation";
import {
  ChevronDown,
  HelpCircle,
  Lightbulb,
  MessageCircleQuestion,
  Play,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useTrainerMaturity } from "@/hooks/useTrainerMaturity";
import { getPageGuide } from "@/lib/guide-registry";
import { getVideoGuide } from "@/lib/video-guides";

export function PageGuide() {
  const pathname = usePathname();
  const { level } = useTrainerMaturity();
  const guide = useMemo(() => getPageGuide(pathname, level), [pathname, level]);

  // Non mostrare su pagine senza guida (es. /setup, /login)
  if (!guide) return null;

  const video = guide.videoId ? getVideoGuide(guide.videoId) : null;
  const hasContent = guide.tips.length > 0 || guide.faqs.length > 0 || (video?.ready ?? false);

  if (!hasContent) return null;

  return (
    <div className="fixed bottom-5 right-5 z-40">
      <Popover>
        <PopoverTrigger asChild>
          <Button
            size="icon"
            variant="outline"
            className="h-10 w-10 rounded-full border-border/80 bg-background/95 shadow-lg backdrop-blur transition-all hover:shadow-xl"
            aria-label="Guida pagina"
          >
            <HelpCircle className="h-5 w-5 text-muted-foreground" />
          </Button>
        </PopoverTrigger>
        <PopoverContent
          side="top"
          align="end"
          className="w-80 max-h-[28rem] overflow-y-auto p-0"
          sideOffset={12}
        >
          <PageGuideContent guide={guide} video={video} />
        </PopoverContent>
      </Popover>
    </div>
  );
}

// ── Content (separated for readability, NOT a dynamic component) ──

interface PageGuideContentProps {
  guide: NonNullable<ReturnType<typeof getPageGuide>>;
  video: ReturnType<typeof getVideoGuide> | null;
}

function PageGuideContent({ guide, video }: PageGuideContentProps) {
  return (
    <div className="divide-y">
      {/* ── Header ── */}
      <div className="px-4 py-3">
        <p className="text-sm font-medium">{guide.pageLabel}</p>
      </div>

      {/* ── Tips ── */}
      {guide.tips.length > 0 && (
        <div className="space-y-2 px-4 py-3">
          {guide.tips.map((tip, i) => (
            <div key={i} className="flex items-start gap-2">
              <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
              <p className="text-xs leading-relaxed text-muted-foreground">
                {tip.text}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* ── Video link ── */}
      {video?.ready && (
        <div className="px-4 py-3">
          <a
            href={`/guida#${video.id}`}
            className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/5"
          >
            <Play className="h-3.5 w-3.5" />
            {video.title}
            <span className="ml-auto text-[10px] tabular-nums text-muted-foreground">
              {Math.floor(video.durationSec / 60)}:{String(video.durationSec % 60).padStart(2, "0")}
            </span>
          </a>
        </div>
      )}

      {/* ── FAQ ── */}
      {guide.faqs.length > 0 && (
        <div className="space-y-1 px-4 py-3">
          <div className="mb-2 flex items-center gap-1.5">
            <MessageCircleQuestion className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              FAQ
            </span>
          </div>
          {guide.faqs.map((faq) => (
            <FaqItem key={faq.question} question={faq.question} answer={faq.answer} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── FAQ collapsible ──

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between gap-2 rounded px-1 py-1 text-left text-xs transition-colors hover:bg-muted/40"
        >
          <span className="font-medium">{question}</span>
          <ChevronDown
            className={`h-3 w-3 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
          />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <p className="px-1 pb-1 pt-0.5 text-[11px] leading-relaxed text-muted-foreground">
          {answer}
        </p>
      </CollapsibleContent>
    </Collapsible>
  );
}
