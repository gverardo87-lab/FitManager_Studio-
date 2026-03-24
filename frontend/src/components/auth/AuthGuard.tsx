// src/components/auth/AuthGuard.tsx
"use client";

/**
 * AuthGuard — protezione client-side per le rotte autenticate.
 *
 * Due livelli di protezione:
 * 1. Fresh install detection: se backend dice needs_setup=true ma il browser
 *    ha cookie auth stale (es. reinstallazione), li pulisce e manda a /setup.
 * 2. Auth check: se il cookie JWT e' assente, redirect a /login.
 *
 * NOTA: useState(false) + useEffect e' il pattern corretto qui.
 * isAuthenticated() legge document.cookie (browser-only API).
 * Chiamarla durante SSR causa hydration mismatch perche' il server
 * non ha cookie → render null, ma il client ha cookie → render children.
 * Con useState(false) entrambi partono da null → match → effect lato
 * client verifica e setta checked=true.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import apiClient from "@/lib/api-client";
import { isAuthenticated, clearStaleAuth } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    apiClient
      .get<{ needs_setup: boolean }>("/auth/setup-status")
      .then(({ data }) => {
        if (data.needs_setup) {
          // Fresh install: pulisci eventuali cookie stale e manda a setup
          clearStaleAuth();
          router.replace("/setup");
          return;
        }
        // Setup completato: verifica auth normalmente
        if (isAuthenticated()) {
          setChecked(true);
        } else {
          router.replace("/login");
        }
      })
      .catch(() => {
        // Network error: fallback al check auth semplice
        if (isAuthenticated()) {
          setChecked(true);
        } else {
          router.replace("/login");
        }
      });
  }, [router]);

  if (!checked) return null;

  return <>{children}</>;
}
