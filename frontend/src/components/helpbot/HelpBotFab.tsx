// ════════════════════════════════════════════════════════════
// HelpBotFab — Bottone floating bottom-right
//
// Cerchio teal con icona MessageCircle, badge unread,
// pulse animation al primo avvio. Nascosto durante tour.
// Portal in document.body (stesso pattern EventHoverCard).
// ════════════════════════════════════════════════════════════

"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { MessageCircle } from "lucide-react";

interface HelpBotFabProps {
  hasUnread: boolean;
  tourOpen: boolean;
  onClick: () => void;
}

export function HelpBotFab({ hasUnread, tourOpen, onClick }: HelpBotFabProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || tourOpen) return null;

  return createPortal(
    <button
      type="button"
      onClick={onClick}
      className="helpbot-fab fixed bottom-6 right-6 z-[9998] flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 active:scale-95 lg:bottom-6 lg:right-6 max-lg:bottom-4 max-lg:right-4 max-lg:h-11 max-lg:w-11"
      aria-label="Apri assistente"
    >
      <MessageCircle className="h-5 w-5" />

      {/* Badge unread */}
      {hasUnread ? (
        <span className="absolute -top-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-destructive">
          <span className="h-2 w-2 rounded-full bg-white" />
        </span>
      ) : null}
    </button>,
    document.body,
  );
}
