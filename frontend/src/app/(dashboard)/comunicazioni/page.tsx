// src/app/(dashboard)/comunicazioni/page.tsx
"use client";

/**
 * Centro Comunicazioni WhatsApp — rubrica + invio multiplo.
 *
 * Architettura:
 * - useClients() carica tutti i clienti enriched (client-side filter)
 * - Selezione multipla via Set<number> (client_id)
 * - Filtri smart: stato, contratto, inattivita', rate
 * - Template selector con anteprima live
 * - Invio sequenziale wa.me (1 tab alla volta con contatore)
 * - Messaggio libero con firma trainer automatica
 */

import { useState, useMemo, useCallback } from "react";
import {
  MessageCircle,
  Users,
  Send,
  Eye,
  EyeOff,
  Search,
  Check,
  CheckCheck,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WhatsAppButton } from "@/components/ui/whatsapp-button";
import { surfaceRoleClassName } from "@/components/ui/surface-role";
import { useClients } from "@/hooks/useClients";
import { useLogCommunication } from "@/hooks/useCommunications";
import { useTrainerName } from "@/hooks/useTrainerName";
import { buildWhatsAppUrl } from "@/lib/format";
import { usePageReveal } from "@/lib/page-reveal";
import {
  waAppointmentReminder,
  waCheckIn,
  waRenewalReminder,
  waWorkoutShare,
  waBirthday,
  waNutritionPlan,
  waClassReminder,
  waProgressUpdate,
  waFreeMessage,
} from "@/lib/whatsapp-templates";
import type { ClientEnriched } from "@/types/api";

// ── Filter chip config ──

interface FilterChipDef {
  key: string;
  label: string;
  icon: LucideIcon;
  color: string;
  match: (c: ClientEnriched) => boolean;
}

const FILTER_CHIPS: FilterChipDef[] = [
  {
    key: "attivi",
    label: "Attivi",
    icon: Users,
    color: "bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-400 dark:border-emerald-800",
    match: (c) => c.stato === "Attivo",
  },
  {
    key: "inattivi",
    label: "Inattivi",
    icon: Users,
    color: "bg-zinc-100 text-zinc-600 border-zinc-300 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-700",
    match: (c) => c.stato === "Inattivo",
  },
  {
    key: "con_crediti",
    label: "Con crediti",
    icon: Check,
    color: "bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/40 dark:text-blue-400 dark:border-blue-800",
    match: (c) => c.crediti_residui > 0,
  },
  {
    key: "rate_scadute",
    label: "Rate scadute",
    icon: Check,
    color: "bg-red-100 text-red-700 border-red-300 dark:bg-red-900/40 dark:text-red-400 dark:border-red-800",
    match: (c) => c.ha_rate_scadute,
  },
];

// ── Template config ──

interface TemplateDef {
  key: string;
  label: string;
  description: string;
  build: (clientName: string, trainerName: string) => string;
}

const TEMPLATES: TemplateDef[] = [
  {
    key: "free",
    label: "Messaggio libero",
    description: "Scrivi un messaggio personalizzato",
    build: (_cn, tn) => waFreeMessage(tn),
  },
  {
    key: "checkin",
    label: "Check-in",
    description: "Riattiva clienti inattivi",
    build: (cn, tn) => waCheckIn(cn, tn, 14),
  },
  {
    key: "birthday",
    label: "Auguri compleanno",
    description: "Messaggio di auguri",
    build: (cn, tn) => waBirthday(cn, tn),
  },
  {
    key: "workout",
    label: "Scheda pronta",
    description: "Avvisa che la scheda e' pronta",
    build: (cn, tn) => waWorkoutShare(cn, tn),
  },
  {
    key: "nutrition",
    label: "Piano alimentare",
    description: "Avvisa che il piano e' pronto",
    build: (cn, tn) => waNutritionPlan(cn, tn),
  },
  {
    key: "progress",
    label: "Check progressi",
    description: "Aggiornamento misurazioni",
    build: (cn, tn) => waProgressUpdate(cn, tn),
  },
  {
    key: "class",
    label: "Reminder classe",
    description: "Promemoria lezione di gruppo",
    build: (cn, tn) => waClassReminder(cn, tn, "Allenamento", "domani", "10:00"),
  },
  {
    key: "renewal",
    label: "Rinnovo contratto",
    description: "Sollecito rinnovo in scadenza",
    build: (cn, tn) => waRenewalReminder(cn, tn, "allenamento", 7, 3),
  },
  {
    key: "appointment",
    label: "Conferma appuntamento",
    description: "Conferma sessione programmata",
    build: (cn, tn) => waAppointmentReminder(cn, tn, "domani", "10:00"),
  },
];

// ════════════════════════════════════════════════════════════
// PAGINA
// ════════════════════════════════════════════════════════════

export default function ComunicazioniPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const { data, isLoading } = useClients();
  const trainerName = useTrainerName();
  const logComm = useLogCommunication();

  // State
  const [search, setSearch] = useState("");
  const [activeFilters, setActiveFilters] = useState<Set<string>>(() => new Set(["attivi"]));
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [templateKey, setTemplateKey] = useState("free");
  const [customMessage, setCustomMessage] = useState("");
  const [sendQueue, setSendQueue] = useState<ClientEnriched[]>([]);
  const [sendIndex, setSendIndex] = useState(0);
  const [isSending, setIsSending] = useState(false);

  // Filtered clients
  const clients = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((c) => {
      // Telefono obbligatorio per WhatsApp
      if (!c.telefono) return false;
      // Search
      if (search) {
        const q = search.toLowerCase();
        const match = `${c.nome} ${c.cognome} ${c.telefono ?? ""} ${c.email ?? ""}`.toLowerCase();
        if (!match.includes(q)) return false;
      }
      // Filters (OR logic: client matches if any active filter applies)
      if (activeFilters.size > 0) {
        const matchesAny = FILTER_CHIPS.some(
          (chip) => activeFilters.has(chip.key) && chip.match(c),
        );
        if (!matchesAny) return false;
      }
      return true;
    });
  }, [data, search, activeFilters]);

  // Selected template
  const selectedTemplate = TEMPLATES.find((t) => t.key === templateKey) ?? TEMPLATES[0];

  // Build message for a specific client
  const buildMessage = useCallback(
    (client: ClientEnriched): string => {
      const firstName = client.nome.split(" ")[0];
      if (templateKey === "free" && customMessage.trim()) {
        return `${customMessage.trim()}\n— ${trainerName}`;
      }
      return selectedTemplate.build(firstName, trainerName);
    },
    [templateKey, customMessage, trainerName, selectedTemplate],
  );

  // Preview message (using first selected or "Mario")
  const previewMessage = useMemo(() => {
    const firstSelected = clients.find((c) => selectedIds.has(c.id));
    const sampleName = firstSelected?.nome.split(" ")[0] ?? "Mario";
    if (templateKey === "free" && customMessage.trim()) {
      return `${customMessage.trim()}\n— ${trainerName}`;
    }
    return selectedTemplate.build(sampleName, trainerName);
  }, [clients, selectedIds, templateKey, customMessage, trainerName, selectedTemplate]);

  // Toggle filter
  const handleToggleFilter = useCallback((key: string) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  // Toggle select client
  const handleToggleClient = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  // Select all visible
  const handleSelectAll = useCallback(() => {
    const allVisible = new Set(clients.map((c) => c.id));
    const allSelected = clients.every((c) => selectedIds.has(c.id));
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(allVisible);
    }
  }, [clients, selectedIds]);

  // Log communication (fire-and-forget)
  const logSend = useCallback((client: ClientEnriched, msg: string) => {
    logComm.mutate({
      id_cliente: client.id,
      canale: "whatsapp",
      template_usato: templateKey,
      anteprima: msg.slice(0, 200),
    });
  }, [logComm, templateKey]);

  // Start sequential send
  const handleStartSend = useCallback(() => {
    const queue = clients.filter((c) => selectedIds.has(c.id));
    if (queue.length === 0) return;
    setSendQueue(queue);
    setSendIndex(0);
    setIsSending(true);
    // Open first
    const msg = buildMessage(queue[0]);
    const url = buildWhatsAppUrl(queue[0].telefono, msg);
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
      logSend(queue[0], msg);
    }
  }, [clients, selectedIds, buildMessage, logSend]);

  // Send next in queue
  const handleSendNext = useCallback(() => {
    const nextIdx = sendIndex + 1;
    if (nextIdx >= sendQueue.length) {
      setIsSending(false);
      setSendQueue([]);
      setSendIndex(0);
      return;
    }
    setSendIndex(nextIdx);
    const client = sendQueue[nextIdx];
    const msg = buildMessage(client);
    const url = buildWhatsAppUrl(client.telefono, msg);
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
      logSend(client, msg);
    }
  }, [sendIndex, sendQueue, buildMessage, logSend]);

  // Cancel send
  const handleCancelSend = useCallback(() => {
    setIsSending(false);
    setSendQueue([]);
    setSendIndex(0);
  }, []);

  const selectedCount = selectedIds.size;
  const allVisibleSelected = clients.length > 0 && clients.every((c) => selectedIds.has(c.id));

  return (
    <div className="min-w-0 space-y-4 md:space-y-5">
      {/* ── Header ── */}
      <div className={`flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${revealClass(0)}`} style={revealStyle(0)}>
        <div>
          <h1 className="text-xl font-bold tracking-tight sm:text-2xl">Comunicazioni</h1>
          <p className="text-sm text-muted-foreground">
            Invia messaggi WhatsApp ai tuoi clienti
          </p>
        </div>
        {selectedCount > 0 && !isSending && (
          <Button
            onClick={handleStartSend}
            className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Send className="h-4 w-4" />
            Invia a {selectedCount} {selectedCount === 1 ? "cliente" : "clienti"}
          </Button>
        )}
      </div>

      {/* ── Sending progress bar ── */}
      {isSending && sendQueue.length > 0 && (
        <div className={surfaceRoleClassName({ role: "page", tone: "neutral" }, "p-4")}>
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCheck className="h-4 w-4 text-emerald-600" />
              <span className="text-sm font-semibold">
                Invio in corso: {sendIndex + 1} / {sendQueue.length}
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={handleCancelSend} className="text-xs">
              Annulla
            </Button>
          </div>
          {/* Progress bar */}
          <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all duration-300"
              style={{ width: `${((sendIndex + 1) / sendQueue.length) * 100}%` }}
            />
          </div>
          {/* Current client */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Inviato a: <span className="font-medium text-foreground">{sendQueue[sendIndex].nome} {sendQueue[sendIndex].cognome}</span>
            </span>
            {sendIndex + 1 < sendQueue.length ? (
              <Button onClick={handleSendNext} size="sm" className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white">
                Prossimo
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button onClick={handleCancelSend} size="sm" variant="outline" className="gap-1.5">
                <Check className="h-3.5 w-3.5" />
                Completato
              </Button>
            )}
          </div>
        </div>
      )}

      {/* ── Main layout: 2 colonne ── */}
      <div className={`grid gap-4 md:gap-5 lg:grid-cols-5 ${revealClass(80)}`} style={revealStyle(80)}>
        {/* LEFT: Lista clienti (3/5) */}
        <div className="lg:col-span-3 space-y-3">
          {/* Search + select all */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Cerca cliente..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              className="h-9 shrink-0 text-xs gap-1.5"
            >
              {allVisibleSelected ? (
                <>
                  <EyeOff className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Deseleziona</span>
                </>
              ) : (
                <>
                  <Eye className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Seleziona tutti</span>
                </>
              )}
            </Button>
          </div>

          {/* Filter chips */}
          <div className="flex flex-wrap gap-1.5">
            {FILTER_CHIPS.map((chip) => {
              const active = activeFilters.has(chip.key);
              return (
                <button
                  key={chip.key}
                  type="button"
                  onClick={() => handleToggleFilter(chip.key)}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all ${
                    active
                      ? chip.color
                      : "bg-white text-muted-foreground border-zinc-200 dark:bg-zinc-900 dark:border-zinc-700 opacity-50"
                  }`}
                >
                  {active ? (
                    <Eye className="h-3 w-3" />
                  ) : (
                    <EyeOff className="h-3 w-3" />
                  )}
                  {chip.label}
                </button>
              );
            })}
          </div>

          {/* Client list */}
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full rounded-lg" />
              ))}
            </div>
          ) : clients.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-center">
              <Users className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">Nessun cliente trovato</p>
              <p className="text-xs text-muted-foreground/60">
                Prova a modificare i filtri o la ricerca
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[calc(100vh-380px)] min-h-[300px]">
              <div className="space-y-1">
                {/* Counter */}
                <div className="flex items-center justify-between px-1 py-1">
                  <span className="text-[11px] font-medium text-muted-foreground">
                    {clients.length} {clients.length === 1 ? "cliente" : "clienti"}
                    {selectedCount > 0 && (
                      <> · <span className="text-emerald-600 dark:text-emerald-400">{selectedCount} selezionati</span></>
                    )}
                  </span>
                </div>

                {clients.map((client) => {
                  const isSelected = selectedIds.has(client.id);
                  return (
                    <div
                      key={client.id}
                      onClick={() => handleToggleClient(client.id)}
                      className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 transition-all ${
                        isSelected
                          ? "border-emerald-300 bg-emerald-50/60 dark:border-emerald-800 dark:bg-emerald-950/20"
                          : "border-transparent hover:bg-muted/40"
                      }`}
                    >
                      {/* Checkbox */}
                      <div
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors ${
                          isSelected
                            ? "border-emerald-500 bg-emerald-500 text-white"
                            : "border-zinc-300 dark:border-zinc-600"
                        }`}
                      >
                        {isSelected && <Check className="h-3 w-3" />}
                      </div>

                      {/* Client info */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium truncate">
                            {client.nome} {client.cognome}
                          </span>
                          <Badge
                            variant="outline"
                            className={`text-[9px] px-1.5 py-0 ${
                              client.stato === "Attivo"
                                ? "border-emerald-400 text-emerald-600 dark:text-emerald-400"
                                : "text-muted-foreground"
                            }`}
                          >
                            {client.stato}
                          </Badge>
                          {client.ha_rate_scadute && (
                            <Badge variant="destructive" className="text-[9px] px-1.5 py-0">
                              Rate scadute
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground truncate block">
                          {client.telefono}
                        </span>
                      </div>

                      {/* Quick WA button (single) */}
                      <WhatsAppButton
                        phone={client.telefono}
                        message={buildMessage(client)}
                        variant="icon"
                        clientId={client.id}
                        templateKey={templateKey}
                      />
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </div>

        {/* RIGHT: Template + Preview (2/5) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Template selector */}
          <div className={surfaceRoleClassName({ role: "page", tone: "neutral" }, "p-4")}>
            <h3 className="mb-3 text-sm font-bold flex items-center gap-2">
              <MessageCircle className="h-4 w-4 text-emerald-600" />
              Modello messaggio
            </h3>
            <div className="space-y-1">
              {TEMPLATES.map((tpl) => (
                <button
                  key={tpl.key}
                  type="button"
                  onClick={() => setTemplateKey(tpl.key)}
                  className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
                    templateKey === tpl.key
                      ? "bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800"
                      : "hover:bg-muted/50"
                  }`}
                >
                  <span className="text-sm font-medium">{tpl.label}</span>
                  <span className="block text-[11px] text-muted-foreground">{tpl.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Custom message (only for free template) */}
          {templateKey === "free" && (
            <div className={surfaceRoleClassName({ role: "page", tone: "neutral" }, "p-4")}>
              <h3 className="mb-2 text-sm font-bold">Messaggio personalizzato</h3>
              <Textarea
                placeholder="Scrivi il tuo messaggio..."
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={4}
                className="text-sm"
              />
              <p className="mt-1.5 text-[10px] text-muted-foreground">
                La firma &ldquo;— {trainerName}&rdquo; viene aggiunta automaticamente
              </p>
            </div>
          )}

          {/* Preview */}
          <div className={surfaceRoleClassName({ role: "page", tone: "neutral" }, "p-4")}>
            <h3 className="mb-2 text-sm font-bold flex items-center gap-2">
              <Eye className="h-4 w-4 text-muted-foreground" />
              Anteprima
            </h3>
            <div className="rounded-lg bg-emerald-50/80 p-3 dark:bg-emerald-950/20">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed text-foreground font-sans">
                {previewMessage}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
