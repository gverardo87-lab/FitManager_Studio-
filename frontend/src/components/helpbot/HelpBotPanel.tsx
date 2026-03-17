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
  HelpCircle,
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
    <div className="flex items-center gap-1 px-3 py-2">
      <div className="flex gap-1">
        <span className="helpbot-typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground/50" />
        <span className="helpbot-typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground/50 [animation-delay:150ms]" />
        <span className="helpbot-typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground/50 [animation-delay:300ms]" />
      </div>
    </div>
  );
}

// ── Message Bubble ──

function MessageBubble({ message, onAction }: { message: BotMessage; onAction: (a: BotAction) => void }) {
  const isBot = message.sender === "bot";

  return (
    <div className={`flex ${isBot ? "justify-start" : "justify-end"} mb-2`}>
      <div
        className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
          isBot ? "bg-muted text-foreground" : "bg-primary text-primary-foreground"
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
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.actions.map((action) => (
              <button
                key={action.label}
                type="button"
                onClick={() => onAction(action)}
                className="inline-flex items-center gap-1 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:bg-accent"
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
  return (
    <div className="group rounded-lg border border-border bg-background p-3 transition-colors hover:bg-accent/50">
      <div className="flex items-start gap-2.5">
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-medium leading-tight">{action.title}</h4>
          <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{action.description}</p>
          {action.action ? (
            <button
              type="button"
              onClick={() => onAction(action.action!)}
              className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-primary transition-colors hover:text-primary/80"
            >
              {action.action.label}
              <ArrowRight className="h-3 w-3" />
            </button>
          ) : null}
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
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
            <Compass className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">Assistente</h2>
            {currentChapter ? (
              <p className="text-[10px] text-muted-foreground">{currentChapter.title}</p>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onBrowseChapters}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Esplora capitoli"
            title="Esplora capitoli"
          >
            <BookOpen className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Chiudi assistente"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Compass className="mb-2 h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              Cerca nelle FAQ o esplora i capitoli della guida.
            </p>
            <button
              type="button"
              onClick={onBrowseChapters}
              className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80"
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
      <form onSubmit={handleSubmit} className="border-t px-3 py-2">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Cerca nelle FAQ..."
            className="flex-1 rounded-lg border border-input bg-background px-3 py-1.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:ring-1 focus:ring-ring"
          />
          <Button type="submit" size="icon" variant="ghost" className="h-8 w-8 shrink-0">
            <Send className="h-4 w-4" />
            <span className="sr-only">Invia</span>
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
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onBack}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Torna alla chat"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <h2 className="text-sm font-semibold">Guida Completa</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Chiudi"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Chapter list */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        <p className="px-2 pb-2 text-[11px] text-muted-foreground">
          12 capitoli — dal primo cliente al monitoraggio progressi
        </p>
        {chapters.map((ch, i) => {
          const isCurrent = currentChapter?.id === ch.id;
          return (
            <button
              key={ch.id}
              type="button"
              onClick={() => onOpenChapter(ch.id)}
              className={`mb-1 flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-accent ${
                isCurrent ? "bg-primary/5 ring-1 ring-primary/20" : ""
              }`}
            >
              <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                isCurrent ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground"
              }`}>
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <ChapterIcon name={ch.icon} className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-sm font-medium">{ch.title}</span>
                </div>
                <p className="truncate text-[11px] text-muted-foreground">
                  {ch.actions.length} azioni · {ch.faqs.length > 0 ? `${ch.faqs.length} FAQ` : ""}
                </p>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/50" />
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
      {/* Header with breadcrumb */}
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onBack}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Torna ai capitoli"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <ChapterIcon name={chapter.icon} className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">{chapter.title}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Chiudi"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-1.5 pl-7 text-xs leading-relaxed text-muted-foreground">{chapter.intro}</p>

        {/* Tabs */}
        <div className="mt-2 flex gap-1 pl-7">
          <button
            type="button"
            onClick={() => setActiveTab("actions")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              activeTab === "actions"
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            Azioni ({chapter.actions.length})
          </button>
          {chapter.faqs.length > 0 ? (
            <button
              type="button"
              onClick={() => setActiveTab("faq")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                activeTab === "faq"
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              FAQ ({chapter.faqs.length})
            </button>
          ) : null}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 py-2">
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
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-primary/30 bg-primary/5 px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/10"
              >
                <Compass className="h-3.5 w-3.5" />
                Lancia tour guidato per {chapter.title}
              </button>
            ) : null}
          </div>
        ) : (
          <div className="space-y-3">
            {chapter.faqs.map((faq, i) => (
              <div key={i} className="rounded-lg border border-border bg-background p-3">
                <div className="flex items-start gap-2">
                  <HelpCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <div>
                    <h4 className="text-sm font-medium">{faq.question}</h4>
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
      className="helpbot-panel fixed bottom-20 right-6 z-[9998] flex h-[520px] w-80 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-xl animate-in fade-in-0 slide-in-from-bottom-2 duration-200"
      role="dialog"
      aria-label="Assistente FitManager"
    >
      {content}
    </div>,
    document.body,
  );
}
