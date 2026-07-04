import { api } from "@/lib/api";
import { useAuthStore, type TokenResponse } from "@/lib/auth-store";
import { queryClient } from "@/lib/query";
import type { LoginInput } from "./schemas";

/** Faz login e guarda a sessão (access em memória, refresh no localStorage). */
export async function login(input: LoginInput): Promise<void> {
  const res = await api.post<TokenResponse>("/auth/login", input);
  useAuthStore.getState().setSession(res.data);
}

/** Logout real: revoga o refresh token no servidor e depois limpa o cliente.
 *  Best-effort — se a chamada falhar, ainda assim limpamos a sessão local. */
export async function logout(): Promise<void> {
  const refreshToken = useAuthStore.getState().refreshToken;
  try {
    if (refreshToken) {
      await api.post("/auth/logout", { refresh_token: refreshToken });
    }
  } catch {
    // ignora: a limpeza local acontece de qualquer forma
  } finally {
    useAuthStore.getState().clear();
    // Zera o cache do servidor: evita que dados do usuário anterior apareçam
    // para o próximo login no mesmo navegador (recepção compartilhada).
    queryClient.clear();
  }
}
