import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Patient, PatientFormInput } from "./schemas";

const KEY = ["patients"] as const;

/** Normaliza o payload: e-mail vazio vira undefined (o backend valida EmailStr). */
function toPayload(input: PatientFormInput) {
  return {
    nome: input.nome,
    telefone: input.telefone,
    email: input.email ? input.email : undefined,
    observacoes: input.observacoes ? input.observacoes : undefined,
  };
}

export function usePatients() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => (await api.get<Patient[]>("/patients")).data,
  });
}

export function useCreatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: PatientFormInput) =>
      (await api.post<Patient>("/patients", toPayload(input))).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdatePatient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: PatientFormInput) =>
      (await api.patch<Patient>(`/patients/${id}`, toPayload(input))).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeletePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/patients/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
