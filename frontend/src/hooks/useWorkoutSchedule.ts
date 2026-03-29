// src/hooks/useWorkoutSchedule.ts
/**
 * Custom hooks per il modulo Workout Schedule (calendario allenamenti).
 *
 * Pattern: una funzione per operazione, ognuna con la propria queryKey.
 * Le mutations invalidano ["workout-schedule", workoutId] + log correlati.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient, { extractErrorMessage } from "@/lib/api-client";
import type {
  ScheduleSlot,
  ScheduleListResponse,
  ScheduleGenerateRequest,
  ScheduleSlotUpdate,
  ScheduleBulkMoveRequest,
} from "@/types/api";

// ════════════════════════════════════════════════════════════
// QUERY: Lista slot pianificati per una scheda
// ════════════════════════════════════════════════════════════

export function useWorkoutSchedule(workoutId: number | null) {
  return useQuery<ScheduleListResponse>({
    queryKey: ["workout-schedule", workoutId],
    queryFn: async () => {
      const { data } = await apiClient.get<ScheduleListResponse>(
        `/workouts/${workoutId}/schedule`,
      );
      return data;
    },
    enabled: workoutId !== null,
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Genera schedule da pattern settimanale
// ════════════════════════════════════════════════════════════

export function useGenerateSchedule(workoutId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScheduleGenerateRequest) => {
      const { data } = await apiClient.post<ScheduleListResponse>(
        `/workouts/${workoutId}/schedule/generate`,
        payload,
      );
      return data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["workout-schedule", workoutId] });
      queryClient.invalidateQueries({ queryKey: ["workout", workoutId] });
      queryClient.invalidateQueries({ queryKey: ["workouts"] });
      toast.success(`Calendario generato: ${result.total} sessioni pianificate`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella generazione del calendario"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Aggiorna singolo slot (data, stato, note)
// ════════════════════════════════════════════════════════════

export function useUpdateScheduleSlot(workoutId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ slotId, ...payload }: ScheduleSlotUpdate & { slotId: number }) => {
      const { data } = await apiClient.put<ScheduleSlot>(
        `/workout-schedule/${slotId}`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workout-schedule", workoutId] });
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nell'aggiornamento dello slot"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Completa slot → crea WorkoutLog automatico
// ════════════════════════════════════════════════════════════

export function useCompleteScheduleSlot(workoutId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (slotId: number) => {
      const { data } = await apiClient.put<ScheduleSlot>(
        `/workout-schedule/${slotId}/complete`,
      );
      return data;
    },
    onSuccess: (slot) => {
      queryClient.invalidateQueries({ queryKey: ["workout-schedule", workoutId] });
      queryClient.invalidateQueries({ queryKey: ["workout-logs"] });
      queryClient.invalidateQueries({ queryKey: ["session-prep"] });
      queryClient.invalidateQueries({ queryKey: ["client-avatar", slot.id_cliente] });
      toast.success(`${slot.sessione_nome} completata`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nel completamento della sessione"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Riapri slot (reset stato + elimina log)
// ════════════════════════════════════════════════════════════

export function useReopenScheduleSlot(workoutId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (slotId: number) => {
      const { data } = await apiClient.put<ScheduleSlot>(
        `/workout-schedule/${slotId}/reopen`,
      );
      return data;
    },
    onSuccess: async (slot) => {
      // refetchQueries (non invalidate) → forza ri-fetch IMMEDIATO,
      // anche se staleTime non è scaduto. Critico perché i dati
      // eliminati devono sparire subito da tutte le viste.
      await Promise.all([
        queryClient.refetchQueries({ queryKey: ["workout-schedule"] }),
        queryClient.refetchQueries({ queryKey: ["workout-logs"] }),
        queryClient.refetchQueries({ queryKey: ["workout-analytics"] }),
      ]);
      queryClient.invalidateQueries({ queryKey: ["client-avatar", slot.id_cliente] });
      queryClient.invalidateQueries({ queryKey: ["session-prep"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`${slot.sessione_nome} riaperta — tutti i dati eliminati`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella riapertura della sessione"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Soft-delete slot
// ════════════════════════════════════════════════════════════

export function useDeleteScheduleSlot(workoutId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (slotId: number) => {
      await apiClient.delete(`/workout-schedule/${slotId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workout-schedule", workoutId] });
      toast.success("Slot rimosso");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nella rimozione dello slot"));
    },
  });
}

// ════════════════════════════════════════════════════════════
// MUTATION: Bulk move slots
// ════════════════════════════════════════════════════════════

export function useBulkMoveSlots(workoutId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ScheduleBulkMoveRequest) => {
      const { data } = await apiClient.post<ScheduleListResponse>(
        `/workouts/${workoutId}/schedule/bulk-move`,
        payload,
      );
      return data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["workout-schedule", workoutId] });
      toast.success(`${result.total} sessioni spostate`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error, "Errore nello spostamento delle sessioni"));
    },
  });
}
