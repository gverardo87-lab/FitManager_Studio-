// src/hooks/useCommunications.ts
/**
 * Hook per il log comunicazioni.
 *
 * - useClientCommunications(clientId): lista comunicazioni per un cliente
 * - useLogCommunication(): mutation per registrare una comunicazione
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient from "@/lib/api-client";

// ── Types ──

export interface CommunicationLogItem {
  id: number;
  canale: string; // 'whatsapp' | 'telefono' | 'email' | 'nota'
  template_usato: string | null;
  anteprima: string;
  created_at: string | null;
}

export interface CommunicationLogEnriched extends CommunicationLogItem {
  id_cliente: number;
  client_nome: string;
  client_cognome: string;
}

interface CommunicationCreatePayload {
  id_cliente: number;
  canale: string;
  template_usato?: string;
  anteprima: string;
}

// ── Hooks ──

export function useAllCommunications(clientId?: number | null) {
  return useQuery<{ items: CommunicationLogEnriched[]; total: number }>({
    queryKey: ["communications", "all", clientId ?? "all"],
    queryFn: async () => {
      const params = clientId ? { id_cliente: clientId } : {};
      const { data } = await apiClient.get("/communications", { params });
      return data;
    },
  });
}

export function useClientCommunications(clientId: number | null, enabled = true) {
  return useQuery<{ items: CommunicationLogItem[]; total: number }>({
    queryKey: ["communications", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/communications/${clientId}`);
      return data;
    },
    enabled: enabled && !!clientId,
  });
}

export function useLogCommunication() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CommunicationCreatePayload) => {
      const { data } = await apiClient.post("/communications", payload);
      return data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["communications", variables.id_cliente] });
      qc.invalidateQueries({ queryKey: ["communications", "all"] });
    },
    onError: () => {
      // Silenzioso — il log non deve bloccare l'utente
    },
  });
}
