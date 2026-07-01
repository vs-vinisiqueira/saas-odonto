import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface ClinicDataConfig {
  cnpj?: string | null;
  razao_social?: string | null;
  endereco?: string | null;
  telefone?: string | null;
  logo_url?: string | null;
}

export interface DayHours {
  closed: boolean;
  start: string;
  end: string;
  lunch_start?: string | null;
  lunch_end?: string | null;
}

export type WeekdayKey = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";

export type WorkingHoursConfig = Partial<Record<WeekdayKey, DayHours>>;

export interface PreferencesConfig {
  reminders_enabled: boolean;
}

export interface ClinicConfig {
  clinic_data?: ClinicDataConfig;
  working_hours?: WorkingHoursConfig;
  preferences?: PreferencesConfig;
}

export interface Clinic {
  id: string;
  nome: string;
  config: ClinicConfig;
}

async function getMyClinic(): Promise<Clinic> {
  const res = await api.get<Clinic>("/clinics/me");
  return res.data;
}

export function useMyClinic() {
  return useQuery({ queryKey: ["clinic", "me"], queryFn: getMyClinic });
}

export interface UpdateClinicInput {
  nome?: string;
  config?: ClinicConfig;
}

export function useUpdateClinic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: UpdateClinicInput) =>
      (await api.patch<Clinic>("/clinics/me", data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clinic", "me"] }),
  });
}
