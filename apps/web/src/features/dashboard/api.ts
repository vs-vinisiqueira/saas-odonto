import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface SchedulingStats {
  total: number;
  by_status: Record<string, number>;
  per_day: Record<string, number>;
}

/** Resumo da agenda num intervalo [from, to] (datas YYYY-MM-DD, fim inclusivo). */
export function useSchedulingStats(from: string, to: string) {
  return useQuery({
    queryKey: ["scheduling-stats", from, to],
    queryFn: async () =>
      (
        await api.get<SchedulingStats>("/scheduling/stats", {
          params: { from, to },
        })
      ).data,
  });
}
