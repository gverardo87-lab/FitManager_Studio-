// src/app/(dashboard)/impostazioni/page.tsx
"use client";

/**
 * Pagina Impostazioni — organizzata in 2 tab.
 *
 * Tab Sistema: stato installazione, connettivita', snapshot diagnostico
 * Tab Dati: backup/restore, saldo iniziale, export GDPR
 */

import { useRef, useState } from "react";
import { usePageReveal } from "@/lib/page-reveal";
import {
  Settings,
  Database,
  Download,
  Upload,
  FileJson,
  HardDrive,
  RefreshCw,
  AlertTriangle,
  Wallet,
  CalendarIcon,
  Save,
  ShieldCheck,
  CheckCircle2,
  Monitor,
  HardDriveDownload,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ConnectivityStatusSection } from "@/components/settings/ConnectivityStatusSection";
import { SupportSnapshotSection } from "@/components/settings/SupportSnapshotSection";
import { SystemStatusSection } from "@/components/settings/SystemStatusSection";

import {
  useBackups,
  useCreateBackup,
  useRestoreBackup,
  useVerifyBackup,
  downloadBackup,
  exportTrainerData,
} from "@/hooks/useBackup";
import { useSaldoIniziale, useUpdateSaldoIniziale } from "@/hooks/useMovements";
import { formatDateTime, formatCurrency } from "@/lib/format";

// ── Helpers ──

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

// ── Page ──

export default function ImpostazioniPage() {
  const { revealClass, revealStyle } = usePageReveal();

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div data-guide="impostazioni-header" className={revealClass(0, "flex items-center gap-3")} style={revealStyle(0)}>
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-900/40 dark:to-slate-800/30">
          <Settings className="h-5 w-5 text-slate-600 dark:text-slate-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Impostazioni</h1>
          <p className="text-sm text-muted-foreground">
            Sistema, backup e configurazione
          </p>
        </div>
      </div>

      {/* ── Tabs ── */}
      <Tabs defaultValue="sistema" className={revealClass(30)} style={revealStyle(30)}>
        <TabsList className="w-full overflow-x-auto">
          <TabsTrigger value="sistema" className="gap-1.5">
            <Monitor className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sistema</span>
          </TabsTrigger>
          <TabsTrigger value="dati" className="gap-1.5">
            <HardDriveDownload className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Dati</span>
          </TabsTrigger>
        </TabsList>

        {/* ════ Tab Sistema ════ */}
        <TabsContent value="sistema" className="mt-4 space-y-6">
          <SystemStatusSection />
          <div id="connettivita" className="scroll-mt-24">
            <ConnectivityStatusSection />
          </div>
          <SupportSnapshotSection />
        </TabsContent>

        {/* ════ Tab Dati ════ */}
        <TabsContent value="dati" className="mt-4 space-y-6">
          <SaldoInizialeSection />
          <BackupSection />
          <ExportSection />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// Backup Database
// ════════════════════════════════════════════════════════════

function BackupSection() {
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [restoreFilename, setRestoreFilename] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: backups, isLoading, isError, refetch } = useBackups();
  const createBackup = useCreateBackup();
  const restoreBackup = useRestoreBackup();
  const verifyBackup = useVerifyBackup();

  const handleRestoreFromList = (filename: string) => {
    setRestoreFilename(filename);
    setRestoreDialogOpen(true);
  };

  const confirmRestoreFromList = async () => {
    if (!restoreFilename) return;
    setRestoreDialogOpen(false);
    const { data } = await (await import("@/lib/api-client")).default.get(
      `/backup/download/${restoreFilename}`,
      { responseType: "blob" }
    );
    const file = new File([data as Blob], restoreFilename, {
      type: "application/x-sqlite3",
    });
    restoreBackup.mutate(file);
  };

  const handleRestoreFromFile = () => {
    fileInputRef.current?.click();
  };

  const onFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    restoreBackup.mutate(file);
    e.target.value = "";
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              <div>
                <CardTitle>Backup Database</CardTitle>
                <CardDescription>
                  Crea copie di sicurezza e ripristina da backup precedenti
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRestoreFromFile}
                disabled={restoreBackup.isPending}
              >
                <Upload className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Carica Backup</span>
              </Button>
              <Button
                size="sm"
                onClick={() => createBackup.mutate()}
                disabled={createBackup.isPending}
              >
                <HardDrive className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">
                  {createBackup.isPending ? "Creazione..." : "Crea Backup"}
                </span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <input
            ref={fileInputRef}
            type="file"
            accept=".sqlite,.db"
            className="hidden"
            onChange={onFileSelected}
          />

          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : null}

          {isError ? (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
              <p className="text-destructive">Errore nel caricamento dei backup.</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
                Riprova
              </Button>
            </div>
          ) : null}

          {backups && backups.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <Database className="mx-auto mb-3 h-10 w-10 opacity-30" />
              <p>Nessun backup disponibile</p>
              <p className="text-sm">Clicca &quot;Crea Backup&quot; per creare il primo</p>
            </div>
          ) : null}

          {backups && backups.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>File</TableHead>
                    <TableHead className="hidden sm:table-cell">Dimensione</TableHead>
                    <TableHead className="hidden sm:table-cell">Data</TableHead>
                    <TableHead className="hidden md:table-cell">Checksum</TableHead>
                    <TableHead className="text-right">Azioni</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backups.map((backup) => (
                    <TableRow key={backup.filename} className="transition-colors hover:bg-muted/50">
                      <TableCell className="max-w-[180px] truncate font-mono text-sm">
                        {backup.filename}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">{formatBytes(backup.size_bytes)}</TableCell>
                      <TableCell className="hidden sm:table-cell">{formatDateTime(backup.created_at)}</TableCell>
                      <TableCell className="hidden md:table-cell">
                        {backup.checksum ? (
                          <span className="inline-flex items-center gap-1 font-mono text-xs text-emerald-600 dark:text-emerald-400">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            {backup.checksum.slice(0, 12)}...
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => verifyBackup.mutate(backup.filename)} disabled={verifyBackup.isPending} title="Verifica integrita'">
                            <ShieldCheck className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => downloadBackup(backup.filename)} title="Scarica">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleRestoreFromList(backup.filename)} disabled={restoreBackup.isPending} title="Ripristina">
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* Dialog conferma restore */}
      <AlertDialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Ripristinare il backup?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Il database corrente verra&apos; sovrascritto con{" "}
              <span className="font-mono font-medium">{restoreFilename}</span>.
              <br />
              Un backup di sicurezza verra&apos; creato automaticamente prima del ripristino.
              <br />
              <strong>Dopo il ripristino sara&apos; necessario riavviare il server.</strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={confirmRestoreFromList}>
              Ripristina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// ════════════════════════════════════════════════════════════
// Export Dati
// ════════════════════════════════════════════════════════════

function ExportSection() {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <FileJson className="h-5 w-5 text-green-600" />
            <div>
              <CardTitle>Export Dati</CardTitle>
              <CardDescription>
                Scarica tutti i tuoi dati in formato JSON (GDPR / portabilita&apos;)
              </CardDescription>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={exportTrainerData}>
            <Download className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">Esporta JSON</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          L&apos;export include tutti i tuoi dati: clienti, contratti, rate, eventi, movimenti,
          spese ricorrenti, schede allenamento, misurazioni, obiettivi e audit log.
          I record eliminati non vengono inclusi.
        </p>
      </CardContent>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════
// Saldo Iniziale di Cassa
// ════════════════════════════════════════════════════════════

function SaldoInizialeSection() {
  const { data: saldoData, isLoading } = useSaldoIniziale();
  const updateSaldo = useUpdateSaldoIniziale();

  const [draft, setDraft] = useState<{ importo: string; dataInizio: string } | null>(null);
  const importo = draft?.importo ?? (saldoData ? String(saldoData.saldo_iniziale_cassa) : "");
  const dataInizio = draft?.dataInizio ?? (saldoData?.data_saldo_iniziale ?? "");

  const setImportoDraft = (nextImporto: string) => {
    setDraft((prev) => ({
      importo: nextImporto,
      dataInizio: prev?.dataInizio ?? (saldoData?.data_saldo_iniziale ?? ""),
    }));
  };

  const setDataInizioDraft = (nextDataInizio: string) => {
    setDraft((prev) => ({
      importo: prev?.importo ?? (saldoData ? String(saldoData.saldo_iniziale_cassa) : ""),
      dataInizio: nextDataInizio,
    }));
  };

  const handleSave = () => {
    const parsed = parseFloat(importo);
    if (isNaN(parsed)) return;
    updateSaldo.mutate(
      {
        saldo_iniziale_cassa: parsed,
        data_saldo_iniziale: dataInizio || null,
      },
      { onSuccess: () => setDraft(null) },
    );
  };

  const isDirty =
    saldoData != null &&
    (String(saldoData.saldo_iniziale_cassa) !== importo ||
      (saldoData.data_saldo_iniziale ?? "") !== dataInizio);

  if (isLoading) {
    return (
      <Card>
        <CardHeader><Skeleton className="h-6 w-48" /><Skeleton className="h-4 w-72" /></CardHeader>
        <CardContent><Skeleton className="h-10 w-full" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Wallet className="h-5 w-5 text-teal-600" />
          <div>
            <CardTitle>Saldo Iniziale di Cassa</CardTitle>
            <CardDescription>
              Saldo del conto all&apos;inizio dell&apos;utilizzo. Tutti i calcoli partono da qui.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="saldo-iniziale">Importo (&euro;)</Label>
            <Input
              id="saldo-iniziale"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={importo}
              onChange={(e) => setImportoDraft(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="data-saldo">Data di riferimento (opzionale)</Label>
            <div className="relative">
              <CalendarIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="data-saldo"
                type="date"
                value={dataInizio}
                onChange={(e) => setDataInizioDraft(e.target.value)}
                className="pl-10"
              />
            </div>
            <p className="text-[11px] text-muted-foreground">
              Se impostata, solo i movimenti da questa data in poi verranno conteggiati
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <Button onClick={handleSave} disabled={updateSaldo.isPending || !isDirty} size="sm">
            <Save className="mr-2 h-4 w-4" />
            {updateSaldo.isPending ? "Salvataggio..." : "Salva"}
          </Button>
          {saldoData && saldoData.saldo_iniziale_cassa !== 0 ? (
            <p className="text-xs text-muted-foreground">
              Valore attuale: <span className="font-semibold tabular-nums">{formatCurrency(saldoData.saldo_iniziale_cassa)}</span>
              {saldoData.data_saldo_iniziale ? (
                <> dal {new Date(saldoData.data_saldo_iniziale + "T00:00:00").toLocaleDateString("it-IT")}</>
              ) : null}
            </p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
