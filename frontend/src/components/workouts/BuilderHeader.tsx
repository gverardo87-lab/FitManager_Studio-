// src/components/workouts/BuilderHeader.tsx
"use client";

/**
 * Header compatto del builder — riga singola sticky.
 *
 * Layout: [← Back] [Nome editabile] [Cliente ▾] [Obiettivo ▾] [Livello ▾] ... [Export ⋯] [Salva]
 * Tutto in una riga. Nessun banner, nessun titolo gigante.
 * ADR-008: workspace professionale (Figma-style header).
 */

import { useState, useCallback } from "react";
import { ArrowLeft, Pencil, Check, X, Save, FlaskConical } from "lucide-react";
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
  plan, clients, clientNome, totalVolume,
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
      {/* ── Row 1: main toolbar ── */}
      <div className="flex items-center gap-2 px-3 lg:px-4 h-12">
        {/* Left: back + name */}
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={() => onGoBack()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>

        {editingField === "nome" ? (
          <div className="flex items-center gap-1 min-w-0">
            <Input value={editValue} onChange={(e) => setEditValue(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") saveEdit(); if (e.key === "Escape") cancelEdit(); }} className="h-7 text-sm font-semibold w-48" autoFocus />
            <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={saveEdit}><Check className="h-3.5 w-3.5" /></Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={cancelEdit}><X className="h-3.5 w-3.5" /></Button>
          </div>
        ) : (
          <button
            onClick={() => startEdit("nome", plan.nome)}
            className="flex items-center gap-1.5 min-w-0 group/name"
          >
            <span className="text-sm font-bold tracking-tight truncate max-w-[200px] lg:max-w-[280px]">{plan.nome}</span>
            <Pencil className="h-3 w-3 text-muted-foreground/30 group-hover/name:text-muted-foreground/60 transition-opacity shrink-0" />
          </button>
        )}

        {/* Separator */}
        <div className="h-4 w-px bg-border shrink-0 hidden sm:block" />

        {/* Center: client + metadata */}
        <div className="hidden sm:flex items-center gap-1.5 min-w-0">
          <Select value={plan.id_cliente ? String(plan.id_cliente) : "__none__"} onValueChange={(v) => onUpdatePlan({ id_cliente: v === "__none__" ? null : Number(v) })}>
            <SelectTrigger size="sm" className="h-7 w-[140px] text-xs border-0 bg-muted/50 hover:bg-muted transition-colors">
              <SelectValue placeholder="Cliente" />
            </SelectTrigger>
            <SelectContent position="popper" sideOffset={4}>
              <SelectItem value="__none__">Nessun cliente</SelectItem>
              {clients.map((c) => (<SelectItem key={c.id} value={String(c.id)}>{c.nome} {c.cognome}</SelectItem>))}
            </SelectContent>
          </Select>

          <Select value={plan.obiettivo} onValueChange={(v) => onUpdatePlan({ obiettivo: v })}>
            <SelectTrigger className="h-7 w-auto text-[11px] border-0 bg-transparent px-1.5 font-medium hover:bg-muted/50 rounded transition-colors">
              <Badge variant="outline" className="text-[10px] cursor-pointer px-1.5 py-0">{OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}</Badge>
            </SelectTrigger>
            <SelectContent>{OBIETTIVI_SCHEDA.map((o) => (<SelectItem key={o} value={o}>{OBIETTIVO_LABELS[o]}</SelectItem>))}</SelectContent>
          </Select>

          <Select value={plan.livello} onValueChange={(v) => onUpdatePlan({ livello: v })}>
            <SelectTrigger className="h-7 w-auto text-[11px] border-0 bg-transparent px-1.5 font-medium hover:bg-muted/50 rounded transition-colors">
              <Badge variant="outline" className="text-[10px] cursor-pointer px-1.5 py-0">{LIVELLO_LABELS[plan.livello] ?? plan.livello}</Badge>
            </SelectTrigger>
            <SelectContent>{LIVELLI_SCHEDA.map((l) => (<SelectItem key={l} value={l}>{LIVELLO_LABELS[l]}</SelectItem>))}</SelectContent>
          </Select>

          {totalVolume != null && (
            <span className="text-[10px] font-medium tabular-nums text-muted-foreground/60 tracking-tight hidden lg:inline">
              {totalVolume.toLocaleString("it-IT")} kg
            </span>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right: status + actions */}
        {!isDirty && lastSavedLabel && (
          <span className="hidden lg:inline text-[10px] text-muted-foreground/50 font-medium tabular-nums">
            {lastSavedLabel}
          </span>
        )}

        {hasSessions && (
          <Button variant={showAdvanced ? "default" : "ghost"} size="icon" className="h-7 w-7" onClick={onToggleAdvanced} title={showAdvanced ? "Nascondi analisi" : "Mostra analisi"}>
            <FlaskConical className="h-3.5 w-3.5" />
          </Button>
        )}

        <ExportButtons nome={plan.nome} obiettivo={plan.obiettivo} livello={plan.livello} clientNome={clientNome} durata_settimane={plan.durata_settimane} sessioni_per_settimana={plan.sessioni_per_settimana} sessioni={sessions} safety={safetyExportData} logoDataUrl={exportLogoDataUrl} onLogoChange={onLogoChange} />

        {isDirty && (
          <Button size="sm" className="h-7 text-xs gap-1" onClick={onSave} disabled={isSaving}>
            <Save className="h-3.5 w-3.5" />{isSaving ? "..." : "Salva"}
          </Button>
        )}
      </div>

      {/* ── Row 2 mobile only: client + metadata ── */}
      <div className="flex items-center gap-1.5 px-3 pb-2 sm:hidden overflow-x-auto">
        <Select value={plan.id_cliente ? String(plan.id_cliente) : "__none__"} onValueChange={(v) => onUpdatePlan({ id_cliente: v === "__none__" ? null : Number(v) })}>
          <SelectTrigger size="sm" className="h-7 w-[140px] text-xs shrink-0"><SelectValue placeholder="Cliente" /></SelectTrigger>
          <SelectContent position="popper" sideOffset={4}>
            <SelectItem value="__none__">Nessun cliente</SelectItem>
            {clients.map((c) => (<SelectItem key={c.id} value={String(c.id)}>{c.nome} {c.cognome}</SelectItem>))}
          </SelectContent>
        </Select>
        <Badge variant="outline" className="text-[10px] shrink-0">{OBIETTIVO_LABELS[plan.obiettivo] ?? plan.obiettivo}</Badge>
        <Badge variant="outline" className="text-[10px] shrink-0">{LIVELLO_LABELS[plan.livello] ?? plan.livello}</Badge>
      </div>
    </div>
  );
}
