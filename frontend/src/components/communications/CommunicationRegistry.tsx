// src/components/communications/CommunicationRegistry.tsx
"use client";

/**
 * Registro comunicazioni — timeline cronologica di tutte le comunicazioni.
 *
 * Filtro per cliente (via URL o select), raggruppamento per data,
 * icone canale, template badge, anteprima messaggio.
 */

import { useMemo, useState } from "react";
import {
  MessageCircle,
  Phone,
  Mail,
  StickyNote,
  Search,
  Users,
  type LucideIcon,
} from "lucide-react";
import { format } from "date-fns";
import { it } from "date-fns/locale";

import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useClients } from "@/hooks/useClients";
import {
  useAllCommunications,
  type CommunicationLogEnriched,
} from "@/hooks/useCommunications";

// ── Config ──

const CHANNEL_CONFIG: Record<string, { icon: LucideIcon; label: string; color: string }> = {
  whatsapp: { icon: MessageCircle, label: "WhatsApp", color: "text-emerald-600 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/30" },
  telefono: { icon: Phone, label: "Telefonata", color: "text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30" },
  email: { icon: Mail, label: "Email", color: "text-violet-600 bg-violet-100 dark:text-violet-400 dark:bg-violet-900/30" },
  nota: { icon: StickyNote, label: "Nota", color: "text-amber-600 bg-amber-100 dark:text-amber-400 dark:bg-amber-900/30" },
};

const TEMPLATE_LABELS: Record<string, string> = {
  checkin: "Check-in",
  birthday: "Auguri",
  renewal: "Rinnovo",
  workout: "Scheda",
  appointment: "Appuntamento",
  class: "Classe",
  progress: "Progressi",
  welcome: "Benvenuto",
  free: "Messaggio libero",
  rate: "Rata",
};

// ── Component ──

interface CommunicationRegistryProps {
  initialClientId?: number | null;
}

export function CommunicationRegistry({ initialClientId }: CommunicationRegistryProps) {
  const [clientFilter, setClientFilter] = useState<string>(
    initialClientId ? String(initialClientId) : "__all__",
  );
  const [searchText, setSearchText] = useState("");

  const selectedClientId = clientFilter === "__all__" ? null : parseInt(clientFilter, 10);
  const { data: clientsData } = useClients();
  const { data, isLoading } = useAllCommunications(selectedClientId);

  const clients = useMemo(() => {
    const items = clientsData?.items ?? [];
    return items.sort((a, b) => `${a.cognome} ${a.nome}`.localeCompare(`${b.cognome} ${b.nome}`));
  }, [clientsData]);

  // Filter by search text
  const items = useMemo(() => {
    const all = data?.items ?? [];
    if (!searchText) return all;
    const q = searchText.toLowerCase();
    return all.filter((item) =>
      `${item.client_nome} ${item.client_cognome} ${item.anteprima} ${item.canale}`.toLowerCase().includes(q),
    );
  }, [data, searchText]);

  // Group by date
  const grouped = useMemo(() => {
    const map = new Map<string, CommunicationLogEnriched[]>();
    for (const item of items) {
      const dateKey = item.created_at
        ? format(new Date(item.created_at), "yyyy-MM-dd")
        : "sconosciuta";
      const existing = map.get(dateKey);
      if (existing) existing.push(item);
      else map.set(dateKey, [item]);
    }
    return map;
  }, [items]);

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Select value={clientFilter} onValueChange={setClientFilter}>
          <SelectTrigger className="h-9 w-full sm:w-[220px]">
            <SelectValue placeholder="Tutti i clienti" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Tutti i clienti</SelectItem>
            {clients.map((c) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.cognome} {c.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Cerca nel registro..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="pl-9 h-9"
          />
        </div>
        <span className="text-[11px] font-medium text-muted-foreground tabular-nums shrink-0 px-1">
          {items.length} {items.length === 1 ? "comunicazione" : "comunicazioni"}
        </span>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
          <MessageCircle className="h-10 w-10 text-muted-foreground/20" />
          <div>
            <p className="text-sm font-medium text-muted-foreground">Nessuna comunicazione</p>
            <p className="text-xs text-muted-foreground/60">
              I messaggi inviati appariranno qui
            </p>
          </div>
        </div>
      ) : (
        <ScrollArea className="h-[calc(100vh-380px)] min-h-[280px]">
          <div className="space-y-4 pr-2">
            {Array.from(grouped.entries()).map(([dateKey, dayItems]) => (
              <div key={dateKey}>
                {/* Date header */}
                <div className="sticky top-0 z-10 mb-2 flex items-center gap-2 bg-background/95 py-1 backdrop-blur-sm">
                  <div className="h-px flex-1 bg-border" />
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {dateKey === "sconosciuta"
                      ? "Data sconosciuta"
                      : format(new Date(dateKey + "T00:00:00"), "EEEE d MMMM", { locale: it })}
                  </span>
                  <div className="h-px flex-1 bg-border" />
                </div>

                {/* Day items */}
                <div className="space-y-1">
                  {dayItems.map((item) => (
                    <RegistryRow key={item.id} item={item} showClient={!selectedClientId} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

// ── Row ──

function RegistryRow({ item, showClient }: { item: CommunicationLogEnriched; showClient: boolean }) {
  const cfg = CHANNEL_CONFIG[item.canale] ?? CHANNEL_CONFIG.nota;
  const Icon = cfg.icon;
  const templateLabel = item.template_usato
    ? TEMPLATE_LABELS[item.template_usato] ?? item.template_usato
    : null;

  return (
    <div className="flex items-start gap-3 rounded-lg border border-transparent px-3 py-2.5 transition-colors hover:bg-muted/30">
      {/* Channel icon */}
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${cfg.color}`}>
        <Icon className="h-4 w-4" />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          {showClient && (
            <span className="text-sm font-medium">
              {item.client_nome} {item.client_cognome}
            </span>
          )}
          <span className={`text-xs ${showClient ? "text-muted-foreground" : "font-medium"}`}>
            {cfg.label}
          </span>
          {templateLabel && (
            <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              {templateLabel}
            </span>
          )}
        </div>
        {item.anteprima && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
            {item.anteprima}
          </p>
        )}
      </div>

      {/* Time */}
      {item.created_at && (
        <span className="shrink-0 text-[10px] text-muted-foreground tabular-nums pt-0.5">
          {format(new Date(item.created_at), "HH:mm", { locale: it })}
        </span>
      )}
    </div>
  );
}
