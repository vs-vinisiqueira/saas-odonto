import { api } from "@/lib/api";
import { useAuthStore, type TokenResponse } from "@/lib/auth-store";
import type { LoginInput } from "./schemas";

/** Faz login e guarda a sessão (access em memória, refresh no localStorage). */
export async function login(input: LoginInput): Promise<void> {
  const res = await api.post<TokenResponse>("/auth/login", input);
  useAuthStore.getState().setSession(res.data);
}
