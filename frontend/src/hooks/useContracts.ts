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
  ReopenPreview,
  ContractHistoryEvent,
  CreditoTerminazione,
  CreditoDaIncassareItem,
  CreditoCliente,
  RimborsoDaErogareItem,
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

// ── Query: storico stato/attività del contratto (F6, G8.1.1) — timeline curata da audit_log ──

export function useContractHistory(id: number | null) {
  return useQuery<ContractHistoryEvent[]>({
    queryKey: ["contract-history", id],
    queryFn: async () => {
      const { data } = await apiClient.get<ContractHistoryEvent[]>(
        `/contracts/${id}/history`
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

// ── Credito differito post-chiusura (G7.10) — worklist + incasso/annulla del receivable ──
// L'incasso fa crescere totale_versato (Strada B) → stesse invalidazioni cassa di useIncassaResiduo.

export function useCreditiDaIncassare() {
  return useQuery<{ items: CreditoDaIncassareItem[]; total: number }>({
    queryKey: ["dashboard", "crediti-da-incassare"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: CreditoDaIncassareItem[]; total: number }>(
        "/dashboard/crediti-da-incassare"
      );
      return data;
    },
  });
}

export function useCreditiTerminazione(contractId: number | null) {
  return useQuery<CreditoTerminazione[]>({
    queryKey: ["crediti-terminazione", contractId],
    queryFn: async () => {
      const { data } = await apiClient.get<CreditoTerminazione[]>(
        `/contracts/${contractId}/crediti-terminazione`
      );
      return data;
    },
    enabled: contractId !== null,
  });
}

function invalidateCreditoQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["contract"] });
  queryClient.invalidateQueries({ queryKey: ["contracts"] });
  queryClient.invalidateQueries({ queryKey: ["crediti-terminazione"] });
  queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  queryClient.invalidateQueries({ queryKey: ["movements"] });
  queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
  queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
  queryClient.invalidateQueries({ queryKey: ["aging-report"] });
  queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
}

export function useIncassaCredito() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      contractId,
      creditoId,
      ...payload
    }: RatePayment & { contractId: number; creditoId: number }) => {
      const { data } = await apiClient.post<CreditoTerminazione>(
        `/contracts/${contractId}/crediti-terminazione/${creditoId}/incassa`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      invalidateCreditoQueries(queryClient);
      toast.success("Credito incassato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'incasso del credito"));
    },
  });
}

export function useAnnullaCredito() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, creditoId }: { contractId: number; creditoId: number }) => {
      const { data } = await apiClient.post<CreditoTerminazione>(
        `/contracts/${contractId}/crediti-terminazione/${creditoId}/annulla`
      );
      return data;
    },
    onSuccess: () => {
      invalidateCreditoQueries(queryClient);
      toast.success("Credito annullato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'annullamento del credito"));
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
      queryClient.invalidateQueries({ queryKey: ["client-wallet"] });  // G8.1: terminate può creare un wallet
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
      queryClient.invalidateQueries({ queryKey: ["client-wallet"] });  // G8.1: reopen annulla i wallet
      toast.success("Contratto riaperto");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella riapertura del contratto"));
    },
  });
}

// ── Query: anteprima riapertura (G8.1/ADR-019, dry-run) ──
// Impatto pieno PRIMA della conferma (zero scritture): cosa resta / cosa si annulla + rinnovo vivo.
// Sempre fresco (staleTime 0): dipende dallo stato corrente. Abilitata solo a dialog aperto.

export function useReopenPreview(contractId: number | null) {
  return useQuery<ReopenPreview>({
    queryKey: ["reopen-preview", contractId],
    queryFn: async () => {
      const { data } = await apiClient.get<ReopenPreview>(
        `/contracts/${contractId}/reopen-preview`
      );
      return data;
    },
    enabled: contractId !== null,
    staleTime: 0,
    gcTime: 0,
  });
}

// ── Wallet del cliente (G8.1, ADR-020) — worklist + erogazione + lista per profilo ──
// L'erogazione fa USCITA RIMBORSO_CONTRATTO (id_contratto=None) → invalida la cassa, NON il contratto.

export function useRimborsiDaErogare() {
  return useQuery<{ items: RimborsoDaErogareItem[]; total: number }>({
    queryKey: ["dashboard", "rimborsi-da-erogare"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: RimborsoDaErogareItem[]; total: number }>(
        "/dashboard/rimborsi-da-erogare"
      );
      return data;
    },
  });
}

export function useClientWalletCredits(clientId: number | null) {
  return useQuery<CreditoCliente[]>({
    queryKey: ["client-wallet", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<CreditoCliente[]>(`/clients/${clientId}/crediti`);
      return data;
    },
    enabled: clientId !== null,
  });
}

export function useEroghaRimborso() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      clientId,
      creditoId,
      ...payload
    }: RatePayment & { clientId: number; creditoId: number }) => {
      const { data } = await apiClient.post<CreditoCliente>(
        `/clients/${clientId}/crediti/${creditoId}/eroga`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["client-wallet"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["movement-stats"] });
      queryClient.invalidateQueries({ queryKey: ["financial-trend"] });
      queryClient.invalidateQueries({ queryKey: ["aging-report"] });
      queryClient.invalidateQueries({ queryKey: ["cash-balance"] });
      queryClient.invalidateQueries({ queryKey: ["forecast"] });
      toast.success("Rimborso erogato");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'erogazione del rimborso"));
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
