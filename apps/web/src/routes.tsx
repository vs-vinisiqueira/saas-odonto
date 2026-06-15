import { useEffect } from "react";
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouterProvider,
} from "react-router-dom";

import { AppShell } from "@/components/layout/app-shell";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { FullPageSpinner } from "@/components/ui/spinner";
import { AgendaPage } from "@/features/scheduling/agenda-page";
import { BillingPage } from "@/features/billing/billing-page";
import { LoginPage } from "@/features/auth/login-page";
import { PatientsPage } from "@/features/patients/patients-page";
import { bootstrapAuth } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

/** Raiz: dispara o bootstrap da sessão e segura o app até resolver. */
function RootLayout() {
  const status = useAuthStore((s) => s.status);

  useEffect(() => {
    void bootstrapAuth();
  }, []);

  if (status === "idle") {
    return <FullPageSpinner />;
  }
  return <Outlet />;
}

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: "/login", element: <LoginPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppShell />,
            children: [
              { index: true, element: <Navigate to="/agenda" replace /> },
              { path: "agenda", element: <AgendaPage /> },
              { path: "pacientes", element: <PatientsPage /> },
              { path: "cobrancas", element: <BillingPage /> },
            ],
          },
        ],
      },
      { path: "*", element: <Navigate to="/agenda" replace /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
