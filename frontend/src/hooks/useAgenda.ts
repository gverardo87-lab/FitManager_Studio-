// src/hooks/useAgenda.ts
/**
 * Custom hooks per il modulo Agenda.
 *
 * - useEvents({ start, end }): lista eventi con date idratate (Date objects)
 * - useCreateEvent(): crea evento (gestisce 409 sovrapposizione)
 * - useUpdateEvent(): aggiorna evento (gestisce 409 sovrapposizione)
 * - useDeleteEvent(): elimina evento
 *
 * Ogni mutation invalida ["events"] + ["dashboard"] + ["clients"] (crediti).
 */

import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { toast } from "sonner";
import axios from "axios";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  Event,
  EventCreate,
  EventUpdate,
  ListResponse,
} from "@/types/api";

// ── Evento con date idratate (Date objects, non stringhe) ──

export interface EventHydrated extends Omit<Event, "data_inizio" | "data_fine"> {
  data_inizio: Date;
  data_fine: Date;
}

/** Converte stringhe ISO (o con spazio) in Date objects. */
function hydrateEvent(e: Event): EventHydrated {
  return {
    ...e,
    data_inizio: new Date(e.data_inizio.replace(" ", "T")),
    data_fine: new Date(e.data_fine.replace(" ", "T")),
  };
}

// ── Query: lista eventi per range temporale ──

interface UseEventsParams {
  start?: string; // ISO date "YYYY-MM-DD"
  end?: string;
}

export function useEvents(params: UseEventsParams = {}) {
  const { start, end } = params;

  return useQuery({
    queryKey: ["events", { start, end }],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>("/events", {
        params: { start, end },
      });
      return data;
    },
    select: (data): ListResponse<EventHydrated> => ({
      ...data,
      items: data.items.map(hydrateEvent),
    }),
    enabled: !!start && !!end,
    placeholderData: keepPreviousData,
  });
}

// ── Query: eventi di un singolo cliente (profilo) ──

export function useClientEvents(idCliente: number | null) {
  return useQuery({
    queryKey: ["events", { idCliente }],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>("/events", {
        params: { id_cliente: idCliente },
      });
      return data;
    },
    select: (data): ListResponse<EventHydrated> => ({
      ...data,
      items: data.items.map(hydrateEvent),
    }),
    enabled: idCliente !== null,
  });
}

// ── Query: eventi di un singolo contratto (scheda contratto) ──

export function useContractEvents(idContratto: number | null) {
  return useQuery({
    queryKey: ["events", { idContratto }],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>("/events", {
        params: { id_contratto: idContratto },
      });
      return data;
    },
    select: (data): ListResponse<EventHydrated> => ({
      ...data,
      items: data.items.map(hydrateEvent),
    }),
    enabled: idContratto !== null,
  });
}

// ── Mutation: crea evento ──

/**
 * G9.7.1/B5 — predicato del «mai 201 muto» (AC-G97-1): un PT con cliente nato SENZA aggancio
 * (auto-assegnazione fallita o scelta esplicita) non è mai un successo generico. Puro ed
 * esportato: il vitest gemello lo presidia; P5 (ADR-025) lo riuserà per la conferma di scelta.
 */
export function isPtOrfanoCreato(e: {
  categoria: string;
  id_cliente?: number | null;
  id_contratto?: number | null;
}): boolean {
  return e.categoria === "PT" && e.id_cliente != null && e.id_contratto == null;
}

export function useCreateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: EventCreate) => {
      const { data } = await apiClient.post<Event>("/events", payload);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      // G9.7.1/B5 (ADR-024 D-MAI-SILENZIO-IN-SCRITTURA): un PT con cliente nato SENZA aggancio
      // (auto-assegnazione fallita: nessun contratto attivo agganciabile) non è un successo muto —
      // il 201 porta id_contratto=null e va DETTO, mai il toast di successo generico.
      if (isPtOrfanoCreato(data)) {
        toast.warning(
          "Seduta creata SENZA contratto: non scala crediti. Potrai assegnarla a un contratto attivo.",
          { duration: 8000 },
        );
      } else {
        toast.success("Evento creato");
      }
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        toast.error("Sovrapposizione oraria: hai gia' un impegno in questo slot");
        return;
      }
      toast.error(extractErrorMessage(error, "Errore nella creazione dell'evento"));
    },
  });
}

// ── Mutation: aggiorna evento ──

export function useUpdateEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: EventUpdate & { id: number }) => {
      const { data } = await apiClient.put<Event>(`/events/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      toast.success("Evento aggiornato");
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        toast.error("Sovrapposizione oraria: hai gia' un impegno in questo slot");
        return;
      }
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento dell'evento"));
    },
  });
}

// ── Mutation: elimina evento ──

export function useDeleteEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/events/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      toast.success("Evento eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione dell'evento"));
    },
  });
}
