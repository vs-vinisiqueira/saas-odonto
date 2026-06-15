import { CalendarDays, CreditCard, LogOut, Users } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useMyClinic } from "@/features/clinic/api";
import { useAuthStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/agenda", label: "Agenda", icon: CalendarDays },
  { to: "/pacientes", label: "Pacientes", icon: Users },
  { to: "/cobrancas", label: "Cobranças", icon: CreditCard },
];

export function AppShell() {
  const navigate = useNavigate();
  const clear = useAuthStore((s) => s.clear);
  const user = useAuthStore((s) => s.user);
  const clinic = useMyClinic();

  function handleLogout() {
    clear();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card px-3 py-5 md:flex">
        <div className="mb-6 flex items-center gap-2 px-2">
          <span className="text-xl">🦷</span>
          <span className="font-semibold">SaaS Odonto</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Conteúdo */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b bg-card px-4 md:px-6">
          <div className="flex items-center gap-2 text-sm">
            {clinic.isLoading ? (
              <Spinner />
            ) : (
              <span className="font-medium">{clinic.data?.nome ?? "—"}</span>
            )}
            {user?.role && (
              <span className="rounded bg-secondary px-2 py-0.5 text-xs capitalize text-muted-foreground">
                {user.role}
              </span>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Sair
          </Button>
        </header>

        {/* Nav mobile */}
        <nav className="flex gap-1 border-b bg-card px-2 py-2 md:hidden">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex flex-1 flex-col items-center gap-0.5 rounded-md px-2 py-1 text-xs",
                  isActive ? "text-primary" : "text-muted-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <main className="flex-1 bg-background p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
