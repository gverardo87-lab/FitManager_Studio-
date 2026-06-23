// src/components/contracts/ContractForm.tsx
"use client";

/**
 * Form contratto — creazione e modifica.
 *
 * Sfide relazionali risolte:
 * - id_cliente: Select popolato da useClients() → nome visibile, id inviato
 * - Date: DatePicker (Popover + Calendar) con formattazione italiana
 * - Acconto: campo condizionale, visibile solo in creazione
 * - Metodo acconto: appare solo quando acconto > 0 (allineato al backend)
 */

import { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format, parseISO, addDays, differenceInDays, startOfDay } from "date-fns";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DatePicker } from "@/components/ui/date-picker";
import { useClients } from "@/hooks/useClients";
import type { Contract } from "@/types/api";
import { PAYMENT_METHODS } from "@/types/api";

// ── Zod schema (allineato a api/schemas/financial.py ContractCreate) ──

const contractSchema = z
  .object({
    id_cliente: z.number({ error: "Seleziona un cliente" }).gt(0),
    tipo_pacchetto: z.string().min(1, "Tipo pacchetto obbligatorio").max(100),
    crediti_totali: z.number().int().min(1, "Minimo 1 credito").max(1000),
    prezzo_totale: z.number().min(0).max(1_000_000),
    data_inizio: z.date({ error: "Data inizio obbligatoria" }),
    // Scadenza opzionale: i carnet a crediti senza termine sono un'offerta reale (FDM §2).
    // La checkbox "Senza scadenza" governa la presenza del campo.
    data_scadenza: z.date().optional(),
    senza_scadenza: z.boolean().optional(),
    acconto: z.number().min(0).max(1_000_000).optional(),
    metodo_acconto: z.string().optional(),
    note: z.string().max(500).optional(),
  })
  .refine((data) => data.senza_scadenza === true || !!data.data_scadenza, {
    message: "Indica una scadenza o seleziona 'Senza scadenza'",
    path: ["data_scadenza"],
  })
  .refine(
    (data) => !data.data_scadenza || data.data_scadenza > data.data_inizio,
    {
      message: "La scadenza deve essere dopo la data inizio",
      path: ["data_scadenza"],
    },
  )
  .refine(
    (data) => !data.acconto || data.acconto <= data.prezzo_totale,
    {
      message: "L'acconto non puo' superare il prezzo totale",
      path: ["acconto"],
    }
  )
  .refine(
    (data) => !data.acconto || data.acconto === 0 || data.metodo_acconto,
    {
      message: "Metodo pagamento obbligatorio con acconto",
      path: ["metodo_acconto"],
    }
  );

export type ContractFormValues = z.infer<typeof contractSchema>;

/** Payload effettivo dopo conversione Date → string ISO (pronto per API). */
export interface ContractSubmitPayload {
  id_cliente: number;
  tipo_pacchetto: string;
  crediti_totali: number;
  prezzo_totale: number;
  data_inizio: string;
  data_scadenza: string | null; // null = carnet senza scadenza (FDM §2)
  acconto?: number;
  metodo_acconto?: string;
  note?: string;
}

/** Pre-fill values for renewal (new contract with defaults from expiring one). */
export interface RenewalDefaults {
  id_cliente: number;
  tipo_pacchetto: string;
  crediti_totali: number;
  prezzo_totale: number;
  /** Date del contratto-padre: usate solo per derivare la durata del rinnovo (§A.2). */
  data_inizio?: string | null;
  data_scadenza?: string | null;
}

interface ContractFormProps {
  contract?: Contract | null;
  defaultClientId?: number;
  renewalDefaults?: RenewalDefaults;
  onSubmit: (values: ContractSubmitPayload) => void;
  isPending: boolean;
  onDirtyChange?: (dirty: boolean) => void;
}

export function ContractForm({
  contract,
  defaultClientId,
  renewalDefaults,
  onSubmit,
  isPending,
  onDirtyChange,
}: ContractFormProps) {
  const isEdit = !!contract;
  const isRenewal = !!renewalDefaults;
  const { data: clientsData } = useClients();

  // Rinnovo = continuazione sequenziale del padre (§A.2 — derivata, modificabile):
  // - il figlio parte il giorno DOPO la scadenza del padre (continuita', non parallelo);
  // - se il padre e' gia' scaduto (rinnovo tardivo) parte da oggi, mai nel passato → max(scadenza+1, oggi);
  // - dura quanto il padre (stesso numero di giorni).
  let renewalStart: Date | undefined;
  let renewalEnd: Date | undefined;
  if (isRenewal) {
    const today = startOfDay(new Date());
    const parentStart = renewalDefaults?.data_inizio ? parseISO(renewalDefaults.data_inizio) : undefined;
    const parentEnd = renewalDefaults?.data_scadenza ? parseISO(renewalDefaults.data_scadenza) : undefined;
    const dayAfterParent = parentEnd ? addDays(parentEnd, 1) : undefined;
    renewalStart = dayAfterParent && dayAfterParent > today ? dayAfterParent : today;
    if (parentStart && parentEnd) {
      const durationDays = differenceInDays(parentEnd, parentStart);
      if (durationDays > 0) renewalEnd = addDays(renewalStart, durationDays);
    }
  }

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<ContractFormValues>({
    resolver: zodResolver(contractSchema),
    defaultValues: {
      id_cliente: contract?.id_cliente ?? renewalDefaults?.id_cliente ?? defaultClientId ?? undefined,
      tipo_pacchetto: contract?.tipo_pacchetto ?? renewalDefaults?.tipo_pacchetto ?? "",
      crediti_totali: contract?.crediti_totali ?? renewalDefaults?.crediti_totali ?? 10,
      prezzo_totale: contract?.prezzo_totale ?? renewalDefaults?.prezzo_totale ?? 0,
      data_inizio: contract?.data_inizio
        ? parseISO(contract.data_inizio)
        : renewalStart,
      data_scadenza: contract?.data_scadenza
        ? parseISO(contract.data_scadenza)
        : renewalEnd,
      // Un contratto già senza scadenza (edit) o il rinnovo di un carnet (padre senza
      // scadenza) pre-selezionano la checkbox.
      senza_scadenza: isEdit
        ? !contract?.data_scadenza
        : isRenewal
          ? !renewalDefaults?.data_scadenza
          : false,
      acconto: 0,
      metodo_acconto: undefined,
      note: contract?.note ?? "",
    },
  });

  useEffect(() => { onDirtyChange?.(isDirty); }, [isDirty, onDirtyChange]);

  const accontoValue = watch("acconto") ?? 0;
  const senzaScadenza = watch("senza_scadenza") ?? false;

  const handleFormSubmit = (values: ContractFormValues) => {
    // Converti Date in string ISO per il backend. "Senza scadenza" → null (carnet, FDM §2).
    const payload: ContractSubmitPayload = {
      id_cliente: values.id_cliente,
      tipo_pacchetto: values.tipo_pacchetto,
      crediti_totali: values.crediti_totali,
      prezzo_totale: values.prezzo_totale,
      data_inizio: format(values.data_inizio, "yyyy-MM-dd"),
      data_scadenza:
        values.senza_scadenza || !values.data_scadenza
          ? null
          : format(values.data_scadenza, "yyyy-MM-dd"),
      note: values.note || undefined,
      acconto: values.acconto || 0,
      metodo_acconto: values.metodo_acconto || undefined,
    };
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      {/* ── Cliente (Select relazionale) ── */}
      <div className="space-y-2">
        <Label>Cliente *</Label>
        <Controller
          control={control}
          name="id_cliente"
          render={({ field }) => (
            <Select
              value={field.value?.toString() ?? ""}
              onValueChange={(v) => field.onChange(parseInt(v, 10))}
              disabled={isEdit || isRenewal}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleziona cliente..." />
              </SelectTrigger>
              <SelectContent>
                {clientsData?.items.map((client) => (
                  <SelectItem key={client.id} value={client.id.toString()}>
                    {client.cognome} {client.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        {errors.id_cliente && (
          <p className="text-sm text-destructive">
            {errors.id_cliente.message}
          </p>
        )}
      </div>

      {/* ── Tipo Pacchetto / Crediti ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="tipo_pacchetto">Tipo Pacchetto *</Label>
          <Input id="tipo_pacchetto" {...register("tipo_pacchetto")} />
          {errors.tipo_pacchetto && (
            <p className="text-sm text-destructive">
              {errors.tipo_pacchetto.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="crediti_totali">Crediti *</Label>
          <Input
            id="crediti_totali"
            type="number"
            {...register("crediti_totali", { valueAsNumber: true })}
          />
          {errors.crediti_totali && (
            <p className="text-sm text-destructive">
              {errors.crediti_totali.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Prezzo Totale ── */}
      <div className="space-y-2">
        <Label htmlFor="prezzo_totale">Prezzo Totale (EUR) *</Label>
        <Input
          id="prezzo_totale"
          type="number"
          step="0.01"
          {...register("prezzo_totale", { valueAsNumber: true })}
        />
        {errors.prezzo_totale && (
          <p className="text-sm text-destructive">
            {errors.prezzo_totale.message}
          </p>
        )}
      </div>

      {/* ── Date ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Data Inizio *</Label>
          <Controller
            control={control}
            name="data_inizio"
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                placeholder="Inizio..."
              />
            )}
          />
          {errors.data_inizio && (
            <p className="text-sm text-destructive">
              {errors.data_inizio.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label>Data Scadenza {senzaScadenza ? "" : "*"}</Label>
          <Controller
            control={control}
            name="data_scadenza"
            render={({ field }) => (
              <DatePicker
                value={field.value}
                onChange={field.onChange}
                placeholder="Scadenza..."
                disabled={senzaScadenza}
              />
            )}
          />
          <div className="flex items-center gap-2 pt-1">
            <Controller
              control={control}
              name="senza_scadenza"
              render={({ field }) => (
                <Checkbox
                  id="senza_scadenza"
                  checked={field.value ?? false}
                  onCheckedChange={(checked) => {
                    const on = checked === true;
                    field.onChange(on);
                    // Azzera la data quando si passa a "senza scadenza" (carnet a crediti).
                    if (on) setValue("data_scadenza", undefined, { shouldValidate: true });
                  }}
                />
              )}
            />
            <Label htmlFor="senza_scadenza" className="text-sm font-normal text-muted-foreground">
              Senza scadenza (pacchetto a crediti)
            </Label>
          </div>
          {errors.data_scadenza && (
            <p className="text-sm text-destructive">
              {errors.data_scadenza.message}
            </p>
          )}
        </div>
      </div>

      {/* ── Acconto (solo in creazione) ── */}
      {!isEdit && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="acconto">Acconto (EUR)</Label>
              <Input
                id="acconto"
                type="number"
                step="0.01"
                {...register("acconto", { valueAsNumber: true })}
              />
              {errors.acconto && (
                <p className="text-sm text-destructive">
                  {errors.acconto.message}
                </p>
              )}
            </div>
            {accontoValue > 0 && (
              <div className="space-y-2">
                <Label>Metodo Pagamento</Label>
                <Select
                  value={watch("metodo_acconto") ?? ""}
                  onValueChange={(v) =>
                    setValue("metodo_acconto", v, { shouldValidate: true })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Metodo..." />
                  </SelectTrigger>
                  <SelectContent>
                    {PAYMENT_METHODS.map((m) => (
                      <SelectItem key={m} value={m}>
                        {m}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.metodo_acconto && (
                  <p className="text-sm text-destructive">
                    {errors.metodo_acconto.message}
                  </p>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Note ── */}
      <div className="space-y-2">
        <Label htmlFor="note">Note</Label>
        <Input id="note" {...register("note")} />
        {errors.note && (
          <p className="text-sm text-destructive">{errors.note.message}</p>
        )}
      </div>

      {/* ── Submit ── */}
      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isEdit ? "Salva Modifiche" : isRenewal ? "Rinnova Contratto" : "Crea Contratto"}
      </Button>
    </form>
  );
}
