import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import { useAuthStore, type TokenResponse } from "./auth-store";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";

/** Cliente principal: injeta o access token e renova no 401. */
export const api = axios.create({ baseURL: BASE_URL });

/** Cliente "cru" (sem interceptors) usado só para o refresh, evitando loop. */
const bare = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh em single-flight: várias 401 concorrentes compartilham 1 chamada.
let refreshPromise: Promise<TokenResponse> | null = null;

async function doRefresh(): Promise<TokenResponse> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) throw new Error("sem refresh token");
  const res = await bare.post<TokenResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  useAuthStore.getState().setSession(res.data);
  return res.data;
}

function refreshSession(): Promise<TokenResponse> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (AxiosRequestConfig & { _retry?: boolean })
      | undefined;
    const status = error.response?.status;

    if (status === 401 && original && !original._retry) {
      original._retry = true;
      try {
        const tokens = await refreshSession();
        original.headers = {
          ...original.headers,
          Authorization: `Bearer ${tokens.access_token}`,
        };
        return api(original);
      } catch {
        useAuthStore.getState().clear();
      }
    }
    return Promise.reject(error);
  },
);

/** Chamado na carga do app: tenta reerguer a sessão a partir do refresh token. */
export async function bootstrapAuth(): Promise<void> {
  const { refreshToken, accessToken, setStatus } = useAuthStore.getState();
  if (accessToken) {
    setStatus("authed");
    return;
  }
  if (!refreshToken) {
    setStatus("anon");
    return;
  }
  setStatus("loading");
  try {
    await refreshSession();
  } catch {
    useAuthStore.getState().clear();
  }
}

/** Extrai uma mensagem de erro amigável de uma falha do axios. */
export function errorMessage(err: unknown, fallback = "Algo deu errado."): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}
