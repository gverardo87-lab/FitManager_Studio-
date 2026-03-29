// src/components/workouts/BuilderHeader.tsx
"use client";

/**
 * Header compatto del builder — 2 righe sticky.
 *
 * Row 1: [← Back] [Nome editabile]                    [Flask] [Salva]
 * Row 2: [Cliente ▾] [Obiettivo] [Livello] [Volume]   [Export buttons]
 *
 * ADR-008: workspace professionale. Flask toggle controlla SciencePanel.
 */

import { useState, useCallback, useEffect } from "react";
import { ArrowLeft, Pencil, Check, X, Save, FlaskConical, CalendarDays, Share2, Copy, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ExportButtons } from "@/components/workouts/ExportButtons";
import { OBIETTIVO_LABELS, LIVELLO_LABELS } from "@/lib/builder-utils";
import type { SafetyExportData } from "@/lib/export-workout-pdf";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import { OBIETTIVI_SCHEDA, LIVELLI_SCHEDA, type WorkoutPlan } from "@/types/api";
import apiClient from "@/lib/api-client";
import { buildWhatsAppUrl, formatShortDate } from "@/lib/format";
import { waWorkoutPortal } from "@/lib/whatsapp-templates";
import { getStoredTrainer } from "@/lib/auth";

interface BuilderHeaderProps {
  plan: WorkoutPlan;
  clients: { id: number; nome: string; cognome: string }[];
  clientNome?: string;
  clientTelefono?: string | null;
  totalVolume: number | null;
  isDirty: boolean;
  isSaving: boolean;
  lastSavedLabel: string | null;
  canUndo: boolean;
  canRedo: boolean;
  sessions: SessionCardData[];
  safetyExportData?: SafetyExportData;
  exportLogoDataUrl: string | null;
  fromParam: string | null;
  onUndo: () => void;
  onRedo: () => void;
  onSave: () => void;
  onGoBack: () => void;
  onNavigate: (href: string) => void;
  onUpdatePlan: (updates: Record<string, unknown>) => void;
  onLogoChange: (value: string | null) => void;
  showAdvanced: boolean;
  onToggleAdvanced: () => void;
  hasSessions: boolean;
}

export function BuilderHeader({
  plan, clients, clientNome, clientTelefono, totalVolume,
  isDirty, isSaving, lastSavedLabel, canUndo, canRedo,
  sessions, safetyExportData, exportLogoDataUrl, fromParam,
  onUndo, onRedo, onSave, onGoBack, onNavigate, onUpdatePlan, onLogoChange,
  showAdvanced, onToggleAdvanced, hasSessions,
}: BuilderHeaderProps) {
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [shareOpen, setShareOpen] = useState(false);

  const startEdit = useCallback((field: string, value: string) => {
    setEditingField(field);
    setEditValue(value);
  }, []);

  const saveEdit = useCallback(() => {
    if (!editingField) return;
    const v = editValue.trim();
    if (v && v !== String((plan as unknown as Record<string, unknown>)[editingField] ?? "")) {
      onUpdatePlan({ [editingField]: v });
    }
    setEditingField(null);
  }, [plan, editingField, editValue, onUpdatePlan]);

  const cancelEdit = useCallback(() => setEditingField(null), []);

  return (
    <div className="sticky top-0 z-30 -mx-3 lg:-mx-4 -mt-3 lg:-mt-4 mb-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80" data-print-hide>
      {/* ── Row 1: nome + save ── */}
      <div className="flex items-center gap-2 px-3 lg:px-4 h-11">
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={() => onGoBack()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>

        {editingField === "nome" ? (
          <div className="flex items-center gap-1 min-w-0 flex-1">
            <Input value={editValue} onChange={(e) => setEditValue(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") saveEdit(); if (e.key === "Escape") cancelEdit(); }} className="h-7 text-sm font-semibold flex-1 max-w-xs" autoFocus />
            <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={saveEdit}><Check className="h-3.5 w-3.5" /></Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={cancelEdit}><X className="h-3.5 w-3.5" /></Button>
          </div>
        ) : (
          <button onClick={() => startEdit("nome", plan.nome)} className="flex items-center gap-1.5 min-w-0 group/name">
            <span className="text-sm font-bold tracking-tight truncate">{plan.nome}</span>
            {clientNome && <span className="text-xs text-muted-foreground/50 hidden sm:inline">— {clientNome}</span>}
            <Pencil className="h-3 w-3 text-muted-foreground/20 group-hover/name:text-muted-foreground/50 transition-opacity shrink-0" />
          </button>
        )}

        <div className="flex-1" />

        {!isDirty && lastSavedLabel && (
          <span className="hidden sm:inline text-[10px] text-muted-foreground/40 tabular-nums">{lastSavedLabel}</span>
        )}

        {hasSessions && (
          <Button
            variant={showAdvanced ? "default" : "outline"}
            size="sm"
            className="h-7 text-[11px] gap-1.5"
            onClick={onToggleAdvanced}
          >
            <FlaskConical className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{showAdvanced ? "Analisi ON" : "Analisi"}</span>
          </Button>
        )}

        {isDirty && (
          <Button size="sm" className="h-7 text-xs gap-1" onClick={onSave} disabled={isSaving}>
            <Save className="h-3.5 w-3.5" />{isSaving ? "..." : "Salva"}
          </Button>
        )}
      </div>

      {/* ── Row 2: metadata + export ── */}
      <div className="flex items-center gap-1.5 px-3 lg:px-4 pb-2 overflow-x-auto">
        <Select value={plan.id_cliente ? String(plan.id_cliente) : "__none__"} onValueChange={(v) => onUpdatePlan({ id_cliente: v === "__none__" ? null : Number(v) })}>
          <SelectTrigger size="sm" className="h-7 w-[150px] text-xs shrink-0 border-0 bg-muted/40 hover:bg-muted/60 transition-colors">
            <SelectValue placeholder="Assegna cliente" />
          </SelectTrigger>
          <SelectContent position="popper" sideOffset={4}>
            <SelectItem value="__none__">Nessun cliente</SelectItem>
            {clients.map((c) => (<SelectItem key={c.id} value={String(c.id)}>{c.nome} {c.cognome}</SelectItem>))}
          </SelectContent>
        </Select>

        {plan.id_cliente && clientNome && (
          <>
            <button onClick={() => onNavigate(`/clienti/${plan.id_cliente}`)} className="text-[11px] text-primary hover:underline shrink-0">Profilo</button>
            <button onClick={() => onNavigate(`/allenamenti/${plan.id}?from=scheda-${plan.id}`)} className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline shrink-0">
              <CalendarDays className="h-3 w-3" />
              <span className="hidden sm:inline">Pianifica</span>
            </button>
          </>
        )}

        <div className="h-3.5 w-px bg-border/50 shrink-0" />

        <Select value={plan.obiettivo} onValueChange={(v) => onUpdatePlan({ obiettivo: v })}>
          <SelectTrigger className="h-6 w-auto text-[11px] border-0 bg-transparent px-1 font-medium hover:bg-muted/40 rounded transition-colors">
            <Badge variant="outline" className="text-[10px] cursor-pointer px-1.5 py-0">{OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}</Badge>
          </SelectTrigger>
          <SelectContent>{OBIETTIVI_SCHEDA.map((o) => (<SelectItem key={o} value={o}>{OBIETTIVO_LABELS[o]}</SelectItem>))}</SelectContent>
        </Select>

        <Select value={plan.livello} onValueChange={(v) => onUpdatePlan({ livello: v })}>
          <SelectTrigger className="h-6 w-auto text-[11px] border-0 bg-transparent px-1 font-medium hover:bg-muted/40 rounded transition-colors">
            <Badge variant="outline" className="text-[10px] cursor-pointer px-1.5 py-0">{LIVELLO_LABELS[plan.livello] ?? plan.livello}</Badge>
          </SelectTrigger>
          <SelectContent>{LIVELLI_SCHEDA.map((l) => (<SelectItem key={l} value={l}>{LIVELLO_LABELS[l]}</SelectItem>))}</SelectContent>
        </Select>

        {totalVolume != null && (
          <span className="text-[10px] font-medium tabular-nums text-muted-foreground/50 hidden lg:inline shrink-0">{totalVolume.toLocaleString("it-IT")} kg</span>
        )}

        <div className="flex-1" />

        <ExportButtons nome={plan.nome} obiettivo={plan.obiettivo} livello={plan.livello} clientNome={clientNome} clientTelefono={clientTelefono} durata_settimane={plan.durata_settimane} sessioni_per_settimana={plan.sessioni_per_settimana} sessioni={sessions} safety={safetyExportData} logoDataUrl={exportLogoDataUrl} onLogoChange={onLogoChange} />

        {/* Share workout portal button */}
        {plan.id_cliente && plan.data_fine ? (
          <>
            <Button variant="outline" size="sm" className="h-7 text-xs shrink-0 gap-1" onClick={() => setShareOpen(true)}>
              <Share2 className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Condividi</span>
            </Button>
            <ShareWorkoutDialog
              open={shareOpen}
              onOpenChange={setShareOpen}
              planId={plan.id}
              clientId={plan.id_cliente}
              clientNome={clientNome}
              clientTelefono={clientTelefono}
              planNome={plan.nome}
              dataFine={plan.data_fine}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}

// ── Share Workout Dialog ─────────────────────────────────────────────────────

function ShareWorkoutDialog({
  open,
  onOpenChange,
  planId,
  clientId,
  clientNome,
  clientTelefono,
  planNome,
  dataFine,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  planId: number;
  clientId: number;
  clientNome?: string;
  clientTelefono?: string | null;
  planNome: string;
  dataFine: string | null;
}) {
  const [loading, setLoading] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Trainer name per template WhatsApp
  const [tName, setTName] = useState("Il tuo trainer");
  useEffect(() => {
    try { const t = getStoredTrainer(); if (t) setTName(`${t.nome} ${t.cognome}`); }
    catch { /* noop */ }
  }, []);

  const generateLink = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post(`/clients/${clientId}/share-workout`, null, {
        params: { id_scheda: planId },
      });
      setShareUrl(res.data.url);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Errore nella generazione del link";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [clientId, planId]);

  const copyLink = useCallback(async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      toast.success("Link copiato!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Impossibile copiare il link");
    }
  }, [shareUrl]);

  // Messaggio WhatsApp pre-compilato con template
  const waUrl = shareUrl && clientTelefono
    ? buildWhatsAppUrl(
        clientTelefono,
        waWorkoutPortal(
          clientNome?.split(" ")[0] ?? "Ciao",
          tName,
          planNome,
          shareUrl,
          dataFine ?? "",
        ),
      )
    : null;

  const handleWhatsApp = useCallback(() => {
    if (!waUrl) return;
    window.open(waUrl, "_blank");
    // Auto-log comunicazione (fire-and-forget)
    apiClient.post("/communications", {
      id_cliente: clientId,
      canale: "whatsapp",
      template_usato: "workout_portal",
      anteprima: `Scheda "${planNome}" condivisa con link portale`,
    }).catch(() => {});
  }, [waUrl, clientId, planNome]);

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) { setShareUrl(null); setError(null); } }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Condividi scheda con il cliente</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Genera un link per <strong>{clientNome ?? "il cliente"}</strong> per compilare i dati
            di ogni sessione direttamente dal proprio smartphone.
          </p>

          {!shareUrl && !error ? (
            <Button onClick={generateLink} disabled={loading} className="w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Share2 className="h-4 w-4 mr-2" />}
              Genera link
            </Button>
          ) : null}

          {error ? (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
              {error}
            </div>
          ) : null}

          {shareUrl ? (
            <div className="space-y-3">
              {/* Link copiabile */}
              <div className="flex items-center gap-2 p-2 bg-muted rounded-md">
                <Input readOnly value={shareUrl} className="text-xs h-8 bg-white" />
                <Button variant="outline" size="sm" className="shrink-0 h-8" onClick={copyLink}>
                  {copied ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>

              {/* Bottone WhatsApp diretto */}
              {waUrl ? (
                <Button
                  className="w-full bg-[#25D366] hover:bg-[#1DA851] text-white"
                  onClick={handleWhatsApp}
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5 mr-2 fill-current" aria-hidden="true">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                  </svg>
                  Invia su WhatsApp
                </Button>
              ) : !clientTelefono ? (
                <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-md p-2">
                  Il cliente non ha un numero di telefono. Aggiungilo dal profilo per inviare via WhatsApp.
                </p>
              ) : null}

              <p className="text-xs text-muted-foreground">
                Il link e' valido fino alla fine della scheda + 7 giorni.
              </p>

              {shareUrl.startsWith("http://localhost") || shareUrl.startsWith("/public") ? (
                <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-md p-2">
                  Il link usa localhost. Per renderlo accessibile dal cellulare del cliente,
                  configura Tailscale Funnel o accedi da IP LAN.
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
