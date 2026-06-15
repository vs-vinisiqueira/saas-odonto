import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface Slot {
  starts_at: string;
  ends_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  dentist_id: string | null;
  starts_at: string;
  ends_at: string;
  status: string;
  notes: string | null;
}

export interface CreateAppointmentInput {
  patient_id: string;
  starts_at: string;
  duration_min?: number;
}

export function useAvailability(date: string) {
  return useQuery({
    queryKey: ["availability", date],
    queryFn: async () =>
      (await api.get<Slot[]>("/scheduling/availability", { params: { date } })).data,
  });
}

export function useAppointments(date: string) {
  return useQuery({
    queryKey: ["appointments", date],
    queryFn: async () =>
      (await api.get<Appointment[]>("/scheduling/appointments", { params: { date } }))
        .data,
  });
}

function invalidateAgenda(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["availability"] });
  qc.invalidateQueries({ queryKey: ["appointments"] });
}

export function useCreateAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateAppointmentInput) =>
      (await api.post<Appointment>("/scheduling/appointments", input)).data,
    onSuccess: () => invalidateAgenda(qc),
  });
}

export function useCancelAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.post<Appointment>(`/scheduling/appointments/${id}/cancel`)).data,
    onSuccess: () => invalidateAgenda(qc),
  });
}
