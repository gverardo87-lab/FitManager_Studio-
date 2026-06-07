/**
 * Next.js Middleware — Route Protection + Tunnel Route Separation.
 *
 * Intercetta TUTTE le richieste prima che raggiungano i componenti React.
 * Funziona al livello Edge, quindi il redirect avviene PRIMA del rendering.
 *
 * Due layer di protezione:
 * 1. TUNNEL GUARD: richieste dal tunnel FRP possono accedere SOLO a /public/*
 *    Il CRM (login, dashboard, clienti, ecc.) è invisibile da Internet.
 * 2. AUTH GUARD: richieste LAN senza cookie → redirect /login
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_COOKIE = "fitmanager_token";

// Rotte accessibili senza autenticazione (pagine + API pubbliche)
const PUBLIC_ROUTES = ["/login", "/register", "/licenza", "/setup", "/public", "/api", "/health", "/media"];

// Rotte da cui ridirigere utenti già autenticati
const AUTH_ONLY_PAGES = ["/login", "/register", "/setup"];

// Rotte accessibili dal tunnel (tutto il resto → 404)
const TUNNEL_ALLOWED_PREFIXES = ["/public", "/api/public", "/health", "/media", "/_next", "/favicon.ico"];

/**
 * Rileva se la richiesta arriva dal tunnel FRP.
 *
 * Euristica: il hostname NON è localhost/127.0.0.1/IP LAN.
 * Le richieste dal tunnel hanno come Host il dominio pubblico
 * (es. gvera-dev.fitmanagerstudio.com), quelle LAN hanno localhost:3000.
 */
function isTunnelRequest(request: NextRequest): boolean {
  const host = request.headers.get("host") ?? "";
  const hostname = host.split(":")[0];

  // LAN: localhost, 127.0.0.1, IP privati (192.168.x.x, 10.x.x.x, 100.x.x.x)
  if (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname.startsWith("192.168.") ||
    hostname.startsWith("10.") ||
    hostname.startsWith("100.")
  ) {
    return false;
  }

  // Qualsiasi altro hostname = tunnel (es. gvera-dev.fitmanagerstudio.com)
  return true;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // ── Layer 1: Tunnel Guard ──
  // Richieste dal tunnel possono accedere SOLO a route pubbliche.
  // Tutto il resto (login, dashboard, clienti, ecc.) → 404.
  if (isTunnelRequest(request)) {
    const isAllowed = TUNNEL_ALLOWED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
    if (!isAllowed) {
      return new NextResponse(null, { status: 404 });
    }
    // Route pubblica via tunnel → prosegui senza check auth
    return NextResponse.next();
  }

  // ── Layer 2: Auth Guard (solo LAN) ──
  const token = request.cookies.get(TOKEN_COOKIE)?.value;
  const isPublicRoute = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));

  // Utente NON autenticato su rotta protetta → redirect /login
  if (!token && !isPublicRoute) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl, 307);
  }

  // Utente autenticato sulle pagine auth → redirect /
  if (token && AUTH_ONLY_PAGES.some((route) => pathname.startsWith(route))) {
    const homeUrl = new URL("/", request.url);
    return NextResponse.redirect(homeUrl, 307);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|.*\\..*).*)",
  ],
};
