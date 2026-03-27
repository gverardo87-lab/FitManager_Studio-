// src/app/(dashboard)/comunicazioni/page.tsx
"use client";

/**
 * Centro Comunicazioni WhatsApp — rubrica + invio multiplo.
 *
 * Layout CRM-grade:
 * 1. Hero strip emerald con KPI live (clienti raggiungibili, selezionati, template)
 * 2. Toolbar compatta (search + filtri chip + select all + CTA invio)
 * 3. Split panel: lista clienti (left) + composer (right: template grid + anteprima WhatsApp)
 * 4. Sending overlay con progress stepper
 */

import { useState, useMemo, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
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
  Smartphone,
  X,
  Pencil,
  type LucideIcon,
  Cake,
  Dumbbell,
  UtensilsCrossed,
  TrendingUp,
  Calendar,
  FileText,
  UserCheck,
  Heart,
  ClipboardList,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WhatsAppButton } from "@/components/ui/whatsapp-button";
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
import { CommunicationRegistry } from "@/components/communications/CommunicationRegistry";
import type { ClientEnriched } from "@/types/api";

// ── Filter config (2 assi: stato + situazione, pattern pagina Clienti) ──

interface FilterChipDef {
  key: string;
  label: string;
  axis: "stato" | "situazione";
  color: string;
  activeColor: string;
  match: (c: ClientEnriched) => boolean;
}

const STATO_CHIPS: FilterChipDef[] = [
  {
    key: "attivi",
    label: "Attivi",
    axis: "stato",
    color: "border-emerald-200 dark:border-emerald-800",
    activeColor: "bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-400 dark:border-emerald-700",
    match: (c) => c.stato === "Attivo",
  },
  {
    key: "inattivi",
    label: "Inattivi",
    axis: "stato",
    color: "border-zinc-200 dark:border-zinc-700",
    activeColor: "bg-zinc-100 text-zinc-700 border-zinc-300 dark:bg-zinc-800/40 dark:text-zinc-400 dark:border-zinc-600",
    match: (c) => c.stato === "Inattivo",
  },
];

const SITUAZIONE_CHIPS: FilterChipDef[] = [
  {
    key: "con_crediti",
    label: "Con crediti",
    axis: "situazione",
    color: "border-blue-200 dark:border-blue-800",
    activeColor: "bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900/40 dark:text-blue-400 dark:border-blue-700",
    match: (c) => c.crediti_residui > 0,
  },
  {
    key: "rate_scadute",
    label: "Rate scadute",
    axis: "situazione",
    color: "border-red-200 dark:border-red-800",
    activeColor: "bg-red-100 text-red-700 border-red-300 dark:bg-red-900/40 dark:text-red-400 dark:border-red-700",
    match: (c) => c.ha_rate_scadute,
  },
];

// ── Template config ──

interface TemplateDef {
  key: string;
  label: string;
  icon: LucideIcon;
  color: string;
  build: (clientName: string, trainerName: string) => string;
}

const TEMPLATES: TemplateDef[] = [
  {
    key: "free",
    label: "Libero",
    icon: Pencil,
    color: "text-zinc-600 bg-zinc-100 dark:text-zinc-400 dark:bg-zinc-800",
    build: (_cn, tn) => waFreeMessage(tn),
  },
  {
    key: "checkin",
    label: "Check-in",
    icon: Heart,
    color: "text-orange-600 bg-orange-100 dark:text-orange-400 dark:bg-orange-900/30",
    build: (cn, tn) => waCheckIn(cn, tn, 14),
  },
  {
    key: "birthday",
    label: "Auguri",
    icon: Cake,
    color: "text-pink-600 bg-pink-100 dark:text-pink-400 dark:bg-pink-900/30",
    build: (cn, tn) => waBirthday(cn, tn),
  },
  {
    key: "workout",
    label: "Scheda",
    icon: Dumbbell,
    color: "text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30",
    build: (cn, tn) => waWorkoutShare(cn, tn),
  },
  {
    key: "nutrition",
    label: "Nutrizione",
    icon: UtensilsCrossed,
    color: "text-emerald-600 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/30",
    build: (cn, tn) => waNutritionPlan(cn, tn),
  },
  {
    key: "progress",
    label: "Progressi",
    icon: TrendingUp,
    color: "text-violet-600 bg-violet-100 dark:text-violet-400 dark:bg-violet-900/30",
    build: (cn, tn) => waProgressUpdate(cn, tn),
  },
  {
    key: "class",
    label: "Classe",
    icon: Users,
    color: "text-teal-600 bg-teal-100 dark:text-teal-400 dark:bg-teal-900/30",
    build: (cn, tn) => waClassReminder(cn, tn, "Allenamento", "domani", "10:00"),
  },
  {
    key: "renewal",
    label: "Rinnovo",
    icon: FileText,
    color: "text-amber-600 bg-amber-100 dark:text-amber-400 dark:bg-amber-900/30",
    build: (cn, tn) => waRenewalReminder(cn, tn, "allenamento", 7, 3),
  },
  {
    key: "appointment",
    label: "Sessione",
    icon: Calendar,
    color: "text-sky-600 bg-sky-100 dark:text-sky-400 dark:bg-sky-900/30",
    build: (cn, tn) => waAppointmentReminder(cn, tn, "domani", "10:00"),
  },
];

// ════════════════════════════════════════════════════════════
// PAGINA
// ════════════════════════════════════════════════════════════

export default function ComunicazioniPage() {
  const { revealClass, revealStyle } = usePageReveal();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Tab state from URL
  const activeTab = searchParams.get("tab") === "registro" ? "registro" : "invia";
  const urlClienteId = searchParams.get("cliente");
  const initialRegistryClientId = urlClienteId ? parseInt(urlClienteId, 10) : null;

  const setActiveTab = useCallback((tab: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (tab === "invia") {
      params.delete("tab");
      params.delete("cliente");
    } else {
      params.set("tab", tab);
    }
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [searchParams, router, pathname]);

  const { data, isLoading } = useClients();
  const trainerName = useTrainerName();
  const logComm = useLogCommunication();

  // State
  const [search, setSearch] = useState("");
  const [activeStati, setActiveStati] = useState<Set<string>>(() => new Set(["attivi"]));
  const [activeSituazioni, setActiveSituazioni] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [templateKey, setTemplateKey] = useState("free");
  const [customMessage, setCustomMessage] = useState("");
  const [sendQueue, setSendQueue] = useState<ClientEnriched[]>([]);
  const [sendIndex, setSendIndex] = useState(0);
  const [isSending, setIsSending] = useState(false);

  // Filtered clients
  const allWithPhone = useMemo(() => (data?.items ?? []).filter((c) => c.telefono), [data]);

  const clients = useMemo(() => {
    return allWithPhone.filter((c) => {
      // Search
      if (search) {
        const q = search.toLowerCase();
        const match = `${c.nome} ${c.cognome} ${c.telefono ?? ""} ${c.email ?? ""}`.toLowerCase();
        if (!match.includes(q)) return false;
      }
      // Asse 1: Stato (AND — client.stato deve matchare un chip attivo)
      if (activeStati.size > 0) {
        const matchesStato = STATO_CHIPS.some(
          (chip) => activeStati.has(chip.key) && chip.match(c),
        );
        if (!matchesStato) return false;
      }
      // Asse 2: Situazione (AND — se attivo, il cliente deve matchare)
      if (activeSituazioni.size > 0) {
        const matchesSit = SITUAZIONE_CHIPS.some(
          (chip) => activeSituazioni.has(chip.key) && chip.match(c),
        );
        if (!matchesSit) return false;
      }
      return true;
    });
  }, [allWithPhone, search, activeStati, activeSituazioni]);

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

  // Preview message
  const previewMessage = useMemo(() => {
    const firstSelected = clients.find((c) => selectedIds.has(c.id));
    const sampleName = firstSelected?.nome.split(" ")[0] ?? "Mario";
    if (templateKey === "free" && customMessage.trim()) {
      return `${customMessage.trim()}\n— ${trainerName}`;
    }
    return selectedTemplate.build(sampleName, trainerName);
  }, [clients, selectedIds, templateKey, customMessage, trainerName, selectedTemplate]);

  // Toggle filter (2 assi)
  const handleToggleFilter = useCallback((chip: FilterChipDef) => {
    const setter = chip.axis === "stato" ? setActiveStati : setActiveSituazioni;
    setter((prev) => {
      const next = new Set(prev);
      if (next.has(chip.key)) next.delete(chip.key); else next.add(chip.key);
      return next;
    });
  }, []);

  // Toggle select client
  const handleToggleClient = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  // Select all visible
  const handleSelectAll = useCallback(() => {
    const allSelected = clients.length > 0 && clients.every((c) => selectedIds.has(c.id));
    setSelectedIds(allSelected ? new Set() : new Set(clients.map((c) => c.id)));
  }, [clients, selectedIds]);

  // Log communication
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
    const msg = buildMessage(queue[0]);
    const url = buildWhatsAppUrl(queue[0].telefono, msg);
    if (url) { window.open(url, "_blank", "noopener,noreferrer"); logSend(queue[0], msg); }
  }, [clients, selectedIds, buildMessage, logSend]);

  // Send next
  const handleSendNext = useCallback(() => {
    const nextIdx = sendIndex + 1;
    if (nextIdx >= sendQueue.length) { setIsSending(false); setSendQueue([]); setSendIndex(0); return; }
    setSendIndex(nextIdx);
    const client = sendQueue[nextIdx];
    const msg = buildMessage(client);
    const url = buildWhatsAppUrl(client.telefono, msg);
    if (url) { window.open(url, "_blank", "noopener,noreferrer"); logSend(client, msg); }
  }, [sendIndex, sendQueue, buildMessage, logSend]);

  const handleCancelSend = useCallback(() => {
    setIsSending(false); setSendQueue([]); setSendIndex(0);
  }, []);

  const selectedCount = selectedIds.size;
  const allVisibleSelected = clients.length > 0 && clients.every((c) => selectedIds.has(c.id));

  return (
    <div className="min-w-0 space-y-4 md:space-y-5">
      {/* ══════════ HERO STRIP ══════════ */}
      <div
        className={`relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 p-5 shadow-lg sm:p-6 ${revealClass(0)}`}
        style={revealStyle(0)}
      >
        {/* Background pattern */}
        <div className="pointer-events-none absolute inset-0 opacity-[0.07]" style={{
          backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
          backgroundSize: "24px 24px",
        }} />
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/5 blur-2xl" />

        <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/15 backdrop-blur-sm">
              <MessageCircle className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white sm:text-xl">Centro Comunicazioni</h1>
              <p className="text-sm text-emerald-100/80">
                Messaggi WhatsApp ai tuoi clienti
              </p>
            </div>
          </div>

          {/* KPI pills */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-1.5 backdrop-blur-sm">
              <Smartphone className="h-3.5 w-3.5 text-emerald-200" />
              <span className="text-sm font-bold text-white tabular-nums">{allWithPhone.length}</span>
              <span className="text-xs text-emerald-200 hidden sm:inline">raggiungibili</span>
            </div>
            {selectedCount > 0 && (
              <div className="flex items-center gap-2 rounded-lg bg-white/20 px-3 py-1.5 backdrop-blur-sm">
                <UserCheck className="h-3.5 w-3.5 text-white" />
                <span className="text-sm font-bold text-white tabular-nums">{selectedCount}</span>
                <span className="text-xs text-emerald-100 hidden sm:inline">selezionati</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ══════════ TAB SWITCHER ══════════ */}
      <div className={`flex gap-1 rounded-lg bg-muted/50 p-1 ${revealClass(40)}`} style={revealStyle(40)}>
        <button
          type="button"
          onClick={() => setActiveTab("invia")}
          className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all ${
            activeTab === "invia"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Send className="h-3.5 w-3.5" />
          Invia
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("registro")}
          className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all ${
            activeTab === "registro"
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <ClipboardList className="h-3.5 w-3.5" />
          Registro
        </button>
      </div>

      {/* ══════════ TAB: REGISTRO ══════════ */}
      {activeTab === "registro" && (
        <div className={revealClass(80)} style={revealStyle(80)}>
          <CommunicationRegistry initialClientId={initialRegistryClientId} />
        </div>
      )}

      {/* ══════════ TAB: INVIA ══════════ */}
      {activeTab === "invia" && <>

      {/* ══════════ SENDING OVERLAY ══════════ */}
      {isSending && sendQueue.length > 0 && (
        <div className="rounded-xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50 p-4 dark:border-emerald-900/40 dark:from-emerald-950/20 dark:to-teal-950/20">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <CheckCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <span className="text-sm font-bold">
                  Invio {sendIndex + 1} di {sendQueue.length}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {sendQueue[sendIndex].nome} {sendQueue[sendIndex].cognome}
                </span>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={handleCancelSend} className="h-7 w-7 p-0">
              <X className="h-4 w-4" />
            </Button>
          </div>
          {/* Stepper dots */}
          <div className="mb-3 flex items-center gap-1">
            {sendQueue.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                  i <= sendIndex
                    ? "bg-emerald-500"
                    : "bg-zinc-200 dark:bg-zinc-700"
                }`}
              />
            ))}
          </div>
          <div className="flex justify-end">
            {sendIndex + 1 < sendQueue.length ? (
              <Button onClick={handleSendNext} size="sm" className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white">
                Prossimo <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button onClick={handleCancelSend} size="sm" variant="outline" className="gap-1.5">
                <Check className="h-3.5 w-3.5" /> Completato
              </Button>
            )}
          </div>
        </div>
      )}

      {/* ══════════ TOOLBAR ══════════ */}
      <div className={`space-y-3 ${revealClass(60)}`} style={revealStyle(60)}>
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Cerca cliente..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
          {/* Select all */}
          <Button variant="outline" size="sm" onClick={handleSelectAll} className="h-9 shrink-0 text-xs gap-1.5">
            {allVisibleSelected ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{allVisibleSelected ? "Deseleziona" : "Seleziona tutti"}</span>
          </Button>
          {/* CTA invio — sempre visibile */}
          {selectedCount > 0 && !isSending && (
            <Button onClick={handleStartSend} size="sm" className="h-9 gap-2 bg-emerald-600 hover:bg-emerald-700 text-white">
              <Send className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Invia a</span> {selectedCount}
            </Button>
          )}
        </div>
        {/* Filter chips — 2 righe: stato + situazione */}
        <div className="flex flex-wrap items-center gap-1.5">
          {[...STATO_CHIPS, ...SITUAZIONE_CHIPS].map((chip, i) => {
            const active = chip.axis === "stato"
              ? activeStati.has(chip.key)
              : activeSituazioni.has(chip.key);
            return (
              <button
                key={chip.key}
                type="button"
                onClick={() => handleToggleFilter(chip)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all ${
                  active ? chip.activeColor : `bg-background text-muted-foreground ${chip.color} opacity-60 hover:opacity-100`
                }`}
              >
                {active ? <Check className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                {chip.label}
              </button>
            );
          })}
          {/* Separatore + counter */}
          <span className="flex items-center px-2 text-[11px] font-medium text-muted-foreground tabular-nums">
            {clients.length} {clients.length === 1 ? "cliente" : "clienti"}
            {selectedCount > 0 && <> · <span className="text-emerald-600 dark:text-emerald-400">{selectedCount} sel.</span></>}
          </span>
        </div>
      </div>

      {/* ══════════ SPLIT PANEL ══════════ */}
      <div className={`grid min-w-0 gap-4 md:gap-5 lg:grid-cols-3 ${revealClass(120)}`} style={revealStyle(120)}>
        {/* ── LEFT: Client List (2/3) ── */}
        <div className="lg:col-span-2">
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-[52px] w-full rounded-lg" />
              ))}
            </div>
          ) : clients.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
              <Users className="h-10 w-10 text-muted-foreground/20" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Nessun cliente trovato</p>
                <p className="text-xs text-muted-foreground/60">Modifica i filtri o la ricerca</p>
              </div>
            </div>
          ) : (
            <ScrollArea className="h-[calc(100vh-420px)] min-h-[280px]">
              <div className="space-y-1 pr-2">
                {clients.map((client) => {
                  const isSelected = selectedIds.has(client.id);
                  return (
                    <div
                      key={client.id}
                      onClick={() => handleToggleClient(client.id)}
                      className={`group flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 transition-all duration-150 ${
                        isSelected
                          ? "border-emerald-300 bg-emerald-50/70 shadow-sm dark:border-emerald-800 dark:bg-emerald-950/25"
                          : "border-transparent hover:border-zinc-200 hover:bg-muted/30 dark:hover:border-zinc-800"
                      }`}
                    >
                      {/* Checkbox */}
                      <div className={`flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded transition-colors ${
                        isSelected
                          ? "bg-emerald-500 text-white"
                          : "border border-zinc-300 group-hover:border-zinc-400 dark:border-zinc-600"
                      }`}>
                        {isSelected && <Check className="h-3 w-3" />}
                      </div>

                      {/* Avatar initials */}
                      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        isSelected
                          ? "bg-emerald-200 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
                          : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                      }`}>
                        {client.nome[0]}{client.cognome[0]}
                      </div>

                      {/* Info */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-medium truncate">{client.nome} {client.cognome}</span>
                          {client.ha_rate_scadute && (
                            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" title="Rate scadute" />
                          )}
                        </div>
                        <span className="text-[11px] text-muted-foreground truncate block tabular-nums">
                          {client.telefono}
                        </span>
                      </div>

                      {/* Status + WA */}
                      <Badge
                        variant="outline"
                        className={`text-[9px] px-1.5 py-0 hidden sm:inline-flex ${
                          client.stato === "Attivo"
                            ? "border-emerald-400/50 text-emerald-600 dark:text-emerald-400"
                            : "text-muted-foreground"
                        }`}
                      >
                        {client.stato}
                      </Badge>
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

        {/* ── RIGHT: Composer (1/3) ── */}
        <div className="space-y-4">
          {/* Template grid */}
          <div className="rounded-xl border p-4">
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Modello messaggio
            </p>
            <div className="grid grid-cols-3 gap-1.5">
              {TEMPLATES.map((tpl) => {
                const active = templateKey === tpl.key;
                const Icon = tpl.icon;
                return (
                  <button
                    key={tpl.key}
                    type="button"
                    onClick={() => setTemplateKey(tpl.key)}
                    className={`flex flex-col items-center gap-1.5 rounded-lg border p-2.5 text-center transition-all duration-150 ${
                      active
                        ? "border-emerald-400 bg-emerald-50 shadow-sm dark:border-emerald-700 dark:bg-emerald-950/30"
                        : "border-transparent hover:border-zinc-200 hover:bg-muted/40 dark:hover:border-zinc-700"
                    }`}
                  >
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${tpl.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className={`text-[10px] font-medium leading-tight ${active ? "text-emerald-700 dark:text-emerald-400" : "text-muted-foreground"}`}>
                      {tpl.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom message (free only) */}
          {templateKey === "free" && (
            <div className="rounded-xl border p-4">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Testo libero
              </p>
              <Textarea
                placeholder="Scrivi il tuo messaggio..."
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={3}
                className="text-sm resize-none"
              />
              <p className="mt-1.5 text-[10px] text-muted-foreground">
                Firma automatica: — {trainerName}
              </p>
            </div>
          )}

          {/* Preview — WhatsApp bubble style */}
          <div className="rounded-xl border p-4">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Anteprima messaggio
            </p>
            <div className="rounded-xl bg-[#e7fed6] p-3 shadow-sm dark:bg-emerald-950/40">
              <pre className="whitespace-pre-wrap text-[13px] leading-relaxed text-zinc-800 dark:text-zinc-200 font-sans">
                {previewMessage}
              </pre>
              <div className="mt-1 flex justify-end">
                <span className="text-[10px] text-zinc-500 dark:text-zinc-500 tabular-nums">
                  {new Date().toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      </>}
    </div>
  );
}
