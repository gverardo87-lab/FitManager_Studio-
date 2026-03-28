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

import { useState, useCallback } from "react";
import { ArrowLeft, Pencil, Check, X, Save, FlaskConical, CalendarDays } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ExportButtons } from "@/components/workouts/ExportButtons";
import { OBIETTIVO_LABELS, LIVELLO_LABELS } from "@/lib/builder-utils";
import type { SafetyExportData } from "@/lib/export-workout-pdf";
import type { SessionCardData } from "@/components/workouts/SessionCard";
import { OBIETTIVI_SCHEDA, LIVELLI_SCHEDA, type WorkoutPlan } from "@/types/api";

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
      </div>
    </div>
  );
}
