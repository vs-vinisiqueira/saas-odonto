import {
  CalendarDays,
  CreditCard,
  LayoutDashboard,
  LogOut,
  MessagesSquare,
  Moon,
  Settings,
  Sun,
  Users,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Spinner } from "@/components/ui/spinner";
import { useMyClinic } from "@/features/clinic/api";
import { useConversations } from "@/features/conversations/api";
import { useAuthStore } from "@/lib/auth-store";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/agenda", label: "Agenda", icon: CalendarDays },
  { to: "/conversas", label: "Conversas", icon: MessagesSquare, badge: true },
  { to: "/pacientes", label: "Pacientes", icon: Users },
  { to: "/cobrancas", label: "Cobranças", icon: CreditCard },
];

function initials(name: string) {
  return name
    .replace(/^Dra?\.?\s*/i, "")
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const toggle = useThemeStore((s) => s.toggle);
  return (
    <button
      onClick={toggle}
      title={theme === "dark" ? "Tema claro" : "Tema escuro"}
      className="flex h-9 w-9 items-center justify-center rounded-[11px] border border-border bg-card text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

export function AppShell() {
  const navigate = useNavigate();
  const clear = useAuthStore((s) => s.clear);
  const user = useAuthStore((s) => s.user);
  const clinic = useMyClinic();
  const conversations = useConversations();

  const unreadCount = conversations.data?.filter((c) => c.unread).length ?? 0;

  const clinicName = clinic.data?.nome ?? "SaaS Odonto";
  const userName = user?.role === "owner" ? clinicName : (user?.role ?? "Usuário");
  const userInitials = initials(userName);

  function handleLogout() {
    clear();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="hidden w-[248px] shrink-0 flex-col border-r bg-card md:flex" style={{ padding: "18px 14px" }}>
        {/* Logo + Clínica */}
        <div className="flex items-center gap-3 pb-5 pl-1">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
            style={{
              background: "linear-gradient(145deg, #7C3AED, #0D9488)",
              boxShadow: "0 4px 12px rgba(124,58,237,.28)",
            }}
          >
            <div className="relative h-4 w-4">
              <div className="absolute left-0 top-0 h-2.5 w-2.5 rounded-full bg-white opacity-90" />
              <div className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-white opacity-55" />
            </div>
          </div>
          <div className="leading-tight">
            {clinic.isLoading ? (
              <Spinner className="h-4 w-4 text-primary" />
            ) : (
              <span className="block text-[15px] font-extrabold tracking-tight text-foreground">
                {clinicName}
              </span>
            )}
            <span className="block text-[11.5px] font-medium text-muted-foreground">
              Painel da clínica
            </span>
          </div>
        </div>

        {/* Label seção */}
        <div className="mb-1.5 px-2 text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
          Menu
        </div>

        {/* Navegação */}
        <nav className="flex flex-col gap-0.5">
          {NAV.map(({ to, label, icon: Icon, badge }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-[10px] px-2.5 py-2 text-[14px] font-medium transition-all",
                  isActive
                    ? "font-bold text-[hsl(var(--nav-active-text))] [background:hsl(var(--nav-active-bg))] [box-shadow:inset_0_0_0_1px_hsl(var(--nav-active-ring))]"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )
              }
            >
              <Icon className="h-[18px] w-[18px] shrink-0" />
              <span className="flex-1">{label}</span>
              {badge && unreadCount > 0 && (
                <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-primary px-1.5 text-[11.5px] font-bold text-primary-foreground">
                  {unreadCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex-1" />

        {/* Configurações */}
        <NavLink
          to="/config"
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2.5 rounded-[10px] px-2.5 py-2 text-[14px] font-medium transition-all",
              isActive
                ? "font-bold text-[hsl(var(--nav-active-text))] [background:hsl(var(--nav-active-bg))]"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground",
            )
          }
        >
          <Settings className="h-[18px] w-[18px] shrink-0" />
          <span className="flex-1">Configurações</span>
        </NavLink>

        {/* Usuário */}
        <div className="mt-2 flex items-center gap-2.5 border-t border-border-soft px-2 pt-3">
          <div
            className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-white"
            style={{ background: "linear-gradient(135deg, #7C3AED, #0D9488)" }}
          >
            {userInitials}
          </div>
          <div className="min-w-0 flex-1 leading-tight">
            <span className="block truncate text-[13px] font-bold text-foreground">
              {clinicName}
            </span>
            <span className="block text-[11.5px] capitalize text-muted-foreground">
              {user?.role ?? ""}
            </span>
          </div>
          <button
            onClick={handleLogout}
            title="Sair"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* Conteúdo principal */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar */}
        <header
          className="flex h-[66px] shrink-0 items-center gap-4 border-b px-7"
          style={{ background: "var(--glass)", backdropFilter: "blur(10px)", zIndex: 5 }}
        >
          <h1 className="text-[19px] font-extrabold tracking-tight text-foreground">
            {/* título dinâmico via outlet — mantemos a clínica no topo */}
            {clinicName}
          </h1>
          <div className="flex-1" />
          <ThemeToggle />
          <button
            onClick={handleLogout}
            title="Sair"
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-destructive md:px-3"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden md:inline">Sair</span>
          </button>
          {/* Avatar topbar */}
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[13px] font-bold text-white"
            style={{ background: "linear-gradient(135deg, #7C3AED, #0D9488)" }}
          >
            {userInitials}
          </div>
        </header>

        {/* Nav mobile — inclui Configurações, que no desktop fica na barra lateral */}
        <nav className="flex gap-1 overflow-x-auto border-b bg-card px-2 py-2 md:hidden">
          {[...NAV, { to: "/config", label: "Config", icon: Settings }].map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-md px-1 py-1.5 text-[10.5px]",
                  isActive ? "text-primary font-semibold" : "text-muted-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <main className="flex-1 overflow-auto bg-background p-5 md:p-7">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
