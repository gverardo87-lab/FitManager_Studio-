// components/guide/PageVideoGuide.tsx
"use client";

/**
 * PageVideoGuide — wrapper che mostra VideoGuidePopover
 * se esiste un video pronto per la pagina corrente.
 *
 * Uso: inserire nell'header di ogni pagina, a sinistra del bottone azione.
 * Si auto-configura in base al pathname (zero props manuali).
 *
 * Ritorna null se nessun video pronto per la pagina.
 */

import { usePathname } from "next/navigation";
import { VideoGuidePopover } from "./VideoGuidePopover";
import { getVideoGuidesForPage } from "@/lib/video-guides";

export function PageVideoGuide() {
  const pathname = usePathname();
  // Normalizza: /clienti/123 → /clienti, /contratti/45 → /contratti
  const basePath = "/" + (pathname.split("/")[1] || "");
  const videos = getVideoGuidesForPage(basePath).filter((v) => v.ready);

  if (videos.length === 0) return null;

  // Regola §7.1: UN solo video per pagina (il primo match ready)
  return <VideoGuidePopover video={videos[0]} />;
}
