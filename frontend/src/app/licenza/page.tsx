"use client"

import { Suspense, useCallback, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { ShieldAlert, Mail, ArrowLeft, Copy, Check, Monitor, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getStoredTrainer, type StoredTrainer } from "@/lib/auth"

const STATUS_CONFIG: Record<string, { label: string; description: string; color: string }> = {
  missing: {
    label: "Non trovata",
    description: "Nessun file di licenza presente. Invia la richiesta di attivazione al supporto.",
    color: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  },
  expired: {
    label: "Scaduta",
    description: "La tua licenza e' scaduta. Contatta il supporto per rinnovarla.",
    color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
  invalid: {
    label: "Non valida",
    description: "Il file di licenza non e' valido. Potrebbe essere corrotto o non autorizzato.",
    color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
  unconfigured: {
    label: "Non configurata",
    description: "Il sistema di licenza non e' ancora configurato. Contatta il supporto.",
    color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
  },
  wrong_machine: {
    label: "Computer non autorizzato",
    description: "Questa licenza e' associata a un altro computer. Contatta il supporto per trasferirla.",
    color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  },
}

const DEFAULT_CONFIG = {
  label: "Problema licenza",
  description: "Si e' verificato un problema con la licenza. Contatta il supporto.",
  color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
}

function formatMachineIdDisplay(id: string): string {
  if (id === "unavailable" || id.length < 4) return id
  return id
    .split("")
    .reduce<string[]>((acc, char, i) => {
      if (i > 0 && i % 4 === 0) acc.push(" ")
      acc.push(char)
      return acc
    }, [])
    .join("")
}

function buildActivationText(
  trainer: StoredTrainer | null,
  machineId: string | null,
  machineIdFull: string | null,
): string {
  const lines: string[] = ["--- Richiesta Attivazione FitManager ---", ""]
  if (trainer) {
    lines.push(`Nome: ${trainer.nome} ${trainer.cognome}`)
    lines.push(`Email: ${trainer.email}`)
  }
  if (machineIdFull) {
    lines.push(`Codice Macchina: ${machineIdFull}`)
  } else if (machineId) {
    lines.push(`Codice Macchina: ${machineId}`)
  }
  return lines.join("\n")
}

function ActivationCard({
  trainer,
  machineId,
  machineIdFull,
}: {
  trainer: StoredTrainer | null
  machineId: string | null
  machineIdFull: string | null
}) {
  const [copied, setCopied] = useState(false)

  const activationText = buildActivationText(trainer, machineId, machineIdFull)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(activationText).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [activationText])

  const hasData = trainer || (machineId && machineId !== "unavailable")
  if (!hasData) return null

  return (
    <div className="rounded-lg border-2 border-teal-200 bg-teal-50 p-4 dark:border-teal-800 dark:bg-teal-950/40">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-teal-800 dark:text-teal-300">
          <Monitor className="h-4 w-4" />
          Dati per l&apos;attivazione
        </div>
        <Button variant="outline" size="sm" onClick={handleCopy} className="shrink-0">
          {copied ? (
            <Check className="mr-1.5 h-3.5 w-3.5 text-emerald-600" />
          ) : (
            <Copy className="mr-1.5 h-3.5 w-3.5" />
          )}
          {copied ? "Copiato!" : "Copia tutto"}
        </Button>
      </div>

      <div className="space-y-2">
        {trainer ? (
          <div className="flex items-start gap-2">
            <User className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600 dark:text-teal-400" />
            <div className="text-sm">
              <p className="font-medium text-teal-900 dark:text-teal-100">
                {trainer.nome} {trainer.cognome}
              </p>
              <p className="text-teal-700 dark:text-teal-400">{trainer.email}</p>
            </div>
          </div>
        ) : null}

        {machineId && machineId !== "unavailable" ? (
          <div className="flex items-start gap-2">
            <Monitor className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600 dark:text-teal-400" />
            <div className="text-sm">
              <p className="text-xs uppercase tracking-wide text-teal-600 dark:text-teal-500">
                Codice Macchina
              </p>
              <code className="text-base font-bold tracking-wider text-teal-900 dark:text-teal-100">
                {formatMachineIdDisplay(machineId)}
              </code>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

function LicenzaContent() {
  const searchParams = useSearchParams()
  const status = searchParams.get("status") ?? "missing"
  const config = STATUS_CONFIG[status] ?? DEFAULT_CONFIG

  const [machineId, setMachineId] = useState<string | null>(null)
  const [machineIdFull, setMachineIdFull] = useState<string | null>(null)
  const [trainer, setTrainer] = useState<StoredTrainer | null>(null)

  useEffect(() => {
    setTrainer(getStoredTrainer())
  }, [])

  useEffect(() => {
    fetch("/health", { signal: AbortSignal.timeout(5000) })
      .then((res) => res.json())
      .then((data) => {
        if (data.machine_id) setMachineId(data.machine_id)
        if (data.machine_id_full) setMachineIdFull(data.machine_id_full)
      })
      .catch(() => {})
  }, [])

  const activationText = buildActivationText(trainer, machineId, machineIdFull)

  return (
    <Card className="w-full max-w-md shadow-xl">
      <CardHeader className="text-center">
        <div className="bg-primary/10 mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full">
          <ShieldAlert className="text-primary h-8 w-8" />
        </div>
        <CardTitle className="text-2xl">Licenza FitManager</CardTitle>
        <Badge className={`mx-auto mt-2 ${config.color}`}>{config.label}</Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-muted-foreground text-center text-sm">{config.description}</p>

        <ActivationCard trainer={trainer} machineId={machineId} machineIdFull={machineIdFull} />

        <div className="bg-muted rounded-lg p-4">
          <h3 className="mb-2 text-sm font-medium">Come attivare</h3>
          <ol className="text-muted-foreground list-inside list-decimal space-y-1 text-sm">
            <li>Copia i dati qui sopra o clicca &quot;Richiedi licenza&quot;</li>
            <li>Riceverai un file <code>license.key</code> per questo computer</li>
            <li>Copia il file nella cartella <code>data</code> dell&apos;applicazione</li>
            <li>Riavvia FitManager</li>
          </ol>
        </div>

        <div className="flex flex-col gap-2">
          <Button
            className="w-full"
            onClick={() => {
              const subject = encodeURIComponent("Richiesta Attivazione FitManager")
              const body = encodeURIComponent(activationText)
              window.location.href = `mailto:supporto@fitmanager.it?subject=${subject}&body=${body}`
            }}
          >
            <Mail className="mr-2 h-4 w-4" />
            Richiedi licenza
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              window.location.href = "/login"
            }}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Torna al login
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function LicenzaPage() {
  return (
    <div className="bg-mesh-login flex min-h-screen items-center justify-center p-4">
      <Suspense>
        <LicenzaContent />
      </Suspense>
    </div>
  )
}
