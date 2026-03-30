// src/lib/media.ts
/**
 * Helper per URL media.
 *
 * Next.js proxya /media/* al backend via rewrite in next.config.ts:
 *   /media/:path* → http://127.0.0.1:{backendPort}/media/:path*
 *
 * Quindi i media sono same-origin — basta il path relativo.
 * NON costruire URL assoluti: falliscono via Tailscale Funnel (HTTPS su porta
 * diversa) e su qualsiasi configurazione dove il browser non raggiunge
 * direttamente la porta del backend.
 */

/**
 * Ritorna il path relativo per un media, pronto per src/href.
 * Es: "/media/exercises/42/abc123.jpg" → "/media/exercises/42/abc123.jpg"
 *
 * Ritorna null se il path e' null/undefined.
 */
export function getMediaUrl(relativePath: string | null | undefined): string | null {
  if (!relativePath) return null;
  // Il path dal backend e' gia' relativo (/media/...) — same-origin via rewrite
  return relativePath;
}
