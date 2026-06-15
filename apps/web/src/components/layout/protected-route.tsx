import { Navigate, Outlet, useLocation } from "react-router-dom";

import { FullPageSpinner } from "@/components/ui/spinner";
import { useAuthStore } from "@/lib/auth-store";

/** Bloqueia rotas até a sessão estar resolvida; redireciona p/ login se anônimo. */
export function ProtectedRoute() {
  const status = useAuthStore((s) => s.status);
  const location = useLocation();

  if (status === "idle" || status === "loading") {
    return <FullPageSpinner />;
  }
  if (status === "anon") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}
