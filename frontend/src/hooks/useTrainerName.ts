// src/hooks/useTrainerName.ts
/**
 * Hook che legge nome e cognome del trainer dal cookie.
 *
 * Pattern hydration-safe: useState("") + useEffect per leggere
 * il cookie solo client-side, evitando mismatch SSR.
 */

import { useState, useEffect } from "react";
import { getStoredTrainer } from "@/lib/auth";

export function useTrainerName(): string {
  const [name, setName] = useState("");
  useEffect(() => {
    const t = getStoredTrainer();
    if (t) setName(`${t.nome} ${t.cognome}`);
  }, []);
  return name;
}
