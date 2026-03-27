// src/components/workouts/ExportButtons.tsx
"use client";

/**
 * Bottoni export: scarica clinico + anteprima + gestione logo cliente.
 *
 * Clinico: scarica file HTML locale (stile ex-Excel, con fotografie esercizi).
 * Anteprima: usa la WorkoutPreview stampabile attuale.
 * Il logo viene salvato dal parent e riutilizzato in preview/export.
 */

import { useRef, useState, type ChangeEvent } from "react";
import { Download, ImagePlus, Loader2, Printer, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { buildWhatsAppUrl } from "@/lib/format";
import { downloadWorkoutClinicalPdf, type SafetyExportData } from "@/lib/export-workout-pdf";
import { useTrainerName } from "@/hooks/useTrainerName";
import { waWorkoutShare } from "@/lib/whatsapp-templates";
import type { SessionCardData } from "./SessionCard";

const MAX_LOGO_SIZE_MB = 2;
const MAX_LOGO_SIZE_BYTES = MAX_LOGO_SIZE_MB * 1024 * 1024;

interface ExportButtonsProps {
  nome: string;
  obiettivo: string;
  livello: string;
  clientNome?: string;
  clientTelefono?: string | null;
  durata_settimane?: number;
  sessioni_per_settimana?: number;
  sessioni: SessionCardData[];
  safety?: SafetyExportData;
  logoDataUrl?: string | null;
  onLogoChange?: (value: string | null) => void;
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export function ExportButtons({
  nome,
  obiettivo,
  livello,
  clientNome,
  clientTelefono,
  durata_settimane,
  sessioni_per_settimana,
  sessioni,
  safety,
  logoDataUrl,
  onLogoChange,
}: ExportButtonsProps) {
  const trainerName = useTrainerName();
  const [exportingClinical, setExportingClinical] = useState(false);
  const [sendingWa, setSendingWa] = useState(false);
  const [exportingPreview, setExportingPreview] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const exportData = { nome, obiettivo, livello, clientNome, durata_settimane, sessioni_per_settimana, sessioni, safety, logoDataUrl };

  const handleClinicalPdf = async () => {
    setExportingClinical(true);
    try {
      await downloadWorkoutClinicalPdf(exportData);
    } finally {
      setExportingClinical(false);
    }
  };

  /** Salva PDF (via print) + apre WhatsApp con messaggio pre-compilato. */
  const handleSendWa = async () => {
    if (!clientTelefono || !clientNome) return;
    setSendingWa(true);
    try {
      // Prima apre la finestra di stampa per salvare il PDF
      await downloadWorkoutClinicalPdf(exportData);
      // Poi apre WhatsApp con messaggio pre-compilato
      const msg = waWorkoutShare(clientNome.split(" ")[0], trainerName, nome);
      const url = buildWhatsAppUrl(clientTelefono, msg);
      if (url) {
        // Piccolo delay per evitare conflitto popup blocker (2 finestre in sequenza)
        setTimeout(() => {
          window.open(url, "_blank", "noopener,noreferrer");
        }, 1500);
      }
    } finally {
      setSendingWa(false);
    }
  };

  const handlePreviewPdf = () => {
    setExportingPreview(true);
    try {
      window.print();
    } finally {
      setExportingPreview(false);
    }
  };

  const handlePickLogo = () => {
    inputRef.current?.click();
  };

  const handleLogoSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Seleziona un file immagine valido (PNG, JPG, WEBP, SVG).");
      return;
    }
    if (file.size > MAX_LOGO_SIZE_BYTES) {
      toast.error(`Logo troppo pesante (max ${MAX_LOGO_SIZE_MB} MB).`);
      return;
    }

    setUploadingLogo(true);
    try {
      const dataUrl = await fileToDataUrl(file);
      onLogoChange?.(dataUrl);
      toast.success("Logo aggiornato per l'export PDF.");
    } catch {
      toast.error("Impossibile leggere il file logo.");
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleRemoveLogo = () => {
    onLogoChange?.(null);
    toast.success("Logo rimosso.");
  };

  return (
    <div className="flex gap-2" data-print-hide>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/svg+xml"
        className="hidden"
        onChange={handleLogoSelected}
      />

      <Button variant="outline" size="sm" onClick={handleClinicalPdf} disabled={exportingClinical}>
        {exportingClinical ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Download className="mr-1.5 h-4 w-4" />
        )}
        Scarica Clinico
      </Button>

      <Button variant="outline" size="sm" onClick={handlePreviewPdf} disabled={exportingPreview}>
        {exportingPreview ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Printer className="mr-1.5 h-4 w-4" />
        )}
        Anteprima
      </Button>

      <Button variant="outline" size="sm" onClick={handlePickLogo} disabled={uploadingLogo}>
        {uploadingLogo ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <ImagePlus className="mr-1.5 h-4 w-4" />
        )}
        {logoDataUrl ? "Cambia logo" : "Logo"}
      </Button>

      {logoDataUrl && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={handleRemoveLogo}
          title="Rimuovi logo"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )}

      {clientTelefono && clientNome ? (
        <Button
          variant="outline"
          size="sm"
          onClick={handleSendWa}
          disabled={sendingWa}
          className="gap-1.5 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 border-emerald-200 dark:text-emerald-400 dark:hover:bg-emerald-950/30 dark:border-emerald-800"
        >
          {sendingWa ? (
            <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
          ) : (
            <svg role="img" aria-label="WhatsApp" viewBox="0 0 24 24" fill="currentColor" className="mr-1 h-3.5 w-3.5">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
            </svg>
          )}
          Invia PDF
        </Button>
      ) : null}
    </div>
  );
}
