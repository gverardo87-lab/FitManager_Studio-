// src/hooks/useContracts.ts
/**
 * Custom hooks per il modulo Contratti.
 *
 * Pattern identico a useClients: una funzione per operazione,
 * invalidation su ["contracts"] + ["dashboard"], toast su ogni mutation.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  Contract,
  ContractCreate,
  ContractUpdate,
  ContractWithRates,
  ContractListResponse,
  ContractTerminate,
  ContractSettlementPreview,
  RatePayment,
} from "@/types/api";

// ── Query: lista contratti (tutti, filtraggio client-side) ──

export function useContracts() {
  return useQuery<ContractListResponse>({
    queryKey: ["contracts"],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractListResponse>(
        "/contracts",
        { params: { page: 1, page_size: 200 } }
      );
      return data;
    },
  });
}

// ── Query: dettaglio contratto con rate (Master-Detail) ──

export function useContract(id: number | null) {
  return useQuery<ContractWithRates>({
    queryKey: ["contract", id],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractWithRates>(
        `/contracts/${id}`
      );
      return data;
    },
    enabled: id !== null,
  });
}

// ── Query: contratti di un singolo cliente (profilo) ──

export function useClientContracts(idCliente: number | null) {
  return useQuery<ContractListResponse>({
    queryKey: ["contracts", { idCliente }],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractListResponse>(
        "/contracts",
        { params: { page: 1, page_size: 100, id_cliente: idCliente } }
      );
      return data;
    },
    enabled: idCliente !== null,
  });
}

// ── Mutation: crea contratto ──

export function useCreateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ContractCreate) => {
      const { data } = await apiClient.post<Contract>("/contracts", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success("Contratto creato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella creazione del contratto"));
    },
  });
}

// ── Mutation: aggiorna contratto ──

export function useUpdateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: ContractUpdate & { id: number }) => {
      const { data } = await apiClient.put<Contract>(
        `/contracts/${id}`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Contratto aggiornato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento del contratto"));
    },
  });
}

// ── Mutation: rinnova contratto ──

export function useRenewContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      ...payload
    }: ContractCreate & { contractId: number }) => {
      const { data } = await apiClient.post<Contract>(
        `/contracts/${contractId}/renew`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
      toast.success("Contratto rinnovato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel rinnovo del contratto"));
    },
  });
}

// ── Mutation: esito "non rinnova" (cliente perso) + riapertura ──

export function useMarkRenewalOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, motivo, note }: { contractId: number; motivo: string; note?: string }) => {
      const { data } = await apiClient.post<Contract>(
        `/contracts/${contractId}/renewal-outcome`,
        { motivo, note }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Segnato come non rinnovato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel salvataggio dell'esito"));
    },
  });
}

export function useReopenRenewalOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (contractId: number) => {
      await apiClient.delete(`/contracts/${contractId}/renewal-outcome`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Opportunità riaperta");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella riapertura"));
    },
  });
}

// ── Mutation: incassa residuo diretto (G6) ──
// Incasso ENTRATA legato al contratto SENZA passare da una rata (contratti scaduti il cui
// residuo non è più rateizzabile). Invalidazione IDENTICA a usePayRate (regola ferrea:
// operazioni di cassa contrattuale invalidano lo stesso set) → KPI/ledger/dashboard freschi.

export function useIncassaResiduo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      ...payload
    }: RatePayment & { contractId: number }) => {
      const { data } = await apiClient.post<Contract>(
        `/contracts/${contractId}/incassa-residuo`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success("Residuo incassato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'incasso del residuo"));
    },
  });
}

// ── Query: anteprima conguaglio terminazione (G7.3, dry-run) ──
// Calcolo del conguaglio PRIMA della conferma (zero scritture). Sempre fresco (staleTime 0):
// l'esito dipende dallo stato corrente del contratto. Abilitata solo a dialog aperto.

export function useSettlementPreview(contractId: number | null) {
  return useQuery<ContractSettlementPreview>({
    queryKey: ["settlement-preview", contractId],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractSettlementPreview>(
        `/contracts/${contractId}/settlement-preview`
      );
      return data;
    },
    enabled: contractId !== null,
    staleTime: 0,
    gcTime: 0,
  });
}

// ── Mutation: termina contratto (G7.3) ──
// Terminazione anticipata: conguaglio (rimborso/storno) + chiusura, atto atomico. Invalidazione
// = usePayRate (cassa) + lifecycle (chiude il contratto) + workspace/clients. Gemello in USCITA
// di useIncassaResiduo.

export function useTerminateContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contractId,
      ...payload
    }: ContractTerminate & { contractId: number }) => {
      const { data } = await apiClient.post<Contract>(
        `/contracts/${contractId}/terminate`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["forecast"] });
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
      toast.success("Contratto terminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella terminazione del contratto"));
    },
  });
}

// ── Mutation: riapri contratto chiuso (G7.4) ──
// Inverso esplicito di terminate/auto-close: annulla rimborso+storno, ripristina rate, chiuso=False.
// Stessa invalidazione di useTerminateContract (tocca cassa + lifecycle).

export function useReopenContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contractId: number) => {
      const { data } = await apiClient.post<Contract>(
        `/contracts/${contractId}/reopen`,
        {}
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["forecast"] });
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
      toast.success("Contratto riaperto");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella riapertura del contratto"));
    },
  });
}

// ── Mutation: elimina contratto ──

export function useDeleteContract() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, force, keepPayments }: { id: number; force?: boolean; keepPayments?: boolean }) => {
      const params = new URLSearchParams();
      if (force) params.set("force", "true");
      if (keepPayments) params.set("keep_payments", "true");
      const qs = params.toString();
      await apiClient.delete(`/contracts/${id}${qs ? `?${qs}` : ""}`);
    },
    onSuccess: (_data, { force }) => {
      queryClient.invalidateQueries({ queryKey: ["contracts"] });
      queryClient.invalidateQueries({ queryKey: ["contract"] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["client"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      toast.success(force ? "Contratto eliminato forzatamente" : "Contratto eliminato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'eliminazione del contratto"));
    },
  });
}
