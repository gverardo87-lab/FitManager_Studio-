// ════════════════════════════════════════════════════════════
// HelpBotPanel — Pannello chat + capitoli + azioni
//
// 3 viste: chat (messaggi), chapters (indice 12 capitoli),
// chapter-detail (azioni + FAQ del capitolo selezionato).
// Desktop: fixed portal. Mobile: Sheet bottom.
// ════════════════════════════════════════════════════════════

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  X, Send, Compass, ArrowRight, ArrowLeft, ChevronRight, BookOpen,
  UserPlus, HeartPulse, FileText, Calendar, Wallet, Dumbbell,
  ClipboardList, Activity, Gauge, RefreshCw, Shield, LayoutDashboard,
  HelpCircle, Crosshair, Search, Sparkles,
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
    <div className="helpbot-msg-enter flex items-center gap-1.5 px-3 py-2">
      <div className="flex gap-1">
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
    <div className={`helpbot-msg-enter flex ${isBot ? "justify-start" : "justify-end"} mb-2`}>
      <div
        className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
          isBot
            ? "rounded-tl-md bg-gradient-to-br from-muted to-muted/70 text-foreground"
            : "rounded-tr-md bg-gradient-to-br from-teal-600 to-emerald-700 text-white"
        }`}
      >
        {message.text.split("\n").map((line, i) => (
          <p key={i} className={i > 0 ? "mt-1" : ""}>
            {line.split(/\*\*(.*?)\*\*/).map((part, j) =>
              j % 2 === 1 ? <strong key={j}>{part}</strong> : part
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
                className="inline-flex items-center gap-1 rounded-lg border border-white/20 bg-white/10 px-2.5 py-1 text-xs font-medium text-inherit backdrop-blur-sm transition-colors hover:bg-white/20"
              >
                {action.label}
                <ArrowRight className="h-3 w-3" />
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

// ── Chapter Action Card ──

function ActionCard({ action, index, onAction }: { action: ChapterAction; index: number; onAction: (a: BotAction) => void }) {
  const isSpotlight = action.action?.type === "spotlight";

  return (
    <div className={`helpbot-msg-enter group rounded-xl border p-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-sm ${
      isSpotlight
        ? "border-teal-200/60 bg-gradient-to-br from-teal-50/40 to-white hover:border-teal-300/80 dark:border-teal-800/40 dark:from-teal-950/20 dark:to-zinc-900"
        : "border-border bg-background hover:bg-accent/50"
    }`} style={{ animationDelay: `${index * 40}ms` }}>
      <div className="flex items-start gap-2.5">
        <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
          isSpotlight
            ? "bg-teal-100 text-teal-700 dark:bg-teal-900/50 dark:text-teal-300"
            : "bg-primary/10 text-primary"
        }`}>
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="text-[13px] font-medium leading-tight">{action.title}</h4>
          <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{action.description}</p>
          {action.action ? (
            <button
              type="button"
              onClick={() => onAction(action.action!)}
              className={`mt-2 inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                isSpotlight
                  ? "bg-teal-600 text-white shadow-sm hover:bg-teal-700"
                  : "text-primary hover:bg-primary/10"
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
    <div className="relative overflow-hidden border-b bg-gradient-to-r from-teal-600 via-teal-700 to-emerald-800 px-4 py-3">
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/5 blur-2xl" />
      <div className="relative flex items-center justify-between">
        <div className="flex items-center gap-2">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              className="rounded-md p-1 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Indietro"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/15 backdrop-blur-sm">
              <Sparkles className="h-3.5 w-3.5 text-white" />
            </div>
          )}
          <div>
            <h2 className="text-sm font-semibold text-white">{title}</h2>
            {subtitle ? (
              <p className="text-[10px] text-white/60">{subtitle}</p>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-0.5">
          {onExtra && ExtraIcon ? (
            <button
              type="button"
              onClick={onExtra}
              className="rounded-md p-1.5 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Esplora capitoli"
            >
              <ExtraIcon className="h-4 w-4" />
            </button>
          ) : null}
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
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
        title="Assistente"
        subtitle={currentChapter?.title}
        onExtra={onBrowseChapters}
        extraIcon={BookOpen}
        onClose={onClose}
      />

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-100 to-emerald-100 dark:from-teal-900/40 dark:to-emerald-900/30">
              <Compass className="h-6 w-6 text-teal-600 dark:text-teal-400" />
            </div>
            <p className="mt-3 text-sm font-medium text-foreground">Come posso aiutarti?</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Cerca nelle FAQ o esplora i capitoli della guida
            </p>
            <button
              type="button"
              onClick={onBrowseChapters}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm transition-colors hover:bg-teal-700"
            >
              <BookOpen className="h-3.5 w-3.5" />
              Esplora i 12 capitoli
            </button>
          </div>
        ) : null}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} onAction={onAction} />
        ))}

        {isTyping ? <TypingIndicator /> : null}
      </div>

      {/* Input bar */}
      <form onSubmit={handleSubmit} className="border-t bg-muted/30 px-3 py-2.5">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/50" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Cerca nelle FAQ..."
              className="w-full rounded-lg border border-input bg-background py-1.5 pl-8 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground/60 focus:ring-1 focus:ring-teal-500/50"
            />
          </div>
          <Button type="submit" size="icon" variant="ghost" className="h-8 w-8 shrink-0 text-teal-600 hover:bg-teal-50 hover:text-teal-700 dark:hover:bg-teal-950/50">
            <Send className="h-4 w-4" />
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
        title="Guida Completa"
        subtitle="12 capitoli"
        onBack={onBack}
        onClose={onClose}
      />

      {/* Chapter list */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <p className="px-2 pb-2 text-[11px] text-muted-foreground">
          Dal primo cliente al monitoraggio progressi
        </p>
        {chapters.map((ch, i) => {
          const isCurrent = currentChapter?.id === ch.id;
          return (
            <button
              key={ch.id}
              type="button"
              onClick={() => onOpenChapter(ch.id)}
              className={`helpbot-msg-enter mb-1 flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2.5 text-left transition-all duration-200 hover:bg-accent ${
                isCurrent
                  ? "border-l-2 border-l-teal-500 bg-gradient-to-r from-teal-50/80 to-transparent dark:from-teal-950/30"
                  : ""
              }`}
              style={{ animationDelay: `${i * 30}ms` }}
            >
              <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold transition-colors ${
                isCurrent
                  ? "bg-teal-600 text-white shadow-sm"
                  : "bg-muted text-muted-foreground group-hover:bg-primary/10"
              }`}>
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <ChapterIcon name={ch.icon} className={`h-3.5 w-3.5 ${isCurrent ? "text-teal-600 dark:text-teal-400" : "text-muted-foreground"}`} />
                  <span className={`text-sm font-medium ${isCurrent ? "text-teal-700 dark:text-teal-300" : ""}`}>{ch.title}</span>
                </div>
                <p className="truncate text-[11px] text-muted-foreground">
                  {ch.actions.length} azioni{ch.faqs.length > 0 ? ` · ${ch.faqs.length} FAQ` : ""}
                </p>
              </div>
              <ChevronRight className={`h-4 w-4 shrink-0 transition-transform ${isCurrent ? "text-teal-500" : "text-muted-foreground/40"}`} />
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
      <div className="border-b bg-muted/20 px-4 py-3">
        <p className="text-xs leading-relaxed text-muted-foreground">{chapter.intro}</p>
        <div className="mt-2.5 flex gap-1">
          <button
            type="button"
            onClick={() => setActiveTab("actions")}
            className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
              activeTab === "actions"
                ? "bg-teal-600 text-white shadow-sm"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            Azioni ({chapter.actions.length})
          </button>
          {chapter.faqs.length > 0 ? (
            <button
              type="button"
              onClick={() => setActiveTab("faq")}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                activeTab === "faq"
                  ? "bg-teal-600 text-white shadow-sm"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              FAQ ({chapter.faqs.length})
            </button>
          ) : null}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 py-2.5">
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
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-teal-400/40 bg-gradient-to-r from-teal-50/50 to-emerald-50/30 px-3 py-2.5 text-xs font-medium text-teal-700 transition-all hover:border-teal-400/70 hover:shadow-sm dark:from-teal-950/20 dark:to-emerald-950/10 dark:text-teal-300"
              >
                <Compass className="h-3.5 w-3.5" />
                Tour guidato — {chapter.title}
              </button>
            ) : null}
          </div>
        ) : (
          <div className="space-y-2.5">
            {chapter.faqs.map((faq, i) => (
              <div key={i} className="helpbot-msg-enter rounded-xl border border-border bg-background p-3" style={{ animationDelay: `${i * 50}ms` }}>
                <div className="flex items-start gap-2">
                  <HelpCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600" />
                  <div>
                    <h4 className="text-[13px] font-medium">{faq.question}</h4>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{faq.answer}</p>
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
          <SheetTitle className="sr-only">Assistente FitManager</SheetTitle>
          {content}
        </SheetContent>
      </Sheet>
    );
  }

  // Desktop: fixed panel
  return createPortal(
    <div
      className="helpbot-panel fixed bottom-20 right-6 z-[9998] flex h-[540px] w-[340px] flex-col overflow-hidden rounded-2xl border border-border/50 bg-card shadow-2xl shadow-teal-900/10 animate-in fade-in-0 slide-in-from-bottom-3 duration-300"
      role="dialog"
      aria-label="Assistente FitManager"
    >
      {content}
    </div>,
    document.body,
  );
}
