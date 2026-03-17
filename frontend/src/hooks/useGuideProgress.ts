// ════════════════════════════════════════════════════════════
// useGuideProgress — Tracking stato guida via localStorage
//
// Pattern identico a fitmanager.guida.checklist.v1 (vecchia guida).
// Nessuna API, nessun React Query — stato puramente locale.
// ════════════════════════════════════════════════════════════

import { useCallback, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "fitmanager.guide.progress.v1";

interface GuideProgress {
  completedTours: string[];
  dismissedTours: string[];
  /** Pagine gia' visitate dal bot (progressive reveal) */
  helpBotSeenPages: string[];
  /** Primo avvio bot completato */
  helpBotOnboardingDone: boolean;
}

const EMPTY_PROGRESS: GuideProgress = {
  completedTours: [],
  dismissedTours: [],
  helpBotSeenPages: [],
  helpBotOnboardingDone: false,
};

function loadFromStorage(): GuideProgress {
  if (typeof window === "undefined") return EMPTY_PROGRESS;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_PROGRESS;
    const parsed = JSON.parse(raw) as Partial<GuideProgress>;
    return {
      completedTours: Array.isArray(parsed.completedTours) ? parsed.completedTours : [],
      dismissedTours: Array.isArray(parsed.dismissedTours) ? parsed.dismissedTours : [],
      helpBotSeenPages: Array.isArray(parsed.helpBotSeenPages) ? parsed.helpBotSeenPages : [],
      helpBotOnboardingDone: parsed.helpBotOnboardingDone === true,
    };
  } catch {
    return EMPTY_PROGRESS;
  }
}

export function useGuideProgress() {
  const [progress, setProgress] = useState<GuideProgress>(loadFromStorage);

  // Persistenza su ogni cambio
  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }, [progress]);

  const markTourCompleted = useCallback((tourId: string) => {
    setProgress((prev) => ({
      ...prev,
      completedTours: prev.completedTours.includes(tourId)
        ? prev.completedTours
        : [...prev.completedTours, tourId],
    }));
  }, []);

  const markTourDismissed = useCallback((tourId: string) => {
    setProgress((prev) => ({
      ...prev,
      dismissedTours: prev.dismissedTours.includes(tourId)
        ? prev.dismissedTours
        : [...prev.dismissedTours, tourId],
    }));
  }, []);

  const isTourCompleted = useCallback(
    (tourId: string) => progress.completedTours.includes(tourId),
    [progress.completedTours],
  );

  const markPageSeen = useCallback((page: string) => {
    setProgress((prev) => ({
      ...prev,
      helpBotSeenPages: prev.helpBotSeenPages.includes(page)
        ? prev.helpBotSeenPages
        : [...prev.helpBotSeenPages, page],
    }));
  }, []);

  const isPageSeen = useCallback(
    (page: string) => progress.helpBotSeenPages.includes(page),
    [progress.helpBotSeenPages],
  );

  const markOnboardingDone = useCallback(() => {
    setProgress((prev) => ({ ...prev, helpBotOnboardingDone: true }));
  }, []);

  const resetProgress = useCallback(() => {
    setProgress(EMPTY_PROGRESS);
  }, []);

  const shouldShowOnboarding = useMemo(
    () =>
      !progress.completedTours.includes("scopri-fitmanager") &&
      !progress.dismissedTours.includes("scopri-fitmanager"),
    [progress.completedTours, progress.dismissedTours],
  );

  return {
    progress,
    markTourCompleted,
    markTourDismissed,
    isTourCompleted,
    markPageSeen,
    isPageSeen,
    markOnboardingDone,
    resetProgress,
    shouldShowOnboarding,
  };
}
