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

interface CommunicationCreatePayload {
  id_cliente: number;
  canale: string;
  template_usato?: string;
  anteprima: string;
}

// ── Hooks ──

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
    },
    onError: () => {
      // Silenzioso — il log non deve bloccare l'utente
    },
  });
}
