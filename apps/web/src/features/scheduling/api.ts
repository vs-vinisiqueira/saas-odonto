import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface Slot {
  starts_at: string;
  ends_at: string;
}

export type AppointmentTipo =
  | "avaliacao"
  | "limpeza"
  | "restauracao"
  | "canal"
  | "clareamento"
  | "cirurgia";

export interface Appointment {
  id: string;
  patient_id: string;
  patient_nome: string | null;
  dentist_id: string | null;
  starts_at: string;
  ends_at: string;
  status: string;
  tipo: AppointmentTipo;
  notes: string | null;
}

export interface CreateAppointmentInput {
  patient_id: string;
  starts_at: string;
  duration_min?: number;
  dentist_id?: string | null;
  tipo?: AppointmentTipo;
  notes?: string | null;
}

/** Campos editáveis de um agendamento já existente (PATCH parcial). */
export interface UpdateAppointmentInput {
  status?: string;
  dentist_id?: string;
  tipo?: AppointmentTipo;
  notes?: string;
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

/** Agendamentos de um range de dias (ex.: a semana inteira da visão semanal). */
export function useAppointmentsRange(from: string, to: string) {
  return useQuery({
    queryKey: ["appointments", "range", from, to],
    queryFn: async () =>
      (
        await api.get<Appointment[]>("/scheduling/appointments", {
          params: { from, to },
        })
      ).data,
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

export function useUpdateAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateAppointmentInput }) =>
      (await api.patch<Appointment>(`/scheduling/appointments/${id}`, data)).data,
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

export function useDeleteAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/scheduling/appointments/${id}`);
    },
    onSuccess: () => invalidateAgenda(qc),
  });
}
