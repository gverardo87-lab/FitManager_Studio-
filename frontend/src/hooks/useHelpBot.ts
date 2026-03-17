// ════════════════════════════════════════════════════════════
// useHelpBot — Hook centrale del dispatcher contestuale
//
// State: open, messages, currentChapter, hasUnread, onboarding.
// Consuma usePathname + useGuideProgress.
// Zero API call — legge React Query cache per proactive triggers.
// ════════════════════════════════════════════════════════════

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { useGuideProgress } from "./useGuideProgress";
import {
  resolveChapter,
  resolveSpotlight,
  CHAPTERS,
  ONBOARDING_STEPS,
  ONBOARDING_TOUR_RESPONSE,
  ONBOARDING_SKIP_RESPONSE,
  PROACTIVE_TRIGGERS,
} from "@/lib/helpbot-data";
import type { Chapter } from "@/lib/helpbot-data";
import type { BotAction, BotMessage } from "@/lib/helpbot-types";
import { GUIDE_FAQ } from "@/lib/guide-tours";

// ── Helpers ──

let msgCounter = 0;
function makeBotMessage(text: string, actions?: BotAction[]): BotMessage {
  return { id: `bot-${++msgCounter}`, sender: "bot", text, actions, ts: Date.now() };
}

// ── Views ──
export type HelpBotView = "chat" | "chapters" | "chapter-detail";

// ── Hook ──

export function useHelpBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<BotMessage[]>([]);
  const [hasUnread, setHasUnread] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [onboardingPhase, setOnboardingPhase] = useState<"pending" | "choosing" | "done">("pending");
  const [view, setView] = useState<HelpBotView>("chat");
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);

  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const {
    progress, markPageSeen, isPageSeen, markOnboardingDone,
    shouldShowOnboarding,
  } = useGuideProgress();

  const prevPathnameRef = useRef(pathname);
  const onboardingTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const autoOpenTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isOnboardingDone = progress.helpBotOnboardingDone;

  // ── Current chapter from pathname ──
  const currentChapter = useMemo(() => resolveChapter(pathname), [pathname]);

  // ── Selected chapter (for detail view) ──
  const selectedChapter = useMemo(
    () => CHAPTERS.find((ch) => ch.id === selectedChapterId) ?? null,
    [selectedChapterId],
  );

  // ── Reset onboarding phase from storage ──
  useEffect(() => {
    if (isOnboardingDone) setOnboardingPhase("done");
  }, [isOnboardingDone]);

  // ── Auto-open on first dashboard visit ──
  useEffect(() => {
    if (!shouldShowOnboarding || pathname !== "/" || isOnboardingDone) return;

    autoOpenTimerRef.current = setTimeout(() => {
      setOpen(true);
      setHasUnread(false);
      startOnboarding();
    }, 3000);

    return () => {
      if (autoOpenTimerRef.current) clearTimeout(autoOpenTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldShowOnboarding, pathname, isOnboardingDone]);

  // ── Start onboarding sequence ──
  const startOnboarding = useCallback(() => {
    setOnboardingPhase("choosing");
    const timers: ReturnType<typeof setTimeout>[] = [];

    let cumulativeDelay = 0;
    ONBOARDING_STEPS.forEach((step, i) => {
      cumulativeDelay += step.delayMs;
      const timer = setTimeout(() => {
        if (i > 0) setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          { ...step.message, id: `onb-${i}`, ts: Date.now() },
        ]);
        if (i < ONBOARDING_STEPS.length - 1) {
          setTimeout(() => setIsTyping(true), 300);
        }
      }, cumulativeDelay);
      timers.push(timer);

      if (i > 0) {
        const typingTimer = setTimeout(() => setIsTyping(true), cumulativeDelay - step.delayMs + 300);
        timers.push(typingTimer);
      }
    });

    onboardingTimersRef.current = timers;
  }, []);

  // ── Cleanup onboarding timers ──
  useEffect(() => {
    return () => {
      onboardingTimersRef.current.forEach(clearTimeout);
    };
  }, []);

  // ── Handle onboarding choice ──
  const handleOnboardingChoice = useCallback((choice: "tour" | "skip") => {
    setIsTyping(true);
    const response = choice === "tour" ? ONBOARDING_TOUR_RESPONSE : ONBOARDING_SKIP_RESPONSE;

    setTimeout(() => {
      setIsTyping(false);
      setMessages((prev) => [...prev, { ...response, id: `onb-resp`, ts: Date.now() }]);
      setOnboardingPhase("done");
      markOnboardingDone();

      if (choice === "tour") {
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent("start-mini-tour", { detail: { page: "/" } }));
          setOpen(false);
        }, 800);
      }
    }, 800);
  }, [markOnboardingDone]);

  // ── Page change: contextual greeting ──
  useEffect(() => {
    if (prevPathnameRef.current === pathname) return;
    prevPathnameRef.current = pathname;

    if (onboardingPhase !== "done") return;

    const chapter = resolveChapter(pathname);
    if (!chapter) return;

    const basePage = "/" + pathname.split("/").filter(Boolean)[0];
    const pageKey = basePage || "/";

    if (!isPageSeen(pageKey)) {
      markPageSeen(pageKey);
      const greeting = makeBotMessage(chapter.intro);

      if (open) {
        setIsTyping(true);
        setTimeout(() => {
          setIsTyping(false);
          setMessages((prev) => [...prev, greeting]);
        }, 600);
      } else {
        setHasUnread(true);
      }
    }

    // Auto-switch to matching chapter view when navigating
    if (open && view === "chapter-detail" && selectedChapterId !== chapter.id) {
      setSelectedChapterId(chapter.id);
    }
  }, [pathname, open, onboardingPhase, isPageSeen, markPageSeen, view, selectedChapterId]);

  // ── Proactive triggers (React Query cache) ──
  useEffect(() => {
    if (onboardingPhase !== "done") return;

    for (const trigger of PROACTIVE_TRIGGERS) {
      const regex = new RegExp(trigger.routePattern);
      if (!regex.test(pathname)) continue;

      if (trigger.condition === "zero-clients") {
        type ClientList = { id: number }[];
        const clients = queryClient.getQueryData<ClientList>(["clients"]);
        if (clients && clients.length === 0) {
          setMessages((prev) => {
            if (prev.some((m) => m.text === trigger.message)) return prev;
            return [...prev, makeBotMessage(trigger.message, trigger.action ? [trigger.action] : undefined)];
          });
          if (!open) setHasUnread(true);
        }
      }

      if (trigger.condition === "first-visit") {
        const pageKey = "/" + pathname.split("/").filter(Boolean)[0];
        if (!isPageSeen(pageKey)) {
          setMessages((prev) => {
            if (prev.some((m) => m.text === trigger.message)) return prev;
            return [...prev, makeBotMessage(trigger.message, trigger.action ? [trigger.action] : undefined)];
          });
          if (!open) setHasUnread(true);
        }
      }
    }
  }, [pathname, onboardingPhase, queryClient, open, isPageSeen]);

  // ── Toggle ──
  const toggle = useCallback(() => {
    setOpen((prev) => {
      if (!prev) setHasUnread(false);
      return !prev;
    });
  }, []);

  const close = useCallback(() => setOpen(false), []);

  // ── Navigation: browse chapters ──
  const browseChapters = useCallback(() => {
    setView("chapters");
    setSelectedChapterId(null);
  }, []);

  const openChapter = useCallback((chapterId: string) => {
    setSelectedChapterId(chapterId);
    setView("chapter-detail");
  }, []);

  const backToChat = useCallback(() => {
    setView("chat");
    setSelectedChapterId(null);
  }, []);

  // ── Send action ──
  const sendAction = useCallback((action: BotAction) => {
    switch (action.type) {
      case "navigate":
        if (action.payload) router.push(action.payload);
        setOpen(false);
        break;
      case "mini-tour":
        if (action.payload) {
          window.dispatchEvent(new CustomEvent("start-mini-tour", { detail: { page: action.payload } }));
        }
        setOpen(false);
        break;
      case "spotlight": {
        const spot = action.payload ? resolveSpotlight(action.payload) : null;
        if (spot) {
          window.dispatchEvent(new CustomEvent("start-action-spotlight", { detail: spot }));
        }
        setOpen(false);
        break;
      }
      case "onboarding-choice":
        handleOnboardingChoice(action.payload as "tour" | "skip");
        break;
      case "dismiss":
        setOpen(false);
        break;
    }
  }, [router, handleOnboardingChoice]);

  // ── Launch mini-tour for current page ──
  const launchMiniTour = useCallback(() => {
    const basePage = "/" + pathname.split("/").filter(Boolean)[0] || "/";
    window.dispatchEvent(new CustomEvent("start-mini-tour", { detail: { page: basePage } }));
    setOpen(false);
  }, [pathname]);

  // ── FAQ search ──
  const searchFaq = useCallback((query: string) => {
    if (!query.trim()) return;

    const q = query.toLowerCase();

    // Search in chapter FAQs first, then global FAQ
    const allFaqs = [
      ...CHAPTERS.flatMap((ch) => ch.faqs),
      ...GUIDE_FAQ,
    ];

    const results = allFaqs
      .filter((faq) =>
        faq.question.toLowerCase().includes(q) ||
        faq.answer.toLowerCase().includes(q)
      )
      .slice(0, 3);

    if (results.length > 0) {
      const answerMessages = results.map((faq) =>
        makeBotMessage(`**${faq.question}**\n${faq.answer}`)
      );
      setMessages((prev) => [...prev, ...answerMessages]);
    } else {
      setMessages((prev) => [
        ...prev,
        makeBotMessage("Non ho trovato risposte. Prova con parole diverse o esplora i capitoli della guida.", [
          { label: "Esplora capitoli", type: "dismiss" },
        ]),
      ]);
      setView("chapters");
    }
  }, []);

  return {
    open,
    messages,
    hasUnread,
    isTyping,
    onboardingPhase,
    view,
    currentChapter,
    selectedChapter,
    chapters: CHAPTERS,
    toggle,
    close,
    sendAction,
    launchMiniTour,
    searchFaq,
    browseChapters,
    openChapter,
    backToChat,
  };
}
