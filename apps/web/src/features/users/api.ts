import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  User,
  UserCreateInput,
  UserEditInput,
} from "./schemas";

const KEY = ["users"] as const;

export function useUsers() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => (await api.get<User[]>("/users")).data,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: UserCreateInput) =>
      (
        await api.post<User>("/users", {
          email: input.email,
          password: input.password,
          role: input.role,
          nome: input.nome,
          telefone: input.telefone || undefined,
        })
      ).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

type UpdatePayload = Partial<UserEditInput> & { is_active?: boolean };

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdatePayload }) =>
      (await api.patch<User>(`/users/${id}`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async ({ id, password }: { id: string; password: string }) => {
      await api.post(`/users/${id}/reset-password`, { password });
    },
  });
}
