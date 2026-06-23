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
import { ConversationsPage } from "@/features/conversations/conversations-page";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { LoginPage } from "@/features/auth/login-page";
import { PatientsPage } from "@/features/patients/patients-page";
import { PatientRecordPage } from "@/features/patients/patient-record-page";
import { ConfigPage } from "@/features/config/config-page";
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
              { index: true, element: <Navigate to="/dashboard" replace /> },
              { path: "dashboard", element: <DashboardPage /> },
              { path: "agenda", element: <AgendaPage /> },
              { path: "conversas", element: <ConversationsPage /> },
              { path: "pacientes", element: <PatientsPage /> },
              { path: "pacientes/:id", element: <PatientRecordPage /> },
              { path: "cobrancas", element: <BillingPage /> },
              { path: "config", element: <ConfigPage /> },
            ],
          },
        ],
      },
      { path: "*", element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
