// ════════════════════════════════════════════════════════════
// HelpBotPanel — Pannello Bussola
//
// 3 viste: chat, chapters (indice 12 capitoli),
// chapter-detail (azioni + FAQ).
// Desktop: fixed portal. Mobile: Sheet bottom.
// ════════════════════════════════════════════════════════════

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  X, Send, Compass, ArrowRight, ArrowLeft, ChevronRight, BookOpen,
  UserPlus, HeartPulse, FileText, Calendar, Wallet, Dumbbell,
  ClipboardList, Activity, Gauge, RefreshCw, Shield, LayoutDashboard,
  HelpCircle, Crosshair, Search, MapPin,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import type { BotAction, BotMessage } from "@/lib/helpbot-types";
import type { Chapter, ChapterAction } from "@/lib/helpbot-data";
import type { HelpBotView } from "@/hooks/useHelpBot";

// ── Icon map ──

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  UserPlus, HeartPulse, FileText, Calendar, Wallet, Dumbbell,
  ClipboardList, Activity, Gauge, RefreshCw, Shield, LayoutDashboard,
};

function ChapterIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICON_MAP[name] ?? BookOpen;
  return <Icon className={className} />;
}

// ── Props ──

interface HelpBotPanelProps {
  open: boolean;
  messages: BotMessage[];
  isTyping: boolean;
  view: HelpBotView;
  currentChapter: Chapter | null;
  selectedChapter: Chapter | null;
  chapters: Chapter[];
  onClose: () => void;
  onAction: (action: BotAction) => void;
  onSearch: (query: string) => void;
  onBrowseChapters: () => void;
  onOpenChapter: (id: string) => void;
  onBackToChat: () => void;
}

// ── Typing Indicator ──

function TypingIndicator() {
  return (
    <div className="helpbot-msg-enter flex items-start gap-2 px-3 py-2">
      <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-teal-100 dark:bg-teal-900/40">
        <Compass className="h-2.5 w-2.5 text-teal-600 dark:text-teal-400" />
      </div>
      <div className="flex gap-1 pt-1.5">
        <span className="helpbot-typing-dot h-1.5 w-1.5 rounded-full bg-teal-500/60" />
        <span className="helpbot-typing-dot h-1.5 w-1.5 rounded-full bg-teal-500/60 [animation-delay:150ms]" />
        <span className="helpbot-typing-dot h-1.5 w-1.5 rounded-full bg-teal-500/60 [animation-delay:300ms]" />
      </div>
    </div>
  );
}

// ── Message Bubble ──

function MessageBubble({ message, onAction }: { message: BotMessage; onAction: (a: BotAction) => void }) {
  const isBot = message.sender === "bot";

  return (
    <div className={`helpbot-msg-enter flex ${isBot ? "justify-start" : "justify-end"} mb-3`}>
      {isBot ? (
        <div className="flex items-start gap-2 max-w-[88%]">
          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-teal-100 dark:bg-teal-900/40 mt-0.5">
            <Compass className="h-2.5 w-2.5 text-teal-600 dark:text-teal-400" />
          </div>
          <div className="rounded-2xl rounded-tl-md bg-white px-3.5 py-2.5 text-[13px] leading-relaxed text-foreground shadow-sm ring-1 ring-black/[0.04] dark:bg-zinc-800 dark:ring-white/[0.06]">
            {message.text.split("\n").map((line, i) => (
              <p key={i} className={i > 0 ? "mt-1" : ""}>
                {line.split(/\*\*(.*?)\*\*/).map((part, j) =>
                  j % 2 === 1 ? <strong key={j} className="font-semibold text-teal-700 dark:text-teal-300">{part}</strong> : part
                )}
              </p>
            ))}

            {message.actions && message.actions.length > 0 ? (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {message.actions.map((action) => (
                  <button
                    key={action.label}
                    type="button"
                    onClick={() => onAction(action)}
                    className="inline-flex items-center gap-1 rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-700 ring-1 ring-teal-200/60 transition-all hover:bg-teal-100 hover:ring-teal-300/80 dark:bg-teal-900/30 dark:text-teal-300 dark:ring-teal-700/40 dark:hover:bg-teal-900/50"
                  >
                    {action.label}
                    <ArrowRight className="h-3 w-3" />
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-gradient-to-br from-teal-600 to-emerald-700 px-3.5 py-2.5 text-[13px] leading-relaxed text-white shadow-sm">
          {message.text.split("\n").map((line, i) => (
            <p key={i} className={i > 0 ? "mt-1" : ""}>{line}</p>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Chapter Action Card ──

function ActionCard({ action, index, onAction }: { action: ChapterAction; index: number; onAction: (a: BotAction) => void }) {
  const isSpotlight = action.action?.type === "spotlight";

  return (
    <div className={`helpbot-msg-enter group rounded-xl border p-3 transition-all duration-200 hover:-translate-y-0.5 ${
      isSpotlight
        ? "border-teal-200/60 bg-gradient-to-r from-teal-50/50 via-white to-emerald-50/30 shadow-sm hover:shadow-md hover:border-teal-300 dark:border-teal-800/40 dark:from-teal-950/20 dark:via-zinc-900 dark:to-emerald-950/10"
        : "border-border bg-white hover:bg-accent/50 hover:shadow-sm dark:bg-zinc-800/50"
    }`} style={{ animationDelay: `${index * 50}ms` }}>
      <div className="flex items-start gap-2.5">
        <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-[10px] font-bold ${
          isSpotlight
            ? "bg-teal-600 text-white shadow-sm"
            : "bg-zinc-100 text-zinc-500 dark:bg-zinc-700 dark:text-zinc-400"
        }`}>
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="text-[13px] font-semibold leading-tight">{action.title}</h4>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground/80">{action.description}</p>
          {action.action ? (
            <button
              type="button"
              onClick={() => onAction(action.action!)}
              className={`mt-2 inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase transition-all ${
                isSpotlight
                  ? "bg-teal-600 text-white shadow-sm hover:bg-teal-700 hover:shadow-md"
                  : "text-teal-600 hover:bg-teal-50 dark:text-teal-400 dark:hover:bg-teal-950/30"
              }`}
            >
              {isSpotlight ? (
                <Crosshair className="h-3 w-3" />
              ) : (
                <ArrowRight className="h-3 w-3" />
              )}
              {action.action.label}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ── Panel Header ──

function PanelHeader({ title, subtitle, onBack, onExtra, extraIcon: ExtraIcon, onClose }: {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  onExtra?: () => void;
  extraIcon?: React.ComponentType<{ className?: string }>;
  onClose: () => void;
}) {
  return (
    <div className="helpbot-header relative overflow-hidden border-b px-4 py-3.5">
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-teal-600 via-teal-700 to-emerald-800" />
      <div className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-white/8 blur-xl" />
      <div className="pointer-events-none absolute -left-4 bottom-0 h-12 w-12 rounded-full bg-emerald-400/10 blur-lg" />
      <div className="relative flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              className="rounded-lg p-1 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Indietro"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          ) : (
            <div className="helpbot-compass-icon flex h-8 w-8 items-center justify-center rounded-xl bg-white/15 shadow-inner backdrop-blur-sm">
              <Compass className="h-4 w-4 text-white" />
            </div>
          )}
          <div>
            <h2 className="text-[13px] font-bold tracking-wide text-white">{title}</h2>
            {subtitle ? (
              <p className="text-[10px] font-medium text-white/50">{subtitle}</p>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-0.5">
          {onExtra && ExtraIcon ? (
            <button
              type="button"
              onClick={onExtra}
              className="rounded-lg p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Esplora capitoli"
            >
              <ExtraIcon className="h-4 w-4" />
            </button>
          ) : null}
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
            aria-label="Chiudi"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Chat View ──

function ChatView({ messages, isTyping, currentChapter, onClose, onAction, onSearch, onBrowseChapters }: {
  messages: BotMessage[];
  isTyping: boolean;
  currentChapter: Chapter | null;
  onClose: () => void;
  onAction: (a: BotAction) => void;
  onSearch: (q: string) => void;
  onBrowseChapters: () => void;
}) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, isTyping]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q) return;
    if (q.startsWith(">")) {
      window.dispatchEvent(new Event("open-command-palette"));
      onClose();
      return;
    }
    onSearch(q);
    setInput("");
  }, [input, onSearch, onClose]);

  return (
    <>
      <PanelHeader
        title="Bussola"
        subtitle={currentChapter?.title}
        onExtra={onBrowseChapters}
        extraIcon={BookOpen}
        onClose={onClose}
      />

      {/* Messages */}
      <div ref={scrollRef} className="helpbot-body flex-1 overflow-y-auto px-3 py-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            {/* Animated compass */}
            <div className="helpbot-compass-hero relative flex h-16 w-16 items-center justify-center">
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-teal-100 to-emerald-100 dark:from-teal-900/30 dark:to-emerald-900/20" />
              <div className="helpbot-compass-ring absolute inset-1 rounded-[14px] border-2 border-dashed border-teal-300/50 dark:border-teal-600/30" />
              <Compass className="relative h-7 w-7 text-teal-600 dark:text-teal-400" />
            </div>

            <h3 className="mt-4 text-sm font-bold tracking-tight text-foreground">Come posso orientarti?</h3>
            <p className="mt-1.5 max-w-[220px] text-[11px] leading-relaxed text-muted-foreground">
              Cerca nelle FAQ oppure esplora i 12 capitoli della guida operativa
            </p>

            {/* Quick actions */}
            <div className="mt-5 flex flex-col gap-2 w-full max-w-[220px]">
              <button
                type="button"
                onClick={onBrowseChapters}
                className="flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-700 px-4 py-2.5 text-left text-white shadow-sm transition-all hover:shadow-md"
              >
                <BookOpen className="h-4 w-4 shrink-0" />
                <div>
                  <span className="text-xs font-semibold">Esplora i capitoli</span>
                  <span className="block text-[10px] text-white/60">12 sezioni guidate</span>
                </div>
              </button>
              <button
                type="button"
                onClick={() => onSearch("come")}
                className="flex items-center gap-2.5 rounded-xl bg-white px-4 py-2.5 text-left shadow-sm ring-1 ring-black/[0.04] transition-all hover:shadow-md dark:bg-zinc-800 dark:ring-white/[0.06]"
              >
                <HelpCircle className="h-4 w-4 shrink-0 text-teal-600" />
                <div>
                  <span className="text-xs font-semibold text-foreground">Domande frequenti</span>
                  <span className="block text-[10px] text-muted-foreground">Le risposte piu' cercate</span>
                </div>
              </button>
            </div>
          </div>
        ) : null}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} onAction={onAction} />
        ))}

        {isTyping ? <TypingIndicator /> : null}
      </div>

      {/* Input bar */}
      <form onSubmit={handleSubmit} className="border-t bg-white/80 px-3 py-2.5 backdrop-blur-sm dark:bg-zinc-900/80">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/40" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Cerca nelle FAQ..."
              className="w-full rounded-xl bg-zinc-50 py-2 pl-8 pr-3 text-[13px] outline-none transition-all placeholder:text-muted-foreground/40 focus:bg-white focus:ring-2 focus:ring-teal-500/30 dark:bg-zinc-800 dark:focus:bg-zinc-700"
            />
          </div>
          <Button type="submit" size="icon" className="h-8 w-8 shrink-0 rounded-xl bg-teal-600 text-white shadow-sm hover:bg-teal-700">
            <Send className="h-3.5 w-3.5" />
            <span className="sr-only">Cerca</span>
          </Button>
        </div>
      </form>
    </>
  );
}

// ── Chapters Index View ──

function ChaptersView({ chapters, currentChapter, onOpenChapter, onBack, onClose }: {
  chapters: Chapter[];
  currentChapter: Chapter | null;
  onOpenChapter: (id: string) => void;
  onBack: () => void;
  onClose: () => void;
}) {
  return (
    <>
      <PanelHeader
        title="Guida Operativa"
        subtitle="12 capitoli"
        onBack={onBack}
        onClose={onClose}
      />

      {/* Chapter list */}
      <div className="helpbot-body flex-1 overflow-y-auto p-2">
        <div className="px-2 pb-2 flex items-center gap-1.5">
          <MapPin className="h-3 w-3 text-teal-500" />
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
            Dal primo cliente al monitoraggio
          </p>
        </div>
        {chapters.map((ch, i) => {
          const isCurrent = currentChapter?.id === ch.id;
          return (
            <button
              key={ch.id}
              type="button"
              onClick={() => onOpenChapter(ch.id)}
              className={`helpbot-msg-enter mb-0.5 flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left transition-all duration-200 ${
                isCurrent
                  ? "bg-gradient-to-r from-teal-50 via-teal-50/80 to-emerald-50/50 shadow-sm ring-1 ring-teal-200/60 dark:from-teal-950/30 dark:to-emerald-950/10 dark:ring-teal-700/30"
                  : "hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
              }`}
              style={{ animationDelay: `${i * 30}ms` }}
            >
              <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[11px] font-bold transition-colors ${
                isCurrent
                  ? "bg-teal-600 text-white shadow-sm"
                  : "bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
              }`}>
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <ChapterIcon name={ch.icon} className={`h-3.5 w-3.5 ${isCurrent ? "text-teal-600 dark:text-teal-400" : "text-zinc-400 dark:text-zinc-500"}`} />
                  <span className={`text-[13px] font-semibold ${isCurrent ? "text-teal-700 dark:text-teal-300" : "text-foreground"}`}>{ch.title}</span>
                </div>
                <p className="mt-0.5 truncate text-[10px] text-muted-foreground/60">
                  {ch.actions.length} azioni{ch.faqs.length > 0 ? ` · ${ch.faqs.length} FAQ` : ""}
                </p>
              </div>
              <ChevronRight className={`h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5 ${isCurrent ? "text-teal-500" : "text-zinc-300 dark:text-zinc-600"}`} />
            </button>
          );
        })}
      </div>
    </>
  );
}

// ── Chapter Detail View ──

function ChapterDetailView({ chapter, onAction, onBack, onClose }: {
  chapter: Chapter;
  onAction: (a: BotAction) => void;
  onBack: () => void;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"actions" | "faq">("actions");

  return (
    <>
      <PanelHeader
        title={chapter.title}
        onBack={onBack}
        onClose={onClose}
      />

      {/* Intro + Tabs */}
      <div className="border-b bg-zinc-50/80 px-4 py-3 dark:bg-zinc-900/50">
        <p className="text-[11px] leading-relaxed text-muted-foreground/80">{chapter.intro}</p>
        <div className="mt-2.5 flex gap-1">
          <button
            type="button"
            onClick={() => setActiveTab("actions")}
            className={`rounded-lg px-3 py-1 text-[11px] font-semibold tracking-wide transition-all ${
              activeTab === "actions"
                ? "bg-teal-600 text-white shadow-sm"
                : "text-muted-foreground/60 hover:bg-zinc-200/60 dark:hover:bg-zinc-700/50"
            }`}
          >
            Azioni ({chapter.actions.length})
          </button>
          {chapter.faqs.length > 0 ? (
            <button
              type="button"
              onClick={() => setActiveTab("faq")}
              className={`rounded-lg px-3 py-1 text-[11px] font-semibold tracking-wide transition-all ${
                activeTab === "faq"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-muted-foreground/60 hover:bg-zinc-200/60 dark:hover:bg-zinc-700/50"
              }`}
            >
              FAQ ({chapter.faqs.length})
            </button>
          ) : null}
        </div>
      </div>

      {/* Content */}
      <div className="helpbot-body flex-1 overflow-y-auto px-3 py-2.5">
        {activeTab === "actions" ? (
          <div className="space-y-2">
            {chapter.actions.map((action, i) => (
              <ActionCard key={action.id} action={action} index={i} onAction={onAction} />
            ))}

            {/* Mini-tour CTA */}
            {chapter.miniTourSteps.length > 0 ? (
              <button
                type="button"
                onClick={() => onAction({ label: "Tour", type: "mini-tour", payload: chapter.routePattern })}
                className="helpbot-msg-enter mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-teal-50 to-emerald-50 px-3 py-3 text-xs font-semibold text-teal-700 ring-1 ring-teal-200/60 transition-all hover:shadow-md hover:ring-teal-300 dark:from-teal-950/20 dark:to-emerald-950/10 dark:text-teal-300 dark:ring-teal-700/30"
                style={{ animationDelay: `${chapter.actions.length * 50}ms` }}
              >
                <Compass className="h-4 w-4" />
                Tour guidato — {chapter.title}
              </button>
            ) : null}
          </div>
        ) : (
          <div className="space-y-2.5">
            {chapter.faqs.map((faq, i) => (
              <div key={i} className="helpbot-msg-enter rounded-xl bg-white p-3.5 shadow-sm ring-1 ring-black/[0.04] dark:bg-zinc-800 dark:ring-white/[0.06]" style={{ animationDelay: `${i * 50}ms` }}>
                <div className="flex items-start gap-2.5">
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-teal-100 dark:bg-teal-900/40">
                    <HelpCircle className="h-3 w-3 text-teal-600 dark:text-teal-400" />
                  </div>
                  <div>
                    <h4 className="text-[13px] font-semibold leading-tight">{faq.question}</h4>
                    <p className="mt-1.5 text-[11px] leading-relaxed text-muted-foreground/80">{faq.answer}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

// ── Main Component ──

export function HelpBotPanel(props: HelpBotPanelProps) {
  const { open, onClose, view } = props;
  const [mounted, setMounted] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    setMounted(true);
    setIsMobile(window.innerWidth < 1024);

    const handleResize = () => setIsMobile(window.innerWidth < 1024);
    window.addEventListener("resize", handleResize, { passive: true });
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (!mounted || !open) return null;

  const content = (
    <div className="flex h-full flex-col">
      {view === "chat" ? (
        <ChatView
          messages={props.messages}
          isTyping={props.isTyping}
          currentChapter={props.currentChapter}
          onClose={onClose}
          onAction={props.onAction}
          onSearch={props.onSearch}
          onBrowseChapters={props.onBrowseChapters}
        />
      ) : view === "chapters" ? (
        <ChaptersView
          chapters={props.chapters}
          currentChapter={props.currentChapter}
          onOpenChapter={props.onOpenChapter}
          onBack={props.onBackToChat}
          onClose={onClose}
        />
      ) : props.selectedChapter ? (
        <ChapterDetailView
          chapter={props.selectedChapter}
          onAction={props.onAction}
          onBack={props.onBrowseChapters}
          onClose={onClose}
        />
      ) : null}
    </div>
  );

  // Mobile: Sheet bottom
  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
        <SheetContent side="bottom" className="h-[75vh] p-0">
          <SheetTitle className="sr-only">Bussola FitManager</SheetTitle>
          {content}
        </SheetContent>
      </Sheet>
    );
  }

  // Desktop: fixed panel
  return createPortal(
    <div
      className="helpbot-panel fixed bottom-20 right-6 z-[9998] flex h-[560px] w-[360px] flex-col overflow-hidden rounded-2xl border-0 bg-zinc-50 shadow-2xl shadow-black/20 ring-1 ring-black/[0.08] animate-in fade-in-0 slide-in-from-bottom-4 duration-300 dark:bg-zinc-900 dark:shadow-black/50 dark:ring-white/[0.06]"
      role="dialog"
      aria-label="Bussola FitManager"
    >
      {content}
    </div>,
    document.body,
  );
}
