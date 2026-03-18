// ════════════════════════════════════════════════════════════
// HelpBotFab — Bottone floating bottom-right
//
// Gradient teal-emerald con ombra colorata, pulse al primo avvio.
// Nascosto durante tour. Portal in document.body.
// ════════════════════════════════════════════════════════════

"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Sparkles } from "lucide-react";

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
      className="helpbot-fab fixed bottom-6 right-6 z-[9998] flex h-13 w-13 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 via-teal-600 to-emerald-700 text-white shadow-[0_4px_20px_oklch(0.55_0.14_170/0.4)] transition-all duration-200 hover:scale-105 hover:shadow-[0_6px_28px_oklch(0.55_0.14_170/0.55)] active:scale-95 lg:bottom-6 lg:right-6 max-lg:bottom-4 max-lg:right-4 max-lg:h-11 max-lg:w-11 max-lg:rounded-xl"
      aria-label="Apri Bussola"
    >
      <Sparkles className="h-5 w-5 drop-shadow-sm" />

      {/* Badge unread */}
      {hasUnread ? (
        <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 shadow-sm">
          <span className="h-2 w-2 animate-ping rounded-full bg-white" />
          <span className="absolute h-2 w-2 rounded-full bg-white" />
        </span>
      ) : null}
    </button>,
    document.body,
  );
}
