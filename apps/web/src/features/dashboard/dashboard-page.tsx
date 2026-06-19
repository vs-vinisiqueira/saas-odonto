import {
  CalendarCheck,
  CalendarDays,
  CreditCard,
  MessagesSquare,
  Users,
} from "lucide-react";
import { useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Skeleton } from "@/components/ui/skeleton";
import { useConversations } from "@/features/conversations/api";
import { usePatients } from "@/features/patients/api";
import { useCharges } from "@/features/billing/api";
import { useAppointments } from "@/features/scheduling/api";
import { addDaysStr, formatTimeUTC, todayStr } from "@/lib/datetime";
import { cn } from "@/lib/utils";
import { useSchedulingStats } from "./api";

const PT_WEEKDAYS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];

const STATUS_BADGE: Record<string, { label: string; bg: string; color: string }> = {
  scheduled:  { label: "Agendada",  bg: "#F4F4F5", color: "#52525B" },
  confirmed:  { label: "Confirmada",bg: "#EFF6FF", color: "#1D4ED8" },
  cancelled:  { label: "Cancelada", bg: "#FEF2F2", color: "#B91C1C" },
  completed:  { label: "Concluída", bg: "#F0FDF4", color: "#15803D" },
  no_show:    { label: "Faltou",    bg: "#FFF7ED", color: "#C2410C" },
};

function weekRange(date: string) {
  const [y, mo, da] = date.split("-").map(Number);
  const dow = new Date(Date.UTC(y, mo - 1, da)).getUTCDay();
  const start = addDaysStr(date, -dow);
  return { start, days: Array.from({ length: 7 }, (_, i) => addDaysStr(start, i)) };
}

// ─── KPI card ─────────────────────────────────────────────────────────────────
interface KpiProps {
  label: string;
  value: number | string;
  Icon: typeof CalendarDays;
  iconBg: string;
  iconColor: string;
  badge?: string;
  badgeBg?: string;
  badgeColor?: string;
  loading?: boolean;
  accent?: boolean;
  delay?: string;
}

function KpiCard({ label, value, Icon, iconBg, iconColor, badge, badgeBg, badgeColor, loading, accent, delay = "0s" }: KpiProps) {
  return (
    <div
      className="animate-fade-up rounded-[18px] border bg-card p-5 shadow-[0_1px_2px_rgba(16,24,40,.04)] transition-all hover:-translate-y-[3px] hover:shadow-[0_12px_28px_rgba(16,24,40,.09)]"
      style={{
        animationDelay: delay,
        background: accent ? "var(--surface-accent)" : undefined,
        borderColor: accent ? "var(--border-accent)" : undefined,
      }}
    >
      <div className="mb-4 flex items-center justify-between">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-xl"
          style={{ background: iconBg, color: iconColor, boxShadow: accent ? "0 4px 12px rgba(124,58,237,.3)" : undefined }}
        >
          <Icon className="h-5 w-5" />
        </div>
        {badge && (
          <span className="rounded-full px-2 py-0.5 text-xs font-bold" style={{ background: badgeBg, color: badgeColor }}>
            {badge}
          </span>
        )}
      </div>
      {loading ? (
        <Skeleton className="mb-1.5 h-8 w-14" />
      ) : (
        <div className="text-[32px] font-extrabold leading-none tracking-[-0.03em]" style={{ color: accent ? "#6D28D9" : undefined }}>
          {value}
        </div>
      )}
      <div className="mt-1.5 text-[13px] font-medium text-muted-foreground" style={{ color: accent ? "#7C3AED" : undefined }}>
        {label}
      </div>
    </div>
  );
}

// ─── Appointment row ───────────────────────────────────────────────────────────
function ApptRow({ time, name, status }: { time: string; name: string; status: string }) {
  const st = STATUS_BADGE[status] ?? STATUS_BADGE.scheduled;
  return (
    <div className="flex items-center gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-secondary">
      <div className="w-12 shrink-0 text-center text-[13.5px] font-extrabold tracking-tight text-foreground">
        {time}
      </div>
      <div className="h-7 w-px shrink-0 bg-secondary" />
      <div className="min-w-0 flex-1 text-[13.5px] font-semibold text-foreground truncate">{name}</div>
      <span className="shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-bold whitespace-nowrap" style={{ background: st.bg, color: st.color }}>
        {st.label}
      </span>
    </div>
  );
}

// ─── Bar chart ────────────────────────────────────────────────────────────────
function WeekChart({ days, perDay, today }: { days: string[]; perDay: Record<string, number>; today: string }) {
  const values = days.map((d) => perDay[d] ?? 0);
  const max = Math.max(1, ...values);
  const total = values.reduce((a, b) => a + b, 0);

  return (
    <div
      className="animate-fade-up rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]"
      style={{ animationDelay: ".12s", padding: "22px 24px" }}
    >
      <div className="mb-1 flex items-center justify-between">
        <div>
          <h3 className="text-[15.5px] font-bold text-foreground">Consultas por dia</h3>
          <p className="mt-0.5 text-[12.5px] text-muted-foreground">Esta semana</p>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
          <span className="inline-block h-2.5 w-2.5 rounded-[3px] bg-primary" />
          Total: {total}
        </div>
      </div>
      <div className="flex h-48 items-end justify-between gap-3 pt-6">
        {days.map((d, i) => {
          const v = values[i];
          const isToday = d === today;
          const dow = new Date(`${d}T00:00:00Z`).getUTCDay();
          const heightPct = max > 0 ? (v / max) * 100 : 0;
          return (
            <div key={d} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
              <span className="text-[12.5px] font-bold text-foreground">{v}</span>
              <div className="flex w-full flex-1 items-end">
                <div
                  className="w-full max-w-[46px] mx-auto animate-grow-bar rounded-t-lg transition-all"
                  style={{
                    height: `${heightPct}%`,
                    minHeight: v ? "8px" : "3px",
                    background: isToday
                      ? "linear-gradient(180deg, #0D9488, #14B8A6)"
                      : "linear-gradient(180deg, #7C3AED, #A78BFA)",
                  }}
                  title={`${v} consulta(s)`}
                />
              </div>
              <span
                className={cn("text-xs font-semibold", isToday ? "text-teal" : "text-muted-foreground")}
              >
                {PT_WEEKDAYS[dow]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export function DashboardPage() {
  const navigate = useNavigate();
  const today = todayStr();
  const { start, days } = useMemo(() => weekRange(today), [today]);
  const weekEnd = days[6];

  const weekStats  = useSchedulingStats(start, weekEnd);
  const todayAppts = useAppointments(today);
  const patients   = usePatients();
  const convs      = useConversations();
  const charges    = useCharges();

  const patientName = useMemo(() => {
    const map = new Map((patients.data ?? []).map((p) => [p.id, p.nome]));
    return (id: string) => map.get(id) ?? "Paciente";
  }, [patients.data]);

  const byStatus = weekStats.data?.by_status ?? {};
  const perDay   = weekStats.data?.per_day ?? {};

  const upcoming = useMemo(() => {
    const now = Date.now();
    return (todayAppts.data ?? [])
      .filter((a) => (a.status === "scheduled" || a.status === "confirmed") && new Date(a.starts_at).getTime() >= now)
      .slice(0, 6);
  }, [todayAppts.data]);

  const pendingCharges = (charges.data ?? []).filter((c) => c.status === "pending").length;

  return (
    <div className="mx-auto flex max-w-[1240px] flex-col gap-5 pb-12">
      {/* Header */}
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-foreground">
            Olá, bem-vindo(a) 👋
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Aqui está o resumo da sua clínica hoje.
          </p>
        </div>
        <button
          onClick={() => navigate("/agenda")}
          className="inline-flex items-center gap-2 rounded-[11px] bg-primary px-[17px] py-[11px] text-sm font-bold text-white shadow-[0_4px_14px_rgba(124,58,237,.28)] transition-all hover:-translate-y-px hover:shadow-[0_8px_22px_rgba(124,58,237,.36)]"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
          Agendar consulta
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          label="Consultas hoje"
          value={todayAppts.data?.length ?? 0}
          Icon={CalendarDays}
          iconBg="#EEF2FF" iconColor="#4F46E5"
          badge="+2" badgeBg="#F0FDFA" badgeColor="#0D9488"
          loading={todayAppts.isLoading}
          delay="0.02s"
        />
        <KpiCard
          label="Pacientes cadastrados"
          value={patients.data?.length ?? 0}
          Icon={Users}
          iconBg="#F0FDFA" iconColor="#0D9488"
          badge="+18%" badgeBg="#F0FDFA" badgeColor="#0D9488"
          loading={patients.isLoading}
          delay="0.08s"
        />
        <KpiCard
          label="Conversas ativas"
          value={convs.data?.length ?? 0}
          Icon={MessagesSquare}
          iconBg="#7C3AED" iconColor="#fff"
          badge="IA" badgeBg="#EDE9FE" badgeColor="#6D28D9"
          loading={convs.isLoading}
          accent
          delay="0.14s"
        />
        <KpiCard
          label="Cobranças pendentes"
          value={pendingCharges}
          Icon={CreditCard}
          iconBg="#FFFBEB" iconColor="#D97706"
          loading={charges.isLoading}
          delay="0.20s"
        />
      </div>

      {/* Gráfico + Próximas */}
      <div className="grid gap-4 lg:grid-cols-[1.55fr_1fr]">
        {/* Gráfico */}
        {weekStats.isLoading ? (
          <div className="animate-fade-up rounded-[18px] border bg-card p-6">
            <Skeleton className="h-56 w-full" />
          </div>
        ) : (
          <WeekChart days={days} perDay={perDay} today={today} />
        )}

        {/* Próximas consultas de hoje */}
        <div
          className="animate-fade-up flex flex-col rounded-[18px] border bg-card shadow-[0_1px_2px_rgba(16,24,40,.04)]"
          style={{ animationDelay: ".18s", padding: "20px 14px 14px 20px" }}
        >
          <div className="mb-3 flex items-center justify-between pr-1.5">
            <h3 className="text-[15.5px] font-bold text-foreground">Próximas consultas hoje</h3>
            <Link to="/agenda" className="text-[12.5px] font-semibold text-primary hover:underline">
              Ver agenda
            </Link>
          </div>
          <div className="flex flex-col gap-0.5 overflow-y-auto">
            {todayAppts.isLoading ? (
              <>
                <Skeleton className="h-11 w-full rounded-xl" />
                <Skeleton className="h-11 w-full rounded-xl" />
                <Skeleton className="h-11 w-full rounded-xl" />
              </>
            ) : upcoming.length > 0 ? (
              upcoming.map((a) => (
                <ApptRow
                  key={a.id}
                  time={formatTimeUTC(a.starts_at)}
                  name={patientName(a.patient_id)}
                  status={a.status}
                />
              ))
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Nenhuma consulta pendente para hoje.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Stats rodapé */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatPill icon={<CalendarCheck className="h-5 w-5" />} iconBg="#F0FDF4" iconColor="#16A34A" label="Confirmadas esta semana" value={String(byStatus.confirmed ?? 0)} note={`de ${weekStats.data?.total ?? 0} agendadas`} noteColor="var(--text-faint)" />
        <StatPill icon={<CalendarDays className="h-5 w-5" />} iconBg="#EEF2FF" iconColor="#4F46E5" label="Total esta semana" value={String(weekStats.data?.total ?? 0)} note="agendamentos" noteColor="var(--text-faint)" />
        <StatPill icon={<svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>} iconBg="#FFFBEB" iconColor="#D97706" label="Pendentes de confirmação" value={String(byStatus.scheduled ?? 0)} note="aguardando resposta" noteColor="#B45309" />
        <StatPill icon={<svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /></svg>} iconBg="#F0FDFA" iconColor="#0D9488" label="Pacientes esta semana" value={String(patients.data?.length ?? 0)} note="cadastrados" noteColor="var(--text-faint)" />
      </div>
    </div>
  );
}

function StatPill({ icon, iconBg, iconColor, label, value, note, noteColor }: {
  icon: React.ReactNode; iconBg: string; iconColor: string;
  label: string; value: string; note: string; noteColor: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-[15px] border bg-card p-3.5 shadow-[0_1px_2px_rgba(16,24,40,.04)]">
      <div className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl" style={{ background: iconBg, color: iconColor }}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="truncate text-[10.5px] font-bold uppercase tracking-[.04em] text-muted-foreground">{label}</div>
        <div className="mt-0.5 flex items-baseline gap-1.5">
          <span className="text-[22px] font-extrabold tracking-[-0.03em] text-foreground">{value}</span>
          <span className="text-[11.5px] font-bold whitespace-nowrap" style={{ color: noteColor }}>{note}</span>
        </div>
      </div>
    </div>
  );
}
