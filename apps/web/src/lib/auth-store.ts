import { create } from "zustand";

const REFRESH_KEY = "saas_odonto_refresh";

export interface AuthUser {
  sub: string;
  clinic_id: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

type Status = "idle" | "loading" | "authed" | "anon";

interface AuthState {
  /** Access token vive só em memória (some no reload, é renovado pelo refresh). */
  accessToken: string | null;
  /** Refresh token persiste no localStorage. */
  refreshToken: string | null;
  user: AuthUser | null;
  status: Status;
  setStatus: (status: Status) => void;
  setSession: (tokens: TokenResponse) => void;
  clear: () => void;
}

/** Decodifica o payload de um JWT (sem validar assinatura — só p/ ler claims). */
function decodeJwt(token: string): AuthUser | null {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(
      decodeURIComponent(
        atob(payload.replace(/-/g, "+").replace(/_/g, "/"))
          .split("")
          .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
          .join(""),
      ),
    );
    return { sub: json.sub, clinic_id: json.clinic_id, role: json.role };
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: localStorage.getItem(REFRESH_KEY),
  user: null,
  status: "idle",
  setStatus: (status) => set({ status }),
  setSession: (tokens) => {
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
    set({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      user: decodeJwt(tokens.access_token),
      status: "authed",
    });
  },
  clear: () => {
    localStorage.removeItem(REFRESH_KEY);
    set({ accessToken: null, refreshToken: null, user: null, status: "anon" });
  },
}));
