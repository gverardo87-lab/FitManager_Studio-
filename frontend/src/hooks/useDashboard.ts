// src/hooks/useDashboard.ts
/**
 * Custom hooks per la dashboard.
 *
 * - useDashboard(): KPI aggregati (GET /api/dashboard/summary)
 * - useDashboardAlerts(): warning proattivi (GET /api/dashboard/alerts)
 * - useGhostEvents(): eventi fantasma per risoluzione inline (GET /api/dashboard/ghost-events)
 *
 * Re-fetch automatico ogni 60 secondi.
 */

import { useQuery, keepPreviousData } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import type {
  DashboardSummary,
  DashboardAlerts,
  ClinicalReadinessResponse,
  ClinicalReadinessWorklistResponse,
  ClinicalPriority,
  ClientProjectionResponse,
  Event,
  ListResponse,
  OverdueRateItem,
  ExpiringContractItem,
  ContractToPlanItem,
  ClientToRecoverItem,
  InactiveClientItem,
  BirthdayClientItem,
  TrainingMethodologyWorklistResponse,
} from "@/types/api";

export function useDashboard() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardSummary>(
        "/dashboard/summary"
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}

export function useDashboardAlerts() {
  return useQuery<DashboardAlerts>({
    queryKey: ["dashboard", "alerts"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardAlerts>(
        "/dashboard/alerts"
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}

export function useClinicalReadiness() {
  return useQuery<ClinicalReadinessResponse>({
    queryKey: ["dashboard", "clinical-readiness"],
    queryFn: async () => {
      const { data } = await apiClient.get<ClinicalReadinessResponse>(
        "/dashboard/clinical-readiness"
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}

type ClinicalTimelineStatus =
  | "overdue"
  | "today"
  | "upcoming_7d"
  | "upcoming_14d"
  | "future"
  | "none";

export interface ClinicalReadinessWorklistQuery {
  page?: number;
  page_size?: number;
  view?: "all" | "todo" | "ready";
  sort_by?: "priority" | "due_date";
  priority?: ClinicalPriority;
  timeline_status?: ClinicalTimelineStatus;
  search?: string;
}

export function useClinicalReadinessWorklist(
  query: ClinicalReadinessWorklistQuery = {},
  enabled = true,
) {
  const params = {
    page: query.page ?? 1,
    page_size: query.page_size ?? 25,
    view: query.view ?? "todo",
    sort_by: query.sort_by ?? "priority",
    priority: query.priority,
    timeline_status: query.timeline_status,
    search: query.search?.trim() || undefined,
  };

  return useQuery<ClinicalReadinessWorklistResponse>({
    queryKey: ["dashboard", "clinical-readiness", "worklist", params],
    queryFn: async () => {
      const { data } = await apiClient.get<ClinicalReadinessWorklistResponse>(
        "/dashboard/clinical-readiness/worklist",
        { params },
      );
      return data;
    },
    refetchInterval: 60_000,
    placeholderData: keepPreviousData,
    enabled,
  });
}

export function useGhostEvents(enabled = true) {
  return useQuery<ListResponse<Event>>({
    queryKey: ["dashboard", "ghost-events"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<Event>>(
        "/dashboard/ghost-events"
      );
      return data;
    },
    enabled,
  });
}

export function useOverdueRates(enabled = true) {
  return useQuery<ListResponse<OverdueRateItem>>({
    queryKey: ["dashboard", "overdue-rates"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<OverdueRateItem>>(
        "/dashboard/overdue-rates"
      );
      return data;
    },
    enabled,
  });
}

export function useExpiringContracts(enabled = true) {
  return useQuery<ListResponse<ExpiringContractItem>>({
    queryKey: ["dashboard", "expiring-contracts"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<ExpiringContractItem>>(
        "/dashboard/expiring-contracts"
      );
      return data;
    },
    enabled,
  });
}

export function useContractsToPlan(enabled = true) {
  return useQuery<ListResponse<ContractToPlanItem>>({
    queryKey: ["dashboard", "contracts-to-plan"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<ContractToPlanItem>>(
        "/dashboard/contracts-to-plan"
      );
      return data;
    },
    enabled,
  });
}

export function useClientsToRecover(enabled = true) {
  return useQuery<ListResponse<ClientToRecoverItem>>({
    queryKey: ["dashboard", "clients-to-recover"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<ClientToRecoverItem>>(
        "/dashboard/clients-to-recover"
      );
      return data;
    },
    enabled,
  });
}

export function useBirthdayClients(enabled = true) {
  return useQuery<ListResponse<BirthdayClientItem>>({
    queryKey: ["dashboard", "birthday-clients"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<BirthdayClientItem>>(
        "/dashboard/birthday-clients"
      );
      return data;
    },
    enabled,
  });
}

export function useInactiveClients(enabled = true) {
  return useQuery<ListResponse<InactiveClientItem>>({
    queryKey: ["dashboard", "inactive-clients"],
    queryFn: async () => {
      const { data } = await apiClient.get<ListResponse<InactiveClientItem>>(
        "/dashboard/inactive-clients"
      );
      return data;
    },
    enabled,
  });
}

// ════════════════════════════════════════════════════════════
// TRAINING METHODOLOGY — Proiezioni
// ════════════════════════════════════════════════════════════

/**
 * Proiezione 3-layer per un cliente.
 *
 * GET /api/training-methodology/projection/{clientId}
 * Layer 1: Volume accumulation (se piano attivo)
 * Layer 2: Metric trends (se misurazioni)
 * Layer 3: Goal projections (se goal + trend)
 */
export function useClientProjection(clientId: number | null) {
  return useQuery<ClientProjectionResponse>({
    queryKey: ["projection", clientId],
    queryFn: async () => {
      const { data } = await apiClient.get<ClientProjectionResponse>(
        `/training-methodology/projection/${clientId}`,
      );
      return data;
    },
    enabled: !!clientId,
    staleTime: 60_000,
  });
}
