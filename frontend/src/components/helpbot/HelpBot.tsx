// ════════════════════════════════════════════════════════════
// HelpBot — Wrapper FAB + Panel
//
// Renderizzato in layout.tsx. Gestisce lo state via useHelpBot.
// Nasconde il FAB durante SpotlightTour.
// ════════════════════════════════════════════════════════════

"use client";

import { useHelpBot } from "@/hooks/useHelpBot";
import { HelpBotFab } from "./HelpBotFab";
import { HelpBotPanel } from "./HelpBotPanel";

interface HelpBotProps {
  tourOpen: boolean;
}

export function HelpBot({ tourOpen }: HelpBotProps) {
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
  } = useHelpBot();

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
