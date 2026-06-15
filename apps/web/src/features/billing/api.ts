import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { ChargeFormInput, Payment } from "./schemas";

const KEY = ["charges"] as const;

export function useCharges() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => (await api.get<Payment[]>("/billing/charges")).data,
  });
}

export function useCreateCharge() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: ChargeFormInput) =>
      (
        await api.post<Payment>("/billing/charges", {
          valor: input.valor.toFixed(2),
          descricao: input.descricao || undefined,
          patient_id: input.patient_id || undefined,
        })
      ).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useRefreshCharge() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.post<Payment>(`/billing/charges/${id}/refresh`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
