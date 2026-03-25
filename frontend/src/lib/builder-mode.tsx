// src/lib/builder-mode.tsx
"use client";

/**
 * BuilderModeContext — segnala al layout di nascondere la sidebar.
 *
 * Quando il builder schede si monta, chiama enterBuilderMode().
 * Il layout consuma isBuilderMode e nasconde la sidebar desktop.
 * Al unmount o navigazione, exitBuilderMode() ripristina il layout standard.
 */

import { createContext, useContext, useState, useCallback } from "react";

interface BuilderModeState {
  isBuilderMode: boolean;
  enterBuilderMode: () => void;
  exitBuilderMode: () => void;
}

const BuilderModeContext = createContext<BuilderModeState>({
  isBuilderMode: false,
  enterBuilderMode: () => {},
  exitBuilderMode: () => {},
});

export function BuilderModeProvider({ children }: { children: React.ReactNode }) {
  const [isBuilderMode, setIsBuilderMode] = useState(false);
  const enterBuilderMode = useCallback(() => setIsBuilderMode(true), []);
  const exitBuilderMode = useCallback(() => setIsBuilderMode(false), []);

  return (
    <BuilderModeContext.Provider value={{ isBuilderMode, enterBuilderMode, exitBuilderMode }}>
      {children}
    </BuilderModeContext.Provider>
  );
}

export function useBuilderMode() {
  return useContext(BuilderModeContext);
}
