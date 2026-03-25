// src/app/(dashboard)/layout.tsx
"use client";

/**
 * Layout condiviso per tutte le pagine del dashboard.
 *
 * Desktop (lg+): sidebar fissa a sinistra (w-64) + contenuto a destra.
 * Mobile (<lg): header con hamburger menu che apre la Sidebar in un Sheet.
 *
 * Questo layout NON appare nell'URL grazie al Route Group (dashboard).
 *
 * Scroll restoration: <main> è lo scroll container (h-screen constraint).
 * Lo scroll viene salvato continuamente in sessionStorage e ripristinato
 * al cambio pathname SE esiste un valore salvato (altrimenti scroll to top).
 * La Sidebar cancella il valore salvato onClick → fresh nav = top.
 *
 * SpotlightTour: tour guidato con overlay su elementi reali.
 * Supporta tour completo (19 step), mini-tour e spotlight singolo.
 * Manual trigger da /guida via custom event.
 *
 * HelpBot: dispatcher contestuale FAB + Panel.
 * Lancia spotlight/mini-tour via callback diretto (no custom events).
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Menu } from "lucide-react";

import { Sidebar } from "@/components/layout/Sidebar";
import dynamic from "next/dynamic";

const CommandPalette = dynamic(
  () => import("@/components/layout/CommandPalette").then((m) => ({ default: m.CommandPalette })),
  { ssr: false },
);
import { SpotlightTour } from "@/components/guide/SpotlightTour";
import { HelpBot } from "@/components/helpbot/HelpBot";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useGuideProgress } from "@/hooks/useGuideProgress";
import { BuilderModeProvider, useBuilderMode } from "@/lib/builder-mode";
import { TOUR_SCOPRI_FITMANAGER, MINI_TOUR_MAP } from "@/lib/guide-tours";
import type { TourDefinition } from "@/lib/guide-tours";
import type { SpotlightTarget } from "@/lib/helpbot-types";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [activeTour, setActiveTour] = useState<TourDefinition>(TOUR_SCOPRI_FITMANAGER);
  const mainRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const prevPathnameRef = useRef(pathname);
  const scrollTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const router = useRouter();
  const { shouldShowOnboarding, markTourCompleted, markTourDismissed } = useGuideProgress();

  // ── Build mini-tour from step indices ──
  const buildMiniTour = useCallback((page: string): TourDefinition | null => {
    const indices = MINI_TOUR_MAP[page];
    if (!indices || indices.length === 0) return null;
    const steps = indices
      .map((i) => TOUR_SCOPRI_FITMANAGER.steps[i])
      .filter(Boolean);
    if (steps.length === 0) return null;
    return {
      id: `mini-tour-${page}`,
      title: "Tour rapido",
      steps,
    };
  }, []);

  // ── Tour navigation callback (cross-page tour) ──
  const handleTourNavigate = useCallback((href: string) => {
    if (pathname !== href) {
      router.push(href);
    }
  }, [router, pathname]);

  // ── Callback: launch mini-tour (called by HelpBot) ──
  const handleMiniTour = useCallback((page: string) => {
    const mini = buildMiniTour(page);
    if (!mini) return;

    setTourOpen(false);
    setActiveTour(mini);
    requestAnimationFrame(() => {
      setTourOpen(true);
    });
  }, [buildMiniTour]);

  // ── Callback: launch spotlight (called by HelpBot) ──
  // Due fasi: (1) chiudi tour + prepara nuovo, (2) apri dopo un frame.
  // Senza questa separazione, React batcha setActiveTour + setTourOpen
  // e SpotlightTour non monta correttamente sulla stessa pagina.
  const handleSpotlight = useCallback((spot: SpotlightTarget) => {
    // Navigate first if needed
    if (spot.navigateTo && pathname !== spot.navigateTo) {
      router.push(spot.navigateTo);
    }

    // Phase 1: close + prepare
    setTourOpen(false);
    setActiveTour({
      id: `spotlight-${spot.target}-${Date.now()}`,
      title: spot.title,
      steps: [{
        target: spot.target,
        title: spot.title,
        description: spot.description,
        placement: spot.placement,
        navigateTo: spot.navigateTo,
      }],
    });

    // Phase 2: open after React commits the close + new tour
    requestAnimationFrame(() => {
      setTourOpen(true);
    });
  }, [pathname, router]);

  // ── Hook 1: Continuously save scroll position via scroll event ──
  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    let rafId: number | null = null;
    const handleScroll = () => {
      if (rafId !== null) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        sessionStorage.setItem(`scroll:${pathname}`, String(main.scrollTop));
        rafId = null;
      });
    };

    main.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      main.removeEventListener("scroll", handleScroll);
      if (rafId !== null) cancelAnimationFrame(rafId);
    };
  }, [pathname]);

  // ── Hook 2: Restore scroll from sessionStorage or reset to top ──
  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;

    if (prevPathnameRef.current === pathname) return;
    prevPathnameRef.current = pathname;

    scrollTimersRef.current.forEach(clearTimeout);
    scrollTimersRef.current = [];

    const saved = sessionStorage.getItem(`scroll:${pathname}`);
    if (saved) {
      const target = parseInt(saved, 10);
      const tryRestore = () => { main.scrollTop = target; };
      [0, 50, 100, 250, 500, 1000, 2000].forEach(delay => {
        scrollTimersRef.current.push(setTimeout(tryRestore, delay));
      });
    } else {
      main.scrollTop = 0;
    }
  }, [pathname]);

  // ── Hook 3: REMOVED — auto-trigger SpotlightTour on first visit ──
  // Now handled by HelpBot onboarding sequence.

  // ── Hook 4: Listen for manual tour trigger from /guida (full tour) ──
  useEffect(() => {
    const handler = () => {
      setActiveTour(TOUR_SCOPRI_FITMANAGER);
      setTourOpen(true);
    };
    window.addEventListener("start-guide-tour", handler);
    return () => window.removeEventListener("start-guide-tour", handler);
  }, []);

  // ── Hook 5: Listen for mini-tour trigger (custom event — onboarding + /guida) ──
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as { page: string } | undefined;
      if (!detail?.page) return;
      handleMiniTour(detail.page);
    };
    window.addEventListener("start-mini-tour", handler);
    return () => window.removeEventListener("start-mini-tour", handler);
  }, [handleMiniTour]);

  return (
    <AuthGuard>
    <BuilderModeProvider>
    <CommandPalette />
    <SpotlightTour
      key={activeTour.id}
      tour={activeTour}
      open={tourOpen}
      onComplete={() => {
        setTourOpen(false);
        if (activeTour.id === "scopri-fitmanager") {
          markTourCompleted("scopri-fitmanager");
        }
      }}
      onDismiss={() => {
        setTourOpen(false);
        if (activeTour.id === "scopri-fitmanager") {
          markTourDismissed("scopri-fitmanager");
        }
      }}
      onNavigate={handleTourNavigate}
    />
    <HelpBot
      tourOpen={tourOpen}
      onMiniTour={handleMiniTour}
      onSpotlight={handleSpotlight}
    />
    <DashboardShell mainRef={mainRef} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} shouldShowOnboarding={shouldShowOnboarding}>
      {children}
    </DashboardShell>
    </BuilderModeProvider>
    </AuthGuard>
  );
}

/**
 * Shell interna che consuma BuilderModeContext per nascondere la sidebar.
 * Separato dal layout perché useBuilderMode() richiede il Provider come ancestor.
 */
function DashboardShell({
  children, mainRef, mobileOpen, setMobileOpen, shouldShowOnboarding,
}: {
  children: React.ReactNode;
  mainRef: React.RefObject<HTMLDivElement | null>;
  mobileOpen: boolean;
  setMobileOpen: (v: boolean) => void;
  shouldShowOnboarding: boolean;
}) {
  const { isBuilderMode } = useBuilderMode();

  return (
    <div className="bg-mesh-app flex h-screen">
      {/* ── Sidebar desktop — nascosta in builder mode ── */}
      {!isBuilderMode && (
        <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:bg-sidebar dark:lg:bg-sidebar">
          <Sidebar guidePulse={shouldShowOnboarding} />
        </aside>
      )}

      {/* ── Contenuto principale ── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* ── Header mobile (visibile sotto lg, anche in builder) ── */}
        <header className="flex h-14 shrink-0 items-center gap-3 border-b bg-sidebar px-4 lg:hidden dark:bg-sidebar">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon-sm">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
              <SheetTitle className="sr-only">Menu navigazione</SheetTitle>
              <Sidebar onNavigate={() => setMobileOpen(false)} />
            </SheetContent>
          </Sheet>
          <span className="text-sm font-semibold">FitManager Studio+</span>
        </header>

        {/* ── Page content — padding ridotto in builder mode ── */}
        <main ref={mainRef} className={isBuilderMode ? "flex-1 overflow-y-auto p-3 lg:p-4" : "flex-1 overflow-y-auto p-4 md:p-6 lg:p-8"}>
          {children}
        </main>
      </div>
    </div>
  );
}
