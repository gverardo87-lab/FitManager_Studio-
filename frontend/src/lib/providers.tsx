// src/lib/providers.tsx
/**
 * React Query Provider — wrapper "use client" per Next.js App Router.
 *
 * Next.js App Router rende i componenti Server Components di default.
 * React Query ha bisogno di un contesto React (client-side), quindi
 * lo isoliamo in questo wrapper "use client" che viene usato nel layout.
 *
 * DevTools: visibili solo in development (process.env.NODE_ENV !== "production").
 */

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import dynamic from "next/dynamic";
import { useState, type ReactNode } from "react";

// Import STATICO (fix 201-muto G9.7.1): il lazy-load via dynamic() creava una seconda
// istanza del modulo sonner in dev — toast() scriveva su una copia, il Toaster ascoltava
// l'altra → NESSUN toast renderizzato in tutta l'app (success, warning, error).
// Il wrapper è già "use client" e non tocca browser API al mount: ssr:false non serve.
import { Toaster } from "@/components/ui/sonner";

const ReactQueryDevtools = dynamic(
  () =>
    import("@tanstack/react-query-devtools").then((m) => m.ReactQueryDevtools),
  { ssr: false },
);

export function Providers({ children }: { children: ReactNode }) {
  // useState garantisce che ogni utente abbia la sua istanza QueryClient
  // (importante per SSR/App Router per evitare data sharing tra utenti)
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Non refetchare automaticamente quando la finestra torna in focus
            // (evita chiamate inutili durante lo sviluppo)
            refetchOnWindowFocus: false,
            // Retry 1 volta su errore (default React Query e' 3)
            retry: 1,
            // Dati considerati "freschi" per 30 secondi
            staleTime: 30_000,
          },
        },
      })
  );

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster richColors position="top-right" />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
