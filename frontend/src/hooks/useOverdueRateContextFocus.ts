"use client";

import { useCallback, useEffect, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";

import { parseRenewalsFocus, type OverdueRateFocusIntent } from "@/lib/renewals-focus";
import type { OverdueRateItem } from "@/types/api";

interface UseOverdueRateContextFocusOptions {
  items: OverdueRateItem[];
  isLoading: boolean;
  hasError: boolean;
}

interface OverdueRateContextFocusResult {
  targetRateId: number | null;
  targetRef: (node: HTMLDivElement | null) => void;
  markerLabel: string | null;
  announcement: string;
  isMissing: boolean;
  isHighlighted: boolean;
}

function intentKey(intent: OverdueRateFocusIntent): string {
  return `${intent.focus}:${intent.clientId}:${intent.rateId ?? "client"}`;
}

export function useOverdueRateContextFocus({
  items,
  isLoading,
  hasError,
}: UseOverdueRateContextFocusOptions): OverdueRateContextFocusResult {
  const [isHighlighted, setIsHighlighted] = useState(false);
  const [targetNode, setTargetNode] = useState<HTMLDivElement | null>(null);
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const search = searchParams.toString();
  const routeKey = `${pathname}?${search}`;
  const intent = pathname === "/rinnovi-incassi" ? parseRenewalsFocus(search) : null;

  const clientMatches = intent === null
    ? []
    : items.filter((item) => item.client_id === intent.clientId);
  const target = intent?.rateId === null
    ? clientMatches[0] ?? null
    : clientMatches.find((item) => item.rate_id === intent?.rateId) ?? null;
  const targetRateId = target?.rate_id ?? null;
  const currentIntentKey = intent === null ? null : intentKey(intent);
  const hasVerifiedIntent = intent !== null && !isLoading && !hasError;
  const isMissing = hasVerifiedIntent && target === null;
  const visibleHighlight = isHighlighted && target !== null;
  const markerLabel = visibleHighlight
    ? clientMatches.length > 1 && intent?.rateId === null
      ? `Aperta da Clienti · prima di ${clientMatches.length} rate`
      : "Aperta da Clienti"
    : null;
  const clientName = target === null
    ? ""
    : `${target.client_nome} ${target.client_cognome}`.trim();
  const announcement = !hasVerifiedIntent
    ? ""
    : isMissing
      ? "L'azione richiesta non è più presente e potrebbe essere già stata risolta."
      : target !== null
        ? clientMatches.length > 1 && intent?.rateId === null
          ? `Mostrata la prima di ${clientMatches.length} rate in ritardo di ${clientName}.`
          : `Rata in ritardo di ${clientName} selezionata.`
        : "";

  const targetRef = useCallback((node: HTMLDivElement | null) => {
    setTargetNode(node);
  }, []);

  useEffect(() => {
    if (currentIntentKey === null || isLoading || hasError || targetRateId === null) return;

    if (targetNode === null) return;

    let timeoutId: number | null = null;
    const animationFrameId = window.requestAnimationFrame(() => {
      if (!targetNode.isConnected) return;

      const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
      targetNode.scrollIntoView?.({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
      targetNode.focus({ preventScroll: true });
      setIsHighlighted(true);
      timeoutId = window.setTimeout(() => setIsHighlighted(false), 2500);
    });
    return () => {
      window.cancelAnimationFrame(animationFrameId);
      if (timeoutId !== null) window.clearTimeout(timeoutId);
    };
  }, [currentIntentKey, hasError, isLoading, routeKey, targetNode, targetRateId]);

  return {
    targetRateId,
    targetRef,
    markerLabel,
    announcement,
    isMissing,
    isHighlighted: visibleHighlight,
  };
}
