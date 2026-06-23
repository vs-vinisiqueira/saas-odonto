import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Integration, ProviderId } from "./schemas";

const KEY = ["integrations"] as const;

export function useIntegrations() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => (await api.get<Integration[]>("/integrations")).data,
  });
}

export interface IntegrationUpdatePayload {
  enabled?: boolean;
  public_config?: Record<string, string>;
  secrets?: Record<string, string>;
}

export function useUpdateIntegration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      provider,
      data,
    }: {
      provider: ProviderId;
      data: IntegrationUpdatePayload;
    }) => (await api.put<Integration>(`/integrations/${provider}`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDisconnectIntegration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (provider: ProviderId) =>
      (await api.delete<Integration>(`/integrations/${provider}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
