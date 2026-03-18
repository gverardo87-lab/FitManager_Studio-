// ════════════════════════════════════════════════════════════
// HelpBotFab — Bottone floating "Bussola"
//
// Gradient teal-emerald, icona Compass con rotazione hover,
// anello orbitale animato, badge unread con ping.
// ════════════════════════════════════════════════════════════

"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Compass } from "lucide-react";

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
      className="helpbot-fab group fixed bottom-6 right-6 z-[9998] flex h-[52px] w-[52px] items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 via-teal-600 to-emerald-700 text-white shadow-[0_4px_20px_oklch(0.55_0.14_170/0.35)] transition-all duration-300 hover:scale-105 hover:shadow-[0_8px_32px_oklch(0.55_0.14_170/0.5)] active:scale-95 max-lg:bottom-4 max-lg:right-4 max-lg:h-11 max-lg:w-11 max-lg:rounded-xl"
      aria-label="Apri Bussola"
    >
      {/* Anello orbitale decorativo */}
      <span className="helpbot-orbit pointer-events-none absolute inset-0 rounded-2xl border border-white/20 max-lg:rounded-xl" />

      {/* Icona con rotazione hover */}
      <Compass className="h-[22px] w-[22px] drop-shadow-sm transition-transform duration-500 group-hover:rotate-45 max-lg:h-5 max-lg:w-5" />

      {/* Badge unread */}
      {hasUnread ? (
        <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 shadow-sm">
          <span className="absolute h-2.5 w-2.5 animate-ping rounded-full bg-red-400" />
          <span className="relative h-2 w-2 rounded-full bg-white" />
        </span>
      ) : null}
    </button>,
    document.body,
  );
}
