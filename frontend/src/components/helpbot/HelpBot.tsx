// ════════════════════════════════════════════════════════════
// HelpBot — Wrapper FAB + Panel
//
// Renderizzato in layout.tsx. Riceve callback diretti per
// lanciare spotlight e mini-tour (no custom events).
// ════════════════════════════════════════════════════════════

"use client";

import { useHelpBot } from "@/hooks/useHelpBot";
import { HelpBotFab } from "./HelpBotFab";
import { HelpBotPanel } from "./HelpBotPanel";
import type { SpotlightTarget } from "@/lib/helpbot-types";

interface HelpBotProps {
  tourOpen: boolean;
  onMiniTour: (page: string) => void;
  onSpotlight: (spot: SpotlightTarget) => void;
}

export function HelpBot({ tourOpen, onMiniTour, onSpotlight }: HelpBotProps) {
  const {
    open,
    messages,
    hasUnread,
    isTyping,
    view,
    currentChapter,
    selectedChapter,
    chapters,
    toggle,
    close,
    sendAction,
    searchFaq,
    browseChapters,
    openChapter,
    backToChat,
  } = useHelpBot({ onMiniTour, onSpotlight });

  return (
    <>
      <HelpBotFab
        hasUnread={hasUnread}
        tourOpen={tourOpen || open}
        onClick={toggle}
      />
      <HelpBotPanel
        open={open}
        messages={messages}
        isTyping={isTyping}
        view={view}
        currentChapter={currentChapter}
        selectedChapter={selectedChapter}
        chapters={chapters}
        onClose={close}
        onAction={sendAction}
        onSearch={searchFaq}
        onBrowseChapters={browseChapters}
        onOpenChapter={openChapter}
        onBackToChat={backToChat}
      />
    </>
  );
}
