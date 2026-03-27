// src/components/dashboard/BirthdayClientsSheet.tsx
/**
 * Sheet per compleanni imminenti (oggi + prossimi 7 giorni).
 *
 * Mostra clienti con compleanno vicino:
 * - Badge "Oggi!" / "tra N giorni"
 * - Eta' che compie
 * - WhatsApp pre-compilato con auguri
 * - Contatti rapidi (telefono, email)
 *
 * Obiettivo: non dimenticare mai un compleanno — fidelizzazione massima.
 */

"use client";

import {
  Cake,
  CheckCircle2,
  Phone,
  Mail,
  PartyPopper,
  Calendar,
} from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { WhatsAppButton } from "@/components/ui/whatsapp-button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useBirthdayClients } from "@/hooks/useDashboard";
import { useTrainerName } from "@/hooks/useTrainerName";
import { formatShortDate } from "@/lib/format";
import { waBirthday } from "@/lib/whatsapp-templates";

// ── Helpers ──

function countdownLabel(giorni: number): string {
  if (giorni === 0) return "Oggi!";
  if (giorni === 1) return "Domani";
  return `Tra ${giorni} giorni`;
}

function countdownBadge(giorni: number): string {
  if (giorni === 0) return "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-400";
  if (giorni <= 2) return "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-400";
  return "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400";
}

// ════════════════════════════════════════════════════════════

interface BirthdayClientsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BirthdayClientsSheet({ open, onOpenChange }: BirthdayClientsSheetProps) {
  const { data, isLoading } = useBirthdayClients(open);
  const items = data?.items ?? [];

  const trainerName = useTrainerName();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-hidden sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-pink-100 dark:bg-pink-900/30">
              <Cake aria-hidden="true" className="h-5 w-5 text-pink-600 dark:text-pink-400" />
            </div>
            <div>
              <SheetTitle>Compleanni</SheetTitle>
              <SheetDescription>
                Oggi e nei prossimi 7 giorni
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <Separator />

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3 p-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        )}

        {/* Empty */}
        {!isLoading && items.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30">
              <CheckCircle2 aria-hidden="true" className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
            </div>
            <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              Nessun compleanno in arrivo
            </p>
            <p className="text-xs text-muted-foreground">
              I prossimi 7 giorni sono tranquilli
            </p>
          </div>
        )}

        {/* Lista clienti */}
        {!isLoading && items.length > 0 && (
          <ScrollArea className="min-h-0 flex-1 -mx-1 px-1">
            <div className="space-y-3 pb-4">
              {items.map((item) => (
                <div
                  key={item.client_id}
                  className="rounded-lg border p-4 transition-shadow hover:shadow-sm"
                >
                  {/* Header: nome + badge countdown */}
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {item.giorni_mancanti === 0 && (
                        <PartyPopper aria-hidden="true" className="h-4 w-4 text-pink-500" />
                      )}
                      <span className="text-sm font-semibold">
                        {item.nome} {item.cognome}
                      </span>
                    </div>
                    <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${countdownBadge(item.giorni_mancanti)}`}>
                      {countdownLabel(item.giorni_mancanti)}
                    </span>
                  </div>

                  {/* Info compleanno */}
                  <div className="mb-3 flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar aria-hidden="true" className="h-3 w-3" />
                      <span>{formatShortDate(item.data_nascita)}</span>
                    </div>
                    <span className="font-medium text-foreground">
                      Compie {item.eta_compie} anni
                    </span>
                  </div>

                  {/* Contatti */}
                  <div className="flex flex-wrap gap-2">
                    <WhatsAppButton
                      phone={item.telefono}
                      message={waBirthday(item.nome, trainerName)}
                      variant="compact"
                      label="Auguri"
                      clientId={item.client_id}
                      templateKey="birthday"
                    />
                    {item.telefono && (
                      <a
                        href={`tel:${item.telefono}`}
                        className="inline-flex items-center gap-1.5 rounded-md border bg-white px-2.5 py-1 text-xs font-medium transition-colors hover:bg-blue-50 hover:text-blue-600 dark:bg-zinc-900 dark:hover:bg-blue-950/30 dark:hover:text-blue-400"
                      >
                        <Phone aria-hidden="true" className="h-3 w-3" />
                        Chiama
                      </a>
                    )}
                    {item.email && (
                      <a
                        href={`mailto:${item.email}`}
                        className="inline-flex items-center gap-1.5 rounded-md border bg-white px-2.5 py-1 text-xs font-medium transition-colors hover:bg-blue-50 hover:text-blue-600 dark:bg-zinc-900 dark:hover:bg-blue-950/30 dark:hover:text-blue-400"
                      >
                        <Mail aria-hidden="true" className="h-3 w-3" />
                        Email
                      </a>
                    )}
                    {!item.telefono && !item.email && (
                      <span className="text-[11px] text-muted-foreground/60 italic">
                        Nessun contatto registrato
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  );
}
