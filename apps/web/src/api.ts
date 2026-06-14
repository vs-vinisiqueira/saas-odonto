// Em dev, o Vite faz proxy de /api -> http://localhost:8000 (ver vite.config.ts)
const BASE = "/api";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    throw new Error("Falha no login");
  }
  return res.json();
}

export async function getMyClinic(accessToken: string) {
  const res = await fetch(`${BASE}/clinics/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) {
    throw new Error("Falha ao carregar a clínica");
  }
  return res.json();
}
