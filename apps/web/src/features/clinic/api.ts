import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface Clinic {
  id: string;
  nome: string;
  config: Record<string, unknown>;
}

async function getMyClinic(): Promise<Clinic> {
  const res = await api.get<Clinic>("/clinics/me");
  return res.data;
}

export function useMyClinic() {
  return useQuery({ queryKey: ["clinic", "me"], queryFn: getMyClinic });
}
