"use client";

import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

interface DataErrorStateProps {
  title?: string;
  message: string;
  onRetry: () => void;
  isRetrying?: boolean;
}

/** Stato read-only riusabile: errore esplicito, mai confuso con empty/not-found. */
export function DataErrorState({
  title = "Dati non disponibili",
  message,
  onRetry,
  isRetrying = false,
}: DataErrorStateProps) {
  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50/60 p-4 dark:border-amber-900 dark:bg-amber-950/20">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700 dark:text-amber-300" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold">{title}</p>
            <p className="mt-1 text-xs text-muted-foreground">{message}</p>
          </div>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={onRetry} disabled={isRetrying}>
          {isRetrying ? <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" /> : <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />}
          {isRetrying ? "Caricamento…" : "Riprova"}
        </Button>
      </div>
    </div>
  );
}

